import sys
from threading import Thread

from webview import create_window

from webserver import start_server, route, serve


@route('/')
def installed(request):
    return serve(getattr(sys, '_MEIPASS', '.') + '/public/html/installed.html')


@route()
def all(request):
    return serve(getattr(sys, '_MEIPASS', '.') + '/public/html/all.html')


@route()
def settings(request):
    return serve(getattr(sys, '_MEIPASS', '.') + '/public/html/settings.html')


@route(r'/static/([\w.\-/]+)', no_end_slash=True)
def static(request, file):
    return serve(getattr(sys, '_MEIPASS', '.') + '/public/' + file)


if __name__ == '__main__':
    port = 5674  # randint(6000, 32000)
    server = start_server(bind='127.0.0.1', port=port, serve=False)
    Thread(target=server.serve_forever).start()
    win = create_window('Minecraft Launcher', 'http://127.0.0.1:{}'.format(port), background_color='#000000')
    server.shutdown()
