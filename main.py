from os.path import dirname, abspath, join

from remi import App, start
from remi.gui import *

from db import startup


class MyApp(App):
    def __init__(self, *args, **kwargs):
        self.c = startup()
        super().__init__(*args, static_file_path=join(dirname(abspath(__file__)), 'res'), **kwargs)

    def main(self):
        return self.modpacks()

    def modpacks(self):
        base = TabBox()
        base.get_child('ul').style['margin'] = '0'
        mine = Widget()

        for installed in self.c.execute("SELECT DISTINCT Modpack.Name AS Mod, Modpack.IMG_URL, Modpack_Member.Member, Modpack_File.Name AS File FROM Modpack INNER JOIN Modpack_File ON Modpack.Name==Modpack_File.Mod INNER JOIN Modpack_Member ON Modpack_Member.Mod=Modpack.Name WHERE Modpack_Member.Type=='Owner' AND Modpack_File.Installed==1 ORDER BY Modpack_File.Last_Played"):
            mod = HBox(Image(installed.IMG_URL, height=200, width=200))
            mod.add_child('name', Label(installed.Mod))
            mod.add_child('version', Label('Version: {}'.format('.'.join(installed.File.split('-')[-1].split('.')[:-1]).strip())))
            mod.add_child('owner', Label('By: {}'.format(installed.Member)))
            mine.add_child(installed.Mod, mod)

        browse = Widget()
        head = HBox()
        refresh = Button('Refresh')
        search = Input('text')
        head.add_child('refresh', refresh)
        head.add_child('search', search)
        browse.add_child('head', head)

        create = Widget()

        base.add_tab(mine, 'Installed Modpacks', None)
        base.add_tab(browse, 'Browse Modpacks', None)
        base.add_tab(create, 'Create Modpacks', None)
        return base

    def set_different_root_widget(self, emitter, new_root):
        self.set_root_widget(new_root)


if __name__ == '__main__':
    start(MyApp)  # , standalone=True, resizable=False
