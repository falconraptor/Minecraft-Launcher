import sys
from threading import Thread
from tkinter.messagebox import showerror

from webview import create_window

import modpacks
import mods
from db import startup, MyRow
from modpacks import get_modpacks
from webserver import start_server, route, serve, server
from webserver.server import json_serial


def json_convert(obj):
    try:
        if isinstance(obj, MyRow):
            return dict(obj)
    except TypeError:
        return json_serial(obj)


FOLDER = getattr(sys, '_MEIPASS', '.')
server.json_map = json_convert
API_COMMANDS = {
    'all': {
        'get_modpack_categories': lambda c: c.execute('SELECT Name FROM Modpack_Category'),
    }
}
SORT_MAP = {
    '1': 'Created',
    '2': 'Last_Updated',
    '3': 'Name',
    '5': 'Downloads'
}


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
    return serve(FOLDER + '/public/' + file, 60)


@route(r'/api/([\w]+)/([\w]+)')
def api(request, page, func):
    method = getattr(modpacks, func, None)
    if not method:
        method = getattr(mods, func, None)
        if not method:
            method = API_COMMANDS.get(page, {}).get(func)
            if not method:
                method = globals()['{}_{}'.format(page, func)]
    if not method:
        return '', 404
    return {'results': list(method(DB, **request.GET))}


def all_filter(c, search, category, version, sort, page):
    filters = ''
    params = []
    if search:
        filters = "(Name like '%?%' OR Short_Description LIKE '%?%')"
        params.extend([search] * 2)
    if category:
        filters += '{}Name IN (SELECT Mod FROM Modpack_Category_Map WHERE Category=?)'.format(' AND ' if filters else '')
        params.append(category)
    if version:
        filters += '{}Name IN (SELECT Mod FROM Modpack_Version WHERE Version=?)'.format(' AND ' if filters else '')
        params.append(version)
    results = list(c.execute('SELECT * FROM Modpack WHERE {} ORDER BY {} DESC LIMIT 20 OFFSET {}'.format(filters, SORT_MAP[sort], 0 if page == '1' else (int(page) - 1) * 20), params))
    if not results:
        get_modpacks(c, version, sort or None, max_page=int(page))
        results = list(c.execute('SELECT * FROM Modpack WHERE {} ORDER BY {} DESC LIMIT 20 OFFSET {}'.format(filters, SORT_MAP[sort], 0 if page == '1' else (int(page) - 1) * 20), params))
    return results


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
