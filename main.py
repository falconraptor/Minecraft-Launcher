from db import startup
from mods import get_mods

if __name__ == '__main__':
    c = startup()
    get_mods(c, list(c.execute('SELECT * FROM Version WHERE Name=? LIMIT 1', ('1.12.2',)))[0])
