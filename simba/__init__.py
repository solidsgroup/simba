import pathlib
import sqlite3

import simba.util


class table:
    db = None
    cur = None
    name = None
    def getColumnNames(self):
        self.cur.execute('PRAGMA table_info("' + self.name + '")')
        data = [d[1] for d in self.cur.fetchall()]
        return data

    def get(self,
            columns=None,alias=None,
            match=None,
            asdict=True,
            ):
        if not columns: columns = self.getColumnNames()
        query = 'SELECT ' + ','.join(['"'+c+'"' for c in columns]) + ' FROM "' + self.name + '"' + (' WHERE ' + match if match else '')
        self.cur.execute(query)
        data = [list(d) for d in self.cur.fetchall()]
        if asdict:
            ret = []
            for dat in data:
                item = dict()
                for c,d in zip(alias if alias else columns,dat):
                    item[c] = d
                ret.append(item)
            return ret
        else:
            return data


class db:
    db  = None
    cur = None
    def getTableNames(self):
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        dat = [d[0] for d in self.cur.fetchall()]
        dat.remove('__tables__')
        return dat
    def getTable(self,tableName):
        tablenames = self.getTableNames()
        if not tableName in tablenames:
            raise Exception("Table ", tablenames," not in database")
        tableret = table()
        tableret.db = self.db
        tableret.cur = self.cur
        tableret.name = tableName
        return tableret



def open(filename = None):
    dbret = db()
    path = util.getSimbaDir(filename if filename else pathlib.Path.cwd())
    print(path)
    dbret.db = sqlite3.connect(path/"results.db")
    dbret.db.text_factory = str
    dbret.cur = dbret.db.cursor()
    return dbret


