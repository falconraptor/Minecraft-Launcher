from sqlite3 import connect, Row, PARSE_DECLTYPES, PARSE_COLNAMES


class MyRow(Row):
    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)


def create_tables(c):
    c.executescript('''
        CREATE TABLE IF NOT EXISTS Member (Name VARCHAR(255) PRIMARY KEY, URL TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS Category (Name VARCHAR(255) PRIMARY KEY, IMG_URL TEXT NOT NULL, URL TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS Version (Name VARCHAR(255) PRIMARY KEY, ID VARCHAR(100) NOT NULL UNIQUE, Parent VARCHAR(255) NOT NULL DEFAULT '', Last_Updated TIMESTAMP);
        CREATE TABLE IF NOT EXISTS Mod (Name VARCHAR(255) PRIMARY KEY, Short_Description VARCHAR(255) NOT NULL, Description TEXT NOT NULL DEFAULT '', Downloads INTEGER NOT NULL, ID VARCHAR(255) NOT NULL DEFAULT '', IMG_URL TEXT NOT NULL, URL TEXT NOT NULL, Last_Updated TIMESTAMP NOT NULL, Created TIMESTAMP, Last_Checked TIMESTAMP, Last_Description TIMESTAMP, Wiki TEXT NOT NULL DEFAULT '', Issue_Tracker TEXT NOT NULL DEFAULT '', Source TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS Mod_Version (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Version VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod_Category (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Category VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod_Member (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Member VARCHAR(255) NOT NULL, Type VARCHAR(100) NOT NULL DEFAULT 'Owner');
        CREATE TABLE IF NOT EXISTS File (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Name TEXT NOT NULL, Size INTEGER NOT NULL, Uploaded TIMESTAMP NOT NULL, Downloads INTEGER NOT NULL, Type VARCHAR(1) NOT NULL DEFAULT 'R', Uploaded_By VARCHAR(255) NOT NULL DEFAULT '', Changelog TEXT NOT NULL DEFAULT '', Parent_File INTEGER);
        CREATE TABLE IF NOT EXISTS File_Version (ID INTEGER PRIMARY KEY, File TEXT NOT NULL, Version VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS File_Java_Version (ID INTEGER PRIMARY KEY, File TEXT NOT NULL, Java VARCHAR(255) NOT NULL);
    ''')
    c.commit()


def startup():
    c = connect('client.db', detect_types=PARSE_DECLTYPES | PARSE_COLNAMES, check_same_thread=False)
    c.row_factory = MyRow
    create_tables(c)
    return c
