import sys
from threading import Thread
from tkinter.messagebox import showerror

from webview import create_window

import modpacks
import mods
from db import startup, MyRow
from webserver import start_server, route, serve, server
from webserver.server import json_serial

FOLDER = getattr(sys, '_MEIPASS', '.')


def json_convert(obj):
    try:
        if isinstance(obj, MyRow):
            return dict(obj)
    except TypeError:
        return json_serial(obj)

server.json_map = json_convert


@route('/')
def installed(request):
    return serve(FOLDER + '/public/html/installed.html')


@route()
def all(request):
    return serve(FOLDER + '/public/html/all.html')


@route()
def settings(request):
    return serve(FOLDER + '/public/html/settings.html')


@route(r'/static/([\w.\-/]+)', no_end_slash=True)
def static(request, file):
    return serve(FOLDER + '/public/' + file)


@route(r'/api/([\w]+)')
def api(request, method):
    method = getattr(modpacks, method, getattr(mods, method, None))
    if not method:
        return '', 404
    return {'results': list(method(DB, **request.GET))}


def main():
    port = 5674  # randint(6000, 32000)
    try:
        server = start_server(bind='127.0.0.1', port=port, serve=False)
    except OSError:
        port = 5674  # randint(6000, 32000)
        try:
            server = start_server(bind='0.0.0.0', port=port, serve=False)
        except OSError:
            showerror('Error', 'Unable to bind to address')
    Thread(target=server.serve_forever).start()
    create_window('Minecraft Launcher', background_color='#000', width=850, url='http://127.0.0.1:{}'.format(port), debug=True)
    server.shutdown()


if __name__ == '__main__':
    DB = startup()
    main()
