from datetime import datetime, timedelta
from threading import Thread, Lock
from time import sleep

import requests
from bs4 import BeautifulSoup

from db import MyRow

BASE = 'https://minecraft.curseforge.com'
MODPACKS = f'{BASE}/modpacks'


def get_modpack_versions(c):
    now = datetime.now()
    try:
        last_updated = list(c.execute('SELECT Last_Updated FROM Version_Updated ORDER BY ID DESC LIMIT 1'))[0].Last_Updated
    except IndexError:
        last_updated = 0
    if not last_updated or last_updated < now - timedelta(days=1):
        versions = {n.Name for n in c.execute('SELECT Name FROM Version')}
        last = ''
        to_add = []
        i = 0
        for version in BeautifulSoup(requests.get(MODPACKS).text, 'html.parser').find('select', {'id': 'filter-game-version'}).find_all('option'):
            if version['value']:
                name = version.text.replace('\xa0', '')
                parent = version.attrs.get('class', [''])[-1] == 'game-version-type'
                if parent:
                    last = name
                if name not in versions:
                    to_add.append((i, name, version['value'], '' if parent else last))
                i += 1
        if to_add:
            if versions:
                c.executemany('UPDATE Version SET I = I + 1 WHERE I >= ?', map(lambda v: v[0], to_add))
            c.executemany('INSERT INTO Version (I, Name, ID, Parent) VALUES (?, ?, ?, ?)', to_add)
        c.execute('INSERT INTO Version_Updated (Last_Updated) VALUES (?)', (now,))
        c.commit()
    return c.execute('SELECT * FROM Version')


def get_modpacks(c, version, sort=None, max_page=None):
    if not isinstance(version, MyRow):
        try:
            version = list(c.execute('SELECT * FROM Version WHERE Name=? LIMIT 1', (version,)))[0]
        except IndexError:
            get_modpack_versions(c)
            version = list(c.execute('SELECT * FROM Version WHERE Name=? LIMIT 1', (version,)))[0]
    if version.Modpacks_Last_Updated and version.Modpacks_Last_Updated > (datetime.utcnow() - timedelta(hours=1)):
        return c.execute('SELECT * FROM Modpack WHERE Name IN (SELECT Mod FROM Modpack_Version WHERE Version=?)', (version.Name,)), 0
    members = {m.Name for m in c.execute('SELECT Name FROM Member')}
    add_members = []
    categories = {ca.Name: ca.URL for ca in c.execute('SELECT Name, URL FROM Modpack_Category')}
    add_categories = []
    mods = {m.Name for m in c.execute('SELECT Name FROM Modpack')}
    add_mods = []
    mod_versions = {v.Mod + v.Version for v in c.execute('SELECT Mod, Version FROM Modpack_Version')}
    add_mod_versions = []
    mod_members = {m.Mod + m.Member: m.Type for m in c.execute('SELECT Mod, Member, Type FROM Modpack_Member')}
    add_mod_members = []
    mod_categories = {ca.Mod + ca.Category for ca in c.execute('SELECT Mod, Category FROM Modpack_Category_Map')}
    add_mod_categories = []
    page_one = BeautifulSoup(requests.get(f'{MODPACKS}{f"?filter-game-version={version.ID}" if version else ""}').text, 'html.parser')
    try:
        total_pages = int(page_one.find('section', {'role': 'main'}).find('div', {'class': 'listing-header'}).find_all('a', {'class': 'b-pagination-item'})[-1].text)
    except IndexError:
        total_pages = 1
    lock = Lock()

    def process_page(page_num, page=None):
        for mod in (page or BeautifulSoup(requests.get(f'{MODPACKS}?page={page_num}{f"&filter-game-version={version.ID}" if version else ""}{f"&filter-sort={sort}" if sort else ""}').text, 'html.parser')).find_all('li', {'class': 'project-list-item'}):
            elem = mod.find('div', {'class': 'name'}).find('a')
            if not elem:
                continue
            name = elem.text.strip()
            m = {'url': elem['href'], 'img': '', 'downloads': 0, 'last_updated': None, 'short_description': '', 'name': name, 'id': '', 'description': ''}
            elem = mod.find('div', {'class': 'avatar'}).find('img')
            if elem:
                m['img'] = elem['src']
            elem = mod.find('span', {'class': 'byline'}).find('a')
            while lock.locked():
                sleep(.01)
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

    threads = [Thread(target=process_page, args=(i, page_one if i == 1 else None)) for i in range(1, total_pages + 1)]
    [t.start() for t in threads]

    def db_add():
        lock.acquire()
        if add_members:
            c.executemany('INSERT INTO Member (Name, URL) VALUES (?, ?)', add_members)
        if add_categories:
            c.executemany('INSERT INTO Modpack_Category VALUES (?, ?, ?)', add_categories)
        if add_mods:
            c.executemany('INSERT INTO Modpack (Name, Short_Description, Downloads, IMG_URL, URL, Last_Updated) VALUES (?, ?, ?, ?, ?, ?)', add_mods)
        if add_mod_versions:
            c.executemany('INSERT INTO Modpack_Version (Mod, Version) VALUES (?, ?)', add_mod_versions)
        if add_mod_members:
            c.executemany('INSERT INTO Modpack_Member (Mod, Member) VALUES (?, ?)', add_mod_members)
        if add_mod_categories:
            c.executemany('INSERT INTO Modpack_Category_Map (Mod, Category) VALUES (?, ?)', add_mod_categories)
        c.execute("UPDATE Version SET Modpacks_Last_Updated=DATETIME('now') WHERE Name=?", (version.Name,))
        c.commit()
        lock.release()

    if not max_page:
        [t.join() for t in threads]
        db_add()
    else:
        [t.join() for t in threads[:max_page]]
        db_add()
        add_members.clear()
        add_categories.clear()
        add_mods.clear()
        add_mod_versions.clear()
        add_mod_members.clear()
        add_mod_categories.clear()

        def wait():
            [t.join() for t in threads[max_page:]]
            db_add()

        Thread(target=wait).start()
    return c.execute('SELECT * FROM Modpack WHERE Name IN (SELECT Mod FROM Modpack_Version WHERE Version=?)', (version.Name,)), total_pages


def get_modpack_details(c, mod):
    if not isinstance(mod, MyRow):
        mod = list(c.execute('SELECT * FROM Modpack WHERE Name=? LIMIT 1', (mod,)))[0]
    if mod.Last_Description and mod.Last_Description > (datetime.utcnow() - timedelta(days=1)):
        return
    members = {m.Name for m in c.execute('SELECT Name FROM Member')}
    add_members = []
    mod_members = {m.Mod + m.Member: m.Type for m in c.execute('SELECT Mod, Member, Type FROM Modpack_Member')}
    add_mod_members = []
    change_title = []
    html = BeautifulSoup(requests.get(f'{BASE}{mod.URL}').text, 'html.parser')
    for external in html.find_all('a', {'class': 'external-link'}):
        mod[external.text.replace('Issues', 'Issue_Tracker').strip()] = external['href']
    project, project_members = html.find_all('div', {'class': 'cf-sidebar-wrapper'})[::2]
    mod.ID = int(project.find('div', {'class': 'info-data'}).text)
    mod.Created = datetime.fromtimestamp(int(project.find_all('div', {'class': 'info-data'})[1].find('abbr')['data-epoch']))
    mod.Description = str(html.find('div', {'class': 'e-project-details-primary'}))
    for member in project_members.find_all('div', {'class': 'info-wrapper'}):
        member = member.find('p')
        a = member.find('a')
        name = a.find('span').text
        title = member.find('span', {'class': 'title'}).text
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
        c.executemany('INSERT INTO Modpack_Member (Mod, Member, Type) VALUES (?, ?, ?)', add_mod_members)
    if change_title:
        for member in change_title:
            c.execute('UPDATE Modpack_Member SET Type=? WHERE Mod=? AND Member=?', member)
    c.execute("UPDATE Modpack SET ID=?, Created=?, Description=?, Wiki=?, Source=?, Issue_Tracker=?, Last_Description=DATETIME('now') WHERE Name=?", (mod.ID, mod.Created, mod.Description, mod.Wiki, mod.Source, mod.Issue_Tracker, mod.Name))
    c.commit()


def get_modpack_files(c, mod):
    if not isinstance(mod, MyRow):
        mod = list(c.execute('SELECT * FROM Modpack WHERE Name=? LIMIT 1', (mod,)))[0]
    if mod.Last_Checked and mod.Last_Checked > (datetime.utcnow() - timedelta(hours=1)):
        return
    mod_versions = {v.Mod + v.Version for v in c.execute('SELECT Mod, Version FROM Modpack_Version')}
    add_mod_versions = []
    files = {f.ID for f in c.execute('SELECT ID FROM Modpack_File')}
    add_files = []
    file_versions = {str(v.File_ID) + v.Version for v in c.execute('SELECT File_ID, Version FROM Modpack_File_Version')}
    add_file_version = []
    page_one = BeautifulSoup(requests.get(f'{BASE}{mod.URL}/files').text, 'html.parser').find('div', {'class': 'listing-container'})
    header = page_one.find('div', {'class': 'listing-header'})
    for version in header.find('div', {'class': 'listing-filters-wrapper'}).find('select', {'id': 'filter-game-version'}).find_all('option'):
        if version['value']:
            name = version.text.replace('\xa0', '')
            if mod.Name + name not in mod_versions:
                add_mod_versions.append((mod.Name, name))
                mod_versions.add(mod.Name + name)
    pages = header.find_all('a', {'class': 'b-pagination-item'})
    total_pages = int(pages[-1].text) if pages else 1

    def process_page(page_num, page=None):
        for file in (page or BeautifulSoup(requests.get(f'{BASE}{mod.URL}/files?page={page_num}').text, 'html.parser')).find_all('tr', {'class': 'project-file-list-item'}):
            typ = file.find('td', {'class': 'project-file-release-type'}).find('div')['class'][0].split('-')[0][0].upper()
            a = file.find('div', {'class': 'project-file-name-container'}).find('a')
            i = int(a['href'].split('/')[-1])
            name = a.text
            size = file.find('td', {'class': 'project-file-size'}).text.strip()
            date = datetime.fromtimestamp(int(file.find('td', {'class': 'project-file-date-uploaded'}).find('abbr')['data-epoch']))
            version = file.find('span', {'class': 'version-label'}).text
            downloads = int(file.find('td', {'class': 'project-file-downloads'}).text.strip().replace(',', ''))
            if i not in files:
                add_files.append((i, typ, name, size, date, downloads, mod.Name))
                files.add(i)
            if str(i) + version not in file_versions:
                add_file_version.append((i, version))
                file_versions.add(str(i) + version)

    threads = [Thread(target=process_page, args=(i, page_one if i == 1 else None)) for i in range(1, total_pages + 1)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    if add_mod_versions:
        c.executemany('INSERT INTO Modpack_Version (Mod, Version) VALUES (?, ?)', add_mod_versions)
    if add_files:
        c.executemany('INSERT INTO Modpack_File (ID, Type, Name, Size, Uploaded, Downloads, Mod) VALUES (?, ?, ?, ?, ?, ?, ?)', add_files)
    if add_file_version:
        c.executemany('INSERT INTO Modpack_File_Version (File_ID, Version) VALUES (?, ?)', add_file_version)
    c.execute("UPDATE Modpack SET Last_Checked=DATETIME('now') WHERE Name=?", (mod.Name,))
    c.commit()


def get_modpack_file_changelog(c, file_id):
    if not isinstance(file_id, MyRow):
        file_id = list(c.execute('SELECT ID, Mod, Changelog FROM Modpack_File WHERE ID=?', (file_id,)))[0]
    if file_id.Changelog:
        return
    file_dependencies = {str(f.File_ID) + f.Dependency for f in c.execute('SELECT File_ID, Dependency FROM Modpack_File_Dependency')}
    add_file_dependencies = []
    url = list(c.execute('SELECT URL FROM Modpack WHERE Name=?', (file_id.Mod,)))[0].URL
    html = BeautifulSoup(requests.get(f'{BASE}{url}/files/{file_id.ID}').text, 'html.parser')
    file_id.Uploaded_By = html.find('div', {'class': 'user-tag'}).find_all('a')[-1].text
    file_id.Changelog = str(html.find('div', {'class': 'logbox'}))
    for tr in html.find_all('tr', {'class': 'project-file-list-item'}):
        a = tr.find('td', {'class': 'project-file-name'}).find_all('a')[-1]
        if 'server files' in (a.text or '').lower().strip():
            file_id.Server_ID = int(a['href'].split('/')[-1])
            file_id.Server_Size = tr.find('td', {'class': 'project-file-size'}).text.strip()
            file_id.Server_Downloads = int(tr.find('td', {'class': 'project-file-downloads'}).text.replace(',', ''))
    for dependencies in html.find_all('div', {'class': 'project-tag-info'}):
        name = dependencies.find('span').text
        if str(file_id.ID) + name not in file_dependencies:
            add_file_dependencies.append((file_id.ID, name))
            file_dependencies.add(str(file_id.ID) + name)
    if add_file_dependencies:
        c.executemany('INSERT INTO Modpack_File_Dependency (File_ID, Dependency) VALUES (?, ?)', add_file_dependencies)
    c.execute('UPDATE Modpack_File SET Changelog=?, Uploaded_By=?, Server_ID=?, Server_Size=?, Server_Downloads=? WHERE ID=?', (file_id.Changelog, file_id.Uploaded_By, file_id.Server_ID, file_id.Server_Size, file_id.Server_Downloads, file_id.ID))
    c.commit()
