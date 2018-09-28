from datetime import datetime

from db import startup
from mods import get_mods, get_versions, get_mod_details, get_mod_files, get_mod_file_changelog

if __name__ == '__main__':
    total = datetime.now()
    _start = datetime.now()
    c = startup()
    start = datetime.now()
    print('db', start - _start)
    get_versions(c)
    _start = datetime.now()
    print('versions', _start - start)
    get_mods(c, '1.12.2')
    start = datetime.now()
    print('mods', start - _start)
    get_mod_details(c, 'Quark')
    _start = datetime.now()
    print('mod_details', _start - start)
    get_mod_files(c, 'Quark')
    start = datetime.now()
    print('mod_files', start - _start)
    get_mod_file_changelog(c, 2620164)
    _start = datetime.now()
    print('file_changelog', _start - start)
    print('total', _start - total)
