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
            

async def run_command(*args):
    # Create subprocess
    process = await asyncio.create_subprocess_exec(
        *args,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE)
    # Wait for the subprocess to finish
    print("before subprocess")
    stdout, stderr = await process.communicate()
    print("after subprocess")
    # Return stdout
    return stdout.decode().strip()



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


app = web.Application()
app.add_routes([web.get('/', handle),
                web.get('/sub', handle_sub),
                web.get('/doorbird_viewer_ctrl', handle_db_viewer_ctrl),
                web.get('/idle', handle_idle)])

# if __name__ == '__main__':
web.run_app(app)
    
