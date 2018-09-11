from threading import Thread
from tkinter.ttk import Combobox, Frame, Scrollbar

import requests
from bs4 import BeautifulSoup, Tag
from tkinter.tix import W, StringVar, Listbox, SINGLE, END, NW

BASE = 'https://minecraft.curseforge.com'
MODS = BASE + '/mc-mods'


def get_game_versions(page=requests.get(MODS).text):
    versions = {}
    last = ''
    for version in BeautifulSoup(page, 'html.parser').find('select', {'id': 'filter-game-version'}):
        if isinstance(version, Tag) and version['value']:
            if version.attrs.get('class', [''])[-1] == 'game-version-type':
                last = version.text.replace('\xa0', '')
                versions[last] = {'id': version['value'], 'sub-versions': {}}
            else:
                versions[last]['sub-versions'][version.text.replace('\xa0', '')] = {'id': version['value'], 'mods': {}}
    return versions


def get_mods(url=MODS, categories=None, authors=None, total_pages=0, start_page=1, version=None):
    if authors is None:
        authors = {}
    if categories is None:
        categories = {}
    if not total_pages:
        total_pages = int(BeautifulSoup(requests.get(url + ('?filter-game-version={}'.format(version['id']) if version else '')).text, 'html.parser').find('section', {'role': 'main'}).find('div', {'class': 'listing-header'}).find_all('a', {'class': 'b-pagination-item'})[-1].text)
    mods = {}
    for i in range(start_page, total_pages + 1):
        for mod in BeautifulSoup(requests.get('{}?page={}{}'.format(url, i, '&filter-game-version={}'.format(version['id']) if version else '')).text, 'html.parser').find_all('li', {'class': 'project-list-item'}):
            elem = mod.find('div', {'class': 'name'}).find('a')
            if not elem:
                continue
            name = elem.text.strip()
            m = mods[name] = {'url': elem['href'].strip(), 'img': '', 'authors': {}, 'downloads': 0, 'last_updated': {'epoch': 0, 'datetime': '', 'date': ''}, 'short_description': '', 'categories': {}, 'name': name, 'id': '', 'description': '', 'members': {}, 'files': []}
            elem = mod.find('div', {'class': 'avatar'}).find('img')
            if elem:
                m['img'] = elem['src'].strip()
            elem = mod.find('span', {'class': 'byline'}).find('a')
            if elem:
                a = elem.text.strip()
                if a not in authors:
                    authors[a] = {'url': elem['href'], 'mods': {}, 'name': a}
                m['authors'][a] = authors[a]
                authors[a]['mods'][name] = m
            elem = mod.find('div', {'class': 'stats'}).find_all('p')
            if elem:
                m['downloads'] = int(elem[0].text.replace(',', '').strip())
                date = elem[1].find('abbr')
                m['last_updated'] = {'epoch': date['data-epoch'].strip(), 'datetime': date['title'].strip(), 'date': date.text.strip()}
            elem = mod.find('div', {'class': 'description'}).find('p')
            if elem:
                m['short_description'] = elem.text.strip()
            for c in mod.find('div', {'class': 'category-icon-wrapper'}).find_all('div'):
                c = c.find('a')
                t = c['title'].strip()
                if t not in categories:
                    categories[t] = {'url': c['href'].strip(), 'img': c.find('img')['src'].strip(), 'mods': {}, 'name': t}
                m['categories'][t] = categories[t]
                categories[t]['mods'][name] = m
            if version:
                version['mods'][name] = m
    return mods, categories, authors, total_pages


def center(toplevel):
    toplevel.update_idletasks()
    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    toplevel.geometry("%dx%d+%d+%d" % (size + (toplevel.winfo_screenwidth() / 2 - size[0] / 2, toplevel.winfo_screenheight() / 2 - size[1] / 2)))


class MainUI(Frame):
    versions = {}
    cats = {}
    authors = {}
    mods = {}
    page = 1
    total_pages = 1
    old_version = ''

    def __init__(self, master=None):
        super().__init__(master)
        self.get_versions()
        root = self.master
        root.title('MC Mod Controller')
        root.grid(widthInc=25, baseWidth=400, heightInc=100, baseHeight=400)
        center(root)
        self.mod_version = StringVar(root)
        self.combo = Combobox(root, textvariable=self.mod_version, state='readonly', postcommand=self.combo_versions)
        self.combo.bind('<<ComboboxSelected>>', self.get_mods)
        self.combo.grid(column=0, row=0, rowspan=1, columnspan=3, sticky=NW)
        self.select = Listbox(root, selectmode=SINGLE)
        vsb = Scrollbar(root, orient='vertical', command=self.select.yview)
        self.select.configure(yscrollcommand=vsb.set)
        vsb.grid(column=14, row=0, columnspan=1, rowspan=4, sticky='ns')
        self.select.grid(column=3, row=0, rowspan=4, columnspan=11, sticky=W)

    def combo_versions(self):
        self.combo['values'] = list(self.versions.keys())

    def get_mods(self, __thread=True):
        ver = self.mod_version.get()
        if ver not in self.versions:
            return
        if ver != self.old_version:
            self.total_pages = 0
            self.page = 1
        if __thread:
            Thread(target=self.get_mods, args=(False,), daemon=True).start()
        else:
            mods, _, _, self.total_pages = get_mods(MODS, self.cats, self.authors, self.page + 1, self.page, self.versions[ver])
            self.page += 1
            self.mods.update(mods)
            print(len(self.versions[self.mod_version.get()]['mods']))
            self.select.insert(END, *list(self.versions[self.mod_version.get()]['mods']))

    def get_versions(self, __thread=True):
        if __thread:
            Thread(target=self.get_versions, args=(False,), daemon=True).start()
        else:
            self.versions.update(get_game_versions())


if __name__ == '__main__':
    MainUI().mainloop()
