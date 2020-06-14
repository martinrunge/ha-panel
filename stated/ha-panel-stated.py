#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 17:53:13 2019

@author: martin.runge@web.de
"""
import asyncio

from aiohttp import web
import ravel
from dbussy import DBusError
import os.path
from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1, QOS_2

# --------------------------------------------------------------------------- # 
# configure the client logging
# --------------------------------------------------------------------------- # 
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)


# states: each state of the display panel == a different screen is shown
#   - doorbird_active
#   - openhab_active
#   - media_ctrl
#   - info_screen
#   - desktop
#   - screen_off

# each state has its own start script, that will just bring the window to the front if already running
# available states == scripts in the states folder
# if running -> corresponding pid file in the run folder
# wmctrl  

scriptdir = os.path.dirname(__file__)

scriptsdir = os.path.normpath(os.path.join(scriptdir, "../scripts"))
pidfiledir = os.path.normpath(os.path.join(scriptdir, "../run"))

MQTTC = MQTTClient()

PanelState = 'idle'

async def run_command(*args):
    # Create subprocess
    process = await asyncio.create_subprocess_exec(
        *args,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE)
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    # Return stdout
    return stdout.decode().strip()

class Timer:
    def __init__(self, timeout = 0, callback = None):
        log.debug("Timer: timeout=%f  callback=%s"%(timeout,callback))
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        log.debug("Timer timeout. Executing %s"%self._callback)
        await self._callback()

    def cancel(self):
        log.debug("cancel timer")
        self._task.cancel()

TimerTask = Timer()

class CPanelWindow:
    def __init__(self, name):
        self.name=name
        self.pid=-1
        self.title=None
        self.pidfile=None
        self.pidfile = self.pidFileFromName(name)
        self.update()
    
    def update(self):
        self.readPid()
        
    def pidFileFromName(self, name):
        pidfilename = name + ".pid"
        self.pidfile = os.path.join(pidfiledir, pidfilename)
        return self.pidfile
    
    def readPid(self):
        if os.path.exists(self.pidfile):
            f = open(self.pidfile)
            pidstr = f.readline()
            self.pid = int(pidstr)
            return self.pid
        else:
            return -1
        
PanelWindows = []
        
async def getWindowIDs():
    output = await run_command("wmctrl", "-l", "-p")
    print(output)
    lines = output.splitlines()
    
    for line in lines:
        tokens = line.split(None, 4)
        if len(tokens) >= 5:
            winID = tokens[0]
            type = tokens[1]
            pid = tokens[2]
            xclient = tokens[3]
            title = tokens[4]
        
            for pw in PanelWindows:
                if pw.pid == pid:
                    pw.winID = winID
                    pw.title = title
                
async def setIdle():
    PanelStaus = 'idle'
    targetDashboard = 'Info'
    await run_command(os.path.join(scriptsdir, 'ha-panel.sh'))
    await doorbird_viewer_ctrl("stop")
    await MQTTC.publish('/Kueche/panel/dashboard', targetDashboard.encode('utf-8'))
    log.info("system idle")


async def setPanelStatus(status = 'none'):
    PanelStatus = status
    log.info("setPanelStatus: %s"%PanelStatus)
    if(PanelStatus == "doorbird_active"):
        # if doorbord is active, don't stop it by automatically as it might have been started manually
        # If started automatically while in idle state, start timer afterwards in showDoorBird
        TimerTask.cancel()
        
    targetDashboard = 'none'
    log.info("publishing status to MQTT")
    await MQTTC.publish('/Kueche/panel/dashboard', targetDashboard.encode('utf-8'))
    log.info("system active in state '%s'"%PanelStatus)
    
    

async def showDoorBird():
    log.debug("showDoorBird PanelState=%s"%PanelState)
    if PanelState == 'idle':
        await run_command(os.path.join(scriptsdir, 'doorbird.sh'), '--geometry', '1024x600+0+0')
        await setPanelStatus('doorbird_active')
        TimerTask = Timer(30, setIdle)
    else:
        await run_command(os.path.join(scriptsdir, 'doorbird.sh'), '--geometry',  '320x240+650+10')
    


async def handle_kuechenpanel(request):
    itemstr = request.match_info['state']
    targetDashboard = itemstr
    err_msg = "successfully set display to %s"%itemstr
    if itemstr == 'idle':
        err_msg = "successfully set display to idle"
        await setIdle()
    else:
        await setPanelStatus(itemstr)
        
    res_code = 200
    return web.Response(status=res_code, text=err_msg)
    

async def doorbird_viewer_ctrl(cmd):
    res_code = 200
    err_msg = "successfully executed '%s'"%cmd
    try:
        if cmd == "activate":
            await showDoorBird()
        else:
            ifc = ravel.session_bus()["de.rungenetz.doorbirdviewer"]["/"].get_interface("de.rungenetz.doorbirdviewer")
            if cmd == "play":
                ifc.play()
            else:
                if cmd == "stop":
                    ifc.stop()
                else:
                    res_code = 400
                    err_msg = "method '%s' not implemented"%cmd
                    pass    
            
    except DBusError as ex:
            print(str(ex))
            res_code = 500
            err_msg = "str(ex)"
     
    finally:
        return (res_code, err_msg)    
        
async def handle_db_viewer_ctrl(request):
    method = request.url.query['method']
    
    (res_code, err_msg) = await doorbird_viewer_ctrl(method)
    
    return web.Response(status=res_code, text=err_msg)



async def handle(request):
    name = request.match_info.get('name', "Anonymous")
    print("got request")
    text = "Hello, " + name
    return web.Response(text=text)

async def handle_sub(request):
    name = request.match_info.get('name', "Anonymous")
    print("got sub request")
    text = "Hello, " + name
    res = await run_command("sleep", "20")
    return web.Response(text=res)



# @asyncio.coroutine
async def mqtt_recv_coro():
    try:
        while True:
            message = await MQTTC.deliver_message()
            packet = message.publish_packet
            print("%s => %s" % (packet.variable_header.topic_name, str(packet.payload.data)))
        await MQTTC.unsubscribe(['/Kueche/panel/dashboard'])
        await MQTTC.disconnect()
    except ClientException as ce:
        log.error("Client exception: %s" % ce)


async def initMQTT(app):
    await MQTTC.connect('mqtt://omv.fritz.box/')
    # Subscribe to '$SYS/broker/uptime' with QOS=1
    # Subscribe to '$SYS/broker/load/#' with QOS=2
    await MQTTC.subscribe([
            ('/Kueche/panel/dashboard', QOS_1),
         ])
    asyncio.create_task(mqtt_recv_coro())


async def init(app):
    scripts = os.listdir(scriptsdir)

    for scr in scripts:
        (nam,ext) = os.path.splitext(scr)
        cpw = CPanelWindow(nam)
        cpw.update()
        PanelWindows.append(cpw)
    
    await getWindowIDs()

    

log.info("starting up...")
app = web.Application()
app.on_startup.append(initMQTT)
app.on_startup.append(init)
app.add_routes([web.get('/', handle),
                web.get('/sub', handle_sub),
                web.get('/doorbird_viewer_ctrl', handle_db_viewer_ctrl),
                web.get('/kuechenpanel/{state}', handle_kuechenpanel)])

# if __name__ == '__main__':
try:
    web.run_app(app)
    
except OSError as oserr:
    log.error(str(oserr))
    
