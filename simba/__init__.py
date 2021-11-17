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
        database.updateTable(self.cur,self.name,types,verbose=verbose)
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
    def addTable(self,tableName):
        tableret = table()
        tableret.simbaPath = self.simbaPath
        tableret.config = self.config
        tableret.scripts = self.scripts
        tableret.db = self.db
        tableret.cur = self.cur
        tableret.name = tableName
        database.updateTable(tableret.cur, tableName, None,verbose=False)
        tableret.db.commit()
        return tableret
    def copyTable(self,tablenew):
        tableret = table()
        tableret.simbaPath = self.simbaPath
        tableret.config = self.config
        tableret.scripts = self.scripts
        tableret.db = self.db
        tableret.cur = self.cur
        tableret.name = tablenew.name
        recs = tablenew.get()
        if len(recs): types = database.getTypes(recs[0])
        else: types = None
        database.updateTable(tableret.cur,tableret.name,types,verbose=False)
        for rec in recs: tableret.update(rec)
        tableret.db.commit()
        return tableret
    def close(self):
        self.db.close()

def open(filename = None, database = None):
    dbret = db()
    simbaPath = util.getSimbaDir(pathlib.Path(filename) if filename else pathlib.Path.cwd())
    if simbaPath:
        config    = util.getConfigFile(simbaPath)
        scripts   = util.getScripts(config)
        dbret.simbaPath = simbaPath
        dbret.config = config
        dbret.scripts = scripts
    if database: dbret.db = sqlite3.connect(database)
    else: dbret.db = sqlite3.connect(str(simbaPath/"results.db"))
    dbret.db.text_factory = str
    dbret.cur = dbret.db.cursor()
    return dbret


