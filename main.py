import sys
from threading import Thread

from webview import create_window

from db import startup
from webserver import start_server, route, serve


@route('/')
def installed(request):
    return serve(getattr(sys, '_MEIPASS', '.') + '/public/html/installed.html')


@route()
def all(request):
    # versions = get_modpack_versions(DB)
    # versions = ''.join('<option value="{ID}"{0}>{Name}</option>'.format(' selected' if i == 0 else '', **v) for i, v in enumerate(versions))
    return serve(getattr(sys, '_MEIPASS', '.') + '/public/html/all.html')


@route()
def settings(request):
    return serve(getattr(sys, '_MEIPASS', '.') + '/public/html/settings.html')


@route(r'/static/([\w.\-/]+)', no_end_slash=True)
def static(request, file):
    return serve(getattr(sys, '_MEIPASS', '.') + '/public/' + file)


def main():
    port = 5674  # randint(6000, 32000)
    server = start_server(bind='127.0.0.1', port=port, serve=False)
    Thread(target=server.serve_forever).start()
    create_window('Minecraft Launcher', 'http://127.0.0.1:{}'.format(port), background_color='#000', width=850)
    server.shutdown()


if __name__ == '__main__':
    DB = startup()
    main()
