from datetime import datetime, timedelta
from threading import Thread

from bs4 import BeautifulSoup, Tag
import requests

from db import MyRow

BASE = 'https://minecraft.curseforge.com'
MODS = BASE + '/mc-mods'


def get_versions(c):
    cu = c.cursor()
    cu.execute('SELECT Name FROM Version')
    versions = {n.Name for n in cu.fetchall()}
    last = ''
    to_add = []
    for version in BeautifulSoup(requests.get(MODS).text, 'html.parser').find('select', {'id': 'filter-game-version'}):
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


def get_mods(c, version, total_pages=0, start_page=1):
    if not isinstance(version, MyRow):
        version = list(c.execute('SELECT * FROM Version WHERE Name=? LIMIT 1', (version,)))[0]
    if version.Last_Updated and version.Last_Updated > (datetime.utcnow() - timedelta(hours=1)):
        return 0
    members = {m.Name for m in c.execute('SELECT Name FROM Member')}
    add_members = []
    categories = {ca.Name: ca.URL for ca in c.execute('SELECT Name, URL FROM Category')}
    add_categories = []
    mods = {m.Name for m in c.execute('SELECT Name FROM Mod')}
    add_mods = []
    mod_versions = {v.Mod + v.Version for v in c.execute('SELECT Mod, Version FROM Mod_Version')}
    add_mod_versions = []
    mod_members = {m.Mod + m.Member: m.Type for m in c.execute('SELECT Mod, Member, Type FROM Mod_Member')}
    add_mod_members = []
    mod_categories = {ca.Mod + ca.Category for ca in c.execute('SELECT Mod, Category FROM Mod_Category')}
    add_mod_categories = []
    if not total_pages:
        total_pages = int(BeautifulSoup(requests.get(MODS + ('?filter-game-version={}'.format(version.ID) if version else '')).text, 'html.parser').find('section', {'role': 'main'}).find('div', {'class': 'listing-header'}).find_all('a', {'class': 'b-pagination-item'})[-1].text)

    def process_page(page_num):
        for mod in BeautifulSoup(requests.get('{}?page={}{}'.format(MODS, page_num, '&filter-game-version={}'.format(version.ID) if version else '')).text, 'html.parser').find_all('li', {'class': 'project-list-item'}):
            elem = mod.find('div', {'class': 'name'}).find('a')
            if not elem:
                continue
            name = elem.text.strip()
            m = {'url': elem['href'], 'img': '', 'downloads': 0, 'last_updated': None, 'short_description': '', 'name': name, 'id': '', 'description': ''}
            elem = mod.find('div', {'class': 'avatar'}).find('img')
            if elem:
                m['img'] = elem['src']
            elem = mod.find('span', {'class': 'byline'}).find('a')
            if elem:
                a = elem.text.strip()
                if a not in members:
                    add_members.append((a, elem['href']))
                    members.add(a)
                    add_mod_members.append((name, a))
                elif name + a not in mod_members:
                    add_mod_members.append((name, a))
                    mod_members[name + a] = 'Owner'
            elem = mod.find('div', {'class': 'stats'}).find_all('p')
            if elem:
                m['downloads'] = int(elem[0].text.replace(',', '').strip())
                m['last_updated'] = datetime.fromtimestamp(int(elem[1].find('abbr')['data-epoch']))
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
                    u = ca['href']
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
    if add_categories:
        c.executemany('INSERT INTO Category VALUES (?, ?, ?)', add_categories)
    if add_mods:
        c.executemany('INSERT INTO Mod (Name, Short_Description, Downloads, IMG_URL, URL, Last_Updated) VALUES (?, ?, ?, ?, ?, ?)', add_mods)
    if add_mod_versions:
        c.executemany('INSERT INTO Mod_Version (Mod, Version) VALUES (?, ?)', add_mod_versions)
    if add_mod_members:
        c.executemany('INSERT INTO Mod_Member (Mod, Member) VALUES (?, ?)', add_mod_members)
    if add_mod_categories:
        c.executemany('INSERT INTO Mod_Category (Mod, Category) VALUES (?, ?)', add_mod_categories)
    c.execute("UPDATE Version SET Last_Updated=DATETIME('now') WHERE Name=?", (version.Name,))
    c.commit()
    return total_pages


def get_mod_details(c, mod):
    if not isinstance(mod, MyRow):
        mod = list(c.execute('SELECT * FROM Mod WHERE Name=? LIMIT 1', (mod,)))[0]
    if mod.Last_Description and mod.Last_Description > (datetime.utcnow() - timedelta(days=1)):
        return
    members = {m.Name for m in c.execute('SELECT Name FROM Member')}
    add_members = []
    mod_members = {m.Mod + m.Member: m.Type for m in c.execute('SELECT Mod, Member, Type FROM Mod_Member')}
    add_mod_members = []
    change_title = []
    html = BeautifulSoup(requests.get('{}{}'.format(BASE, mod.URL)).text, 'html.parser')
    for external in html.find_all('a', attrs={'class': 'external-link'}):
        mod[external.text.replace('Issues', 'Issue_Tracker').strip()] = external['href']
    project, project_members = html.find_all('div', attrs={'class': 'cf-sidebar-wrapper'})[::2]
    mod.ID = project.find('div', attrs={'class': 'info-data'}).text
    mod.Created = datetime.fromtimestamp(int(project.find_all('div', attrs={'class': 'info-data'})[1].find('abbr')['data-epoch']))
    mod.Description = str(html.find('div', attrs={'class': 'e-project-details-primary'}))
    for member in project_members.find_all('div', attrs={'class': 'info-wrapper'}):
        member = member.find('p')
        a = member.find('a')
        name = a.find('span').text
        title = member.find('span', attrs={'class': 'title'}).text
        if name not in members:
            add_members.append((name, a['href']))
            members.add(name)
            add_mod_members.append((mod.Name, name, title))
        elif mod.Name + name not in mod_members:
            add_mod_members.append((mod.Name, name, title))
            mod_members[mod.Name + name] = title
        elif mod_members[mod.Name + name] != title:
            change_title.append((mod.Name, name, title))
    if add_members:
        c.executemany('INSERT INTO Member (Name, URL) VALUES (?, ?)', add_members)
    if add_mod_members:
        c.executemany('INSERT INTO Mod_Member (Mod, Member, Type) VALUES (?, ?, ?)', add_mod_members)
    if change_title:
        for member in change_title:
            c.execute('UPDATE Mod_Member SET Type=? WHERE Mod=? AND Member=?', member)
    c.execute("UPDATE Mod SET ID=?, Created=?, Description=?, Wiki=?, Source=?, Issue_Tracker=?, Last_Description=DATETIME('now') WHERE Name=?", (mod.ID, mod.Created, mod.Description, mod.Wiki, mod.Source, mod.Issue_Tracker, mod.Name))
    c.commit()
