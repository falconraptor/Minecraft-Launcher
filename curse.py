import requests
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep


def get_last_uploaded(project):
    html = requests.get('https://minecraft.curseforge.com/projects/' + project + '/files?filter-game-version=1738749986%3A572').text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    headings = [th.get_text().replace('\n', '') for th in table.find('tr').find_all('th')]
    datasets = []
    for row in table.find_all("tr")[1:]:
        dataset = zip(headings, (td.get_text().replace('\n', '').replace('\r', '').replace('\t', '').replace('  ', '') for td in row.find_all("td")))
        datasets.append(dataset)
    file = {}
    for field in datasets[0]:
        file[field[0]] = field[1]
    return datetime.strptime(file['Uploaded'], '%b %d, %Y')


if __name__ == '__main__':
    project = input('What project would you like to monitor? ')
    first = None
    while True:
        date = get_last_uploaded(project)
        if not first:
            first = date
            print('last updated:', first)
        elif date > first:
            print(date)
            break
        else:
            print(datetime.now(), project)
        sleep(60 * 60)
