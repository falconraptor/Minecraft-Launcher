from db import startup
from mods import get_mods, get_versions, get_mod_details, get_mod_files

if __name__ == '__main__':
    c = startup()
    get_versions(c)
    get_mods(c, '1.12.2')
    get_mod_details(c, 'Quark')
    get_mod_files(c, 'Quark')  # ~20 seconds
