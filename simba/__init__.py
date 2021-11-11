import pathlib
import sqlite3

import simba.util

from simba import simba_add
from simba import database

class table:
    simbaPath = None
    config = None
    scripts = None
    db = None
    cur = None
    name = None
    def getColumnNames(self):
        self.cur.execute('PRAGMA table_info("' + self.name + '")')
        data = [d[1] for d in self.cur.fetchall()]
        return data

    def get(self,
            columns=None,alias=None,
#            match=None,
            asdict=True,
            **kwargs
            ):
        
        matches = []
        for key, value in kwargs.items():
            matches.append('"{}" LIKE "{}"'.format(key.replace("DOT","."),value))
        match = ' AND '.join(matches)

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

    def add(self,verbose=False):
        simba_add.add(self.simbaPath,self.config,self.scripts,"add",specifictable=self.name,updateall=True,verbose=verbose)

    def update(self,record,verbose=False):
        types = database.getTypes(record)
        database.updateTable(self.cur,self.name,types)
        database.updateRecord(self.cur,self.name,record,record['HASH'],record['DIR'],verbose=verbose)
        self.db.commit()
        
class db:
    simbaPath = None
    config = None
    scripts = None
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
        tableret.simbaPath = self.simbaPath
        tableret.config = self.config
        tableret.scripts = self.scripts
        tableret.db = self.db
        tableret.cur = self.cur
        tableret.name = tableName
        return tableret



def open(filename = None):
    dbret = db()
    simbaPath = util.getSimbaDir(filename if filename else pathlib.Path.cwd())
    config    = util.getConfigFile(simbaPath)
    scripts   = util.getScripts(config)
    dbret.simbaPath = simbaPath
    dbret.config = config
    dbret.scripts = scripts
    dbret.db = sqlite3.connect(simbaPath/"results.db")
    dbret.db.text_factory = str
    dbret.cur = dbret.db.cursor()
    return dbret


