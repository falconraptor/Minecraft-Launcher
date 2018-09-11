from sqlite3 import connect, Row
from threading import Thread

import requests
from bs4 import BeautifulSoup, Tag

BASE = 'https://minecraft.curseforge.com'
MODS = BASE + '/mc-mods'


class MyRow(Row):
    def __getattr__(self, item):
        return self.__getitem__(item)


def create_tables(c):
    c.executescript('''
        CREATE TABLE IF NOT EXISTS Member (Name VARCHAR(255) PRIMARY KEY, URL TEXT NOT NULL, Type VARCHAR(100) NOT NULL DEFAULT 'Owner');
        CREATE TABLE IF NOT EXISTS Category (Name VARCHAR(255) PRIMARY KEY, IMG_URL TEXT NOT NULL, URL TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS Version (Name VARCHAR(255) PRIMARY KEY, ID VARCHAR(100) NOT NULL UNIQUE, Parent VARCHAR(255) NOT NULL DEFAULT '', Last_Updated TIMESTAMP);
        CREATE TABLE IF NOT EXISTS Mod (Name VARCHAR(255) PRIMARY KEY, Short_Description VARCHAR(255) NOT NULL, Description TEXT NOT NULL DEFAULT '', Downloads INTEGER NOT NULL, ID VARCHAR(255) NOT NULL DEFAULT '', IMG_URL TEXT NOT NULL, URL TEXT NOT NULL, Last_Updated TIMESTAMP NOT NULL, Created TIMESTAMP, Last_Checked TIMESTAMP);
        CREATE TABLE IF NOT EXISTS Mod_Version (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Version VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod_Category (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Category VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod_Member (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Member VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS File (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Name TEXT NOT NULL, Size INTEGER NOT NULL, Uploaded TIMESTAMP NOT NULL, Downloads INTEGER NOT NULL, Type VARCHAR(1) NOT NULL DEFAULT 'R', Uploaded_By VARCHAR(255) NOT NULL DEFAULT '', Changelog TEXT NOT NULL DEFAULT '', Parent_File INTEGER);
        CREATE TABLE IF NOT EXISTS File_Version (ID INTEGER PRIMARY KEY, File TEXT NOT NULL, Version VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS File_Java_Version (ID INTEGER PRIMARY KEY, File TEXT NOT NULL, Java VARCHAR(255) NOT NULL);
    ''')


def get_versions(c, url=MODS):
    cu = c.cursor()
    cu.execute('SELECT Name FROM Version')
    versions = {n.Name for n in cu.fetchall()}
    last = ''
    to_add = []
    for version in BeautifulSoup(requests.get(url).text, 'html.parser').find('select', {'id': 'filter-game-version'}):
        if isinstance(version, Tag) and version['value']:
            name = version.text.replace('\xa0', '')
            if version.attrs.get('class', [''])[-1] == 'game-version-type':
                last = name
                if name not in versions:
                    to_add.append((name, version['value'], ''))
            else:
                if name not in versions:
                    to_add.append((name, version['value'], last))
    if to_add:
        c.executemany('INSERT INTO Version (Name, ID, Parent) VALUES (?, ?, ?)', to_add)
        c.commit()


def get_mods(c, version, url=MODS, total_pages=0, start_page=1):
    members = {m.Name: m.Type for m in c.execute('SELECT Name, Type FROM Member')}
    add_members = []
    categories = {ca.Name: ca.URL for ca in c.execute('SELECT Name, URL FROM Category')}
    add_categories = []
    mods = {m.Name for m in c.execute('SELECT Name FROM Mod')}
    add_mods = []
    mod_versions = {v.Mod + v.Version for v in c.execute('SELECT Mod, Version FROM Mod_Version')}
    add_mod_versions = []
    mod_members = {m.Mod + m.Member for m in c.execute('SELECT Mod, Member FROM Mod_Member')}
    add_mod_members = []
    mod_categories = {ca.Mod + ca.Category for ca in c.execute('SELECT Mod, Category FROM Mod_Category')}
    add_mod_categories = []
    if not total_pages:
        total_pages = int(BeautifulSoup(requests.get(url + ('?filter-game-version={}'.format(version.ID) if version else '')).text, 'html.parser').find('section', {'role': 'main'}).find('div', {'class': 'listing-header'}).find_all('a', {'class': 'b-pagination-item'})[-1].text)

    def process_page(page_num):
        for mod in BeautifulSoup(requests.get('{}?page={}{}'.format(url, page_num, '&filter-game-version={}'.format(version.ID) if version else '')).text, 'html.parser').find_all('li', {'class': 'project-list-item'}):
            elem = mod.find('div', {'class': 'name'}).find('a')
            if not elem:
                continue
            name = elem.text.strip()
            m = {'url': elem['href'].strip(), 'img': '', 'downloads': 0, 'last_updated': 0, 'short_description': '', 'name': name, 'id': '', 'description': ''}
            elem = mod.find('div', {'class': 'avatar'}).find('img')
            if elem:
                m['img'] = elem['src'].strip()
            elem = mod.find('span', {'class': 'byline'}).find('a')
            if elem:
                a = elem.text.strip()
                if a not in members:
                    add_members.append((a, elem['href']))
                    members[a] = 'Owner'
                    add_mod_members.append((name, a))
                elif name + a not in mod_members:
                    add_mod_members.append((name, a))
                    mod_members.add(name + a)
            elem = mod.find('div', {'class': 'stats'}).find_all('p')
            if elem:
                m['downloads'] = int(elem[0].text.replace(',', '').strip())
                m['last_updated'] = int(elem[1].find('abbr')['data-epoch'].strip())
            elem = mod.find('div', {'class': 'description'}).find('p')
            if elem:
                m['short_description'] = elem.text.strip()
            if name not in mods:
                add_mods.append((name, m['short_description'], m['downloads'], m['img'], m['url'], m['last_updated']))
                mods.add(name)
            for ca in mod.find('div', {'class': 'category-icon-wrapper'}).find_all('div'):
                ca = ca.find('a')
                t = ca['title'].strip()
                if t not in categories:
                    u = ca['href'].strip()
                    add_categories.append((t, ca.find('img')['src'].strip(), u))
                    add_mod_categories.append((name, t))
                    categories[t] = u
                elif name + t not in mod_categories:
                    add_mod_categories.append((name, t))
                    mod_categories.add(name + t)
            if version and name + version.Name not in mod_versions:
                add_mod_versions.append((name, version.Name))
                mod_versions.add(name + version.Name)

    threads = [Thread(target=process_page, args=(i,)) for i in range(start_page, total_pages + 1)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    if add_members:
        c.executemany('INSERT INTO Member (Name, URL) VALUES (?, ?)', add_members)
        c.commit()
    if add_categories:
        c.executemany('INSERT INTO Category VALUES (?, ?, ?)', add_categories)
        c.commit()
    if add_mods:
        c.executemany('INSERT INTO Mod (Name, Short_Description, Downloads, IMG_URL, URL, Last_Updated) VALUES (?, ?, ?, ?, ?, ?)', add_mods)
        c.commit()
    if add_mod_versions:
        c.executemany('INSERT INTO Mod_Version (Mod, Version) VALUES (?, ?)', add_mod_versions)
        c.commit()
    if add_mod_members:
        c.executemany('INSERT INTO Mod_Member (Mod, Member) VALUES (?, ?)', add_mod_members)
        c.commit()
    if add_mod_categories:
        c.executemany('INSERT INTO Mod_Category (Mod, Category) VALUES (?, ?)', add_mod_categories)
        c.commit()
    c.execute("UPDATE Version SET Last_Updated=DATETIME('now') WHERE Name=?", (version.Name,))
    return total_pages


if __name__ == '__main__':
    c = connect('client.db')
    c.row_factory = MyRow
    create_tables(c)
    get_versions(c)
    get_mods(c, list(c.execute('SELECT * FROM Version WHERE Name=? LIMIT 1', ('1.12.2',)))[0])
