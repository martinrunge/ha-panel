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
        winID = tokens[0]
        type = tokens[1]
        pid = tokens[2]
        xclient = tokens[3]
        title = tokens[4]
        
        for pw in PanelWindows:
            if pw.pid == pid:
                pw.winID = winID
                pw.title = title
                

def handle_idle(request):
    err_msg = "successfully set display to idle"
    res_code = 200
    
    print("system idle")
    
    return web.Response(status=res_code, text=err_msg)
    

def doorbird_viewer_ctrl(cmd):
    res_code = 200
    err_msg = "successfully executed '%s'"%cmd
    try:
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

    print("got request '%s' with mehtod '%s'"%(str(request.url), method))
    
    (res_code, err_msg) = doorbird_viewer_ctrl(method)
    
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



async def init(app):
    scripts = os.listdir(scriptsdir)

    for scr in scripts:
        (nam,ext) = os.path.splitext(scr)
        cpw = CPanelWindow(nam)
        cpw.update()
        PanelWindows.append(cpw)
    
    await getWindowIDs()

    


app = web.Application()
app.on_startup.append(init)
app.add_routes([web.get('/', handle),
                web.get('/sub', handle_sub),
                web.get('/doorbird_viewer_ctrl', handle_db_viewer_ctrl),
                web.get('/idle', handle_idle)])

# if __name__ == '__main__':
web.run_app(app)
    
