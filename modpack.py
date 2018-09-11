import json

import requests
from bs4 import BeautifulSoup

# E:\falco\Documents\Curse\Minecraft\Instances\Techraptor (1)\manifest.json

versions = {'1.11': {'all': '1738749986%3A599', '1.11': '2020709689%3A6317', '1.11.2': '2020709689%3A6452'}, '1.12': {'all': '1738749986%3A628', '1.12': '2020709689%3A6580'}}


def get_version_exists(mod, main, sub):
    html = requests.get('https://minecraft.curseforge.com/projects/{}/files?filter-game-version={}'.format(mod, versions[main][sub])).text
    soup = BeautifulSoup(html, 'html.parser')
    html_table = soup.find('table')
    result = []
    if html_table:
        headings = [th.get_text().replace('\n', '') for th in html_table.find('tr').find_all('th')]
        datasets = []
        for row in html_table.find_all("tr")[1:]:
            dataset = zip(headings, (td.get_text().replace('\n', '').replace('\r', '').replace('\t', '').replace('  ', '') for td in row.find_all("td")))
            datasets.append(dataset)
        version = sub
        if version == 'all':
            version = main
        for data in datasets:
            name = None
            found = False
            for field in data:
                if field[0] == 'Name' and not name:
                    name = field[1]
                if field[0] in {'Name', 'Game Version'} and version in field[1] and not found:
                    found = True
                if found and name:
                    break
            if found and name:
                result.clear()
                break
            elif not found and name:
                result.append(name)
    if not result:
        return False
    return result


if __name__ == '__main__':
    manifest = input('Path to manifest file: ')
    print('\n\nWhich version?')
    version_main = None
    while not version_main:
        for main_version, sub_versions in versions.items():
            print('  ', main_version)
        version_main = input('>>')
        if version_main not in versions:
            version_main = None
            print('That is not a valid version')
    print('\n\nWhich sub version?')
    version_sub = None
    while not version_sub:
        for sub_version in versions[version_main]:
            print('  ', sub_version)
        version_sub = input('>>')
        if version_sub not in versions[version_main]:
            version_sub = None
            print('That is not a valid sub version')
    with open(manifest, mode='rt') as file:
        data = json.loads(''.join(file.readlines()))
    for mod in data['files']:
        if mod:
            result = get_version_exists(mod['projectID'], version_main, version_sub)
            if result:
                print(json.dumps(result))
        print('{}/{} - {:.02%}'.format(data['files'].index(mod) + 1, len(data['files']), (data['files'].index(mod) + 1) / len(data['files'])))
