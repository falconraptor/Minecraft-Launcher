from os import mkdir
from os.path import exists
from sqlite3 import connect, Row, PARSE_DECLTYPES, PARSE_COLNAMES


class MyRow(Row):
    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)


def create_tables(c):
    c.executescript('''
        CREATE TABLE IF NOT EXISTS Member (Name VARCHAR(255) PRIMARY KEY ASC, URL TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod (Name VARCHAR(255) PRIMARY KEY ASC, Short_Description VARCHAR(255) NOT NULL, Description TEXT NOT NULL DEFAULT '', Downloads INTEGER NOT NULL, ID INTEGER, IMG_URL TEXT NOT NULL, URL TEXT NOT NULL, Last_Updated TIMESTAMP NOT NULL, Created TIMESTAMP, Last_Checked TIMESTAMP, Last_Description TIMESTAMP, Wiki TEXT NOT NULL DEFAULT '', Issue_Tracker TEXT NOT NULL DEFAULT '', Source TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS Mod_Category (Name VARCHAR(255) PRIMARY KEY ASC, IMG_URL TEXT NOT NULL, URL TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod_Category_Map (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Category VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod_File (ID INTEGER PRIMARY KEY DESC, Mod VARCHAR(255) NOT NULL, Name TEXT NOT NULL, Size INTEGER NOT NULL, Uploaded TIMESTAMP NOT NULL, Downloads INTEGER NOT NULL, Type VARCHAR(1) NOT NULL DEFAULT 'R', Uploaded_By VARCHAR(255) NOT NULL DEFAULT '', Changelog TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS Mod_File_Dependency (ID INTEGER PRIMARY KEY, File_ID INTEGER NOT NULL, Dependency VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod_File_Version (ID INTEGER PRIMARY KEY, File_ID INTEGER NOT NULL, Version VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Mod_Member (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Member VARCHAR(255) NOT NULL, Type VARCHAR(100) NOT NULL DEFAULT 'Owner');
        CREATE TABLE IF NOT EXISTS Mod_Version (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Version VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Modpack (Name VARCHAR(255) PRIMARY KEY ASC, Short_Description VARCHAR(255) NOT NULL, Description TEXT NOT NULL DEFAULT '', Downloads INTEGER NOT NULL, ID INTEGER, IMG_URL TEXT NOT NULL, URL TEXT NOT NULL, Last_Updated TIMESTAMP NOT NULL, Created TIMESTAMP, Last_Checked TIMESTAMP, Last_Description TIMESTAMP, Wiki TEXT NOT NULL DEFAULT '', Issue_Tracker TEXT NOT NULL DEFAULT '', Source TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS Modpack_Category (Name VARCHAR(255) PRIMARY KEY ASC, IMG_URL TEXT NOT NULL, URL TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS Modpack_Category_Map (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Category VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Modpack_File (ID INTEGER PRIMARY KEY DESC, Mod VARCHAR(255) NOT NULL, Name TEXT NOT NULL, Size INTEGER NOT NULL, Uploaded TIMESTAMP NOT NULL, Downloads INTEGER NOT NULL, Type VARCHAR(1) NOT NULL DEFAULT 'R', Uploaded_By VARCHAR(255) NOT NULL DEFAULT '', Changelog TEXT NOT NULL DEFAULT '', Server_ID INTEGER, Server_Size VARCHAR(255) NOT NULL DEFAULT '', Server_Downloads INTEGER, Installed BOOLEAN DEFAULT FALSE, Last_Played TIMESTAMP);
        CREATE TABLE IF NOT EXISTS Modpack_File_Version (ID INTEGER PRIMARY KEY, File_ID INTEGER NOT NULL, Version VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Modpack_File_Dependency (ID INTEGER PRIMARY KEY, File_ID INTEGER NOT NULL, Dependency VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Modpack_Member (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Member VARCHAR(255) NOT NULL, Type VARCHAR(100) NOT NULL DEFAULT 'Owner');
        CREATE TABLE IF NOT EXISTS Modpack_Version (ID INTEGER PRIMARY KEY, Mod VARCHAR(255) NOT NULL, Version VARCHAR(255) NOT NULL);
        CREATE TABLE IF NOT EXISTS Version (I INTEGER ASC, Name VARCHAR(255) PRIMARY KEY ASC, ID VARCHAR(100) NOT NULL UNIQUE, Parent VARCHAR(255) NOT NULL DEFAULT '', Mods_Last_Updated TIMESTAMP, Modpacks_Last_Updated TIMESTAMP);
        CREATE TABLE IF NOT EXISTS Version_Updated (ID INTEGER PRIMARY KEY, Last_Updated TIMESTAMP);
    ''')
    c.commit()


def startup():
    if not exists('launcher'):
        mkdir('launcher')
    c = connect('launcher/client.db', detect_types=PARSE_DECLTYPES | PARSE_COLNAMES, check_same_thread=False)
    c.row_factory = MyRow
    create_tables(c)
    return c
