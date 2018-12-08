from random import randint
from threading import Thread

import webview

from webserver import start_server, route


@route()
def index(request):
    return 'Test'


if __name__ == '__main__':
    port = randint(6000, 32000)
    with open('public/js/port.js', 'wt') as _out:
        _out.write('const PORT = {}'.format(port))
    server = start_server(bind='127.0.0.1', port=port, serve=False)
    Thread(target=server.serve_forever, args=(.1,)).start()
    webview.create_window('Minecraft Launcher', 'http://localhost:{}'.format(port))
    server.shutdown()
