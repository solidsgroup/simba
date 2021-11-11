#!/usr/bin/env python3
import argparse
import sqlite3
import hashlib
import os
import re
import simba
import configparser
from glob import *
from os.path import *
import importlib.util
import pathlib
import sys

#For deploy mode
#from . import util
#from . import simba
#For local mode
from simba import util
from simba import database
#simbaPath = util.getSimbaDir(pathlib.Path.cwd())




db_local = sqlite3.connect(sys.argv[3])
cur_local = db_local.cursor()

db_remote = sqlite3.connect(sys.argv[2])
cur_remote = db_remote.cursor()

# Start off looking at all of the tables
cur_local.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables_local  = [d[0] for d in cur_local.fetchall()]
if '__tables__' not in tables_local: print("Local db appears to be empty")
else: tables_local.remove('__tables__')
tables_local = set(tables_local)
cur_remote.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables_remote  = sorted([d[0] for d in cur_remote.fetchall()])
if '__tables__' not in tables_remote: print("Remote db appears to be empty")
tables_remote.remove('__tables__')
tables_remote = set(tables_remote)


tables_both = tables_local & tables_remote
tables_added = tables_remote - tables_local
tables_deleted = tables_local - tables_remote

if len(tables_added):
    print(util.green("\nAdded tables"))
    for table in tables_added: print("\t" + util.green(table)) 
if len(tables_deleted):
    print(util.red("\nDeleted tables"))
    for table in tables_deleted: print("\t" + util.red(table)) 

for table in sorted(tables_both):
    quiet = True
    def printTableName(): 
        if quiet: 
            print("TABLE: " + table); quiet = False
    cur_local.execute('PRAGMA table_info("' + table + '")')
    columns_local = set([d[1] for d in cur_local.fetchall()])
    cur_remote.execute('PRAGMA table_info("' + table + '")')
    columns_remote = set([d[1] for d in cur_remote.fetchall()])

    shared_columns = columns_local & columns_remote
    columns_added = columns_local - columns_remote
    columns_deleted = columns_remote - columns_local

    ## Do this if columns have been added. To be implemented.
    if columns_added:   
        printTableName()
        print("Columns added!", columns_added)
    if columns_deleted: 
        printTableName()
        print("Columns deleted!", columns_deleted)
    
    ## Do this if columns are exactly the same
    query = 'SELECT ' + ','.join(['"'+c+'"' for c in shared_columns]) + ' FROM "' + table + '"'
    ## Get local records
    cur_local.execute(query)
    data_local = [list(d) for d in cur_local.fetchall()]
    records_local = []
    for data in data_local:
        item=dict()
        for c,d in zip(columns_local,data): item[c] = d
        records_local.append(item)
    ## Get remote records
    cur_remote.execute(query)
    data_remote = [list(d) for d in cur_remote.fetchall()]
    records_remote = []
    for data in data_remote:
        item=dict()
        for c,d in zip(columns_remote,data): item[c] = d
        records_remote.append(item)

    hashes_local = set([i['HASH'] for i in records_local])
    hashes_remote = set([i['HASH'] for i in records_remote])

    hashes_both = hashes_local & hashes_remote
    hashes_added = hashes_local - hashes_remote
    hashes_deleted = hashes_remote - hashes_local
        
    for hash in hashes_both:
        record_local = next(item for item in records_local if item['HASH'] == hash)
        record_remote = next(item for item in records_remote if item['HASH'] == hash)
        for key in record_local.keys():
            if (record_local[key] != record_remote[key]):
                printTableName()
                print("\t",record_local['HASH'],key,record_local[key],record_remote[key])

    if hashes_added: 
        printTableName
    for hashes in hashes_added:
        record_local = next(item for item in records_local if item['HASH'] == hash)
        printTableName()
        print(util.green("\tAdded: "+record_local['HASH']+record_local['DIR']))
    if hashes_deleted: 
        printTableName()
    for hashes in hashes_deleted:
        record_remote = next(item for item in records_remote if item['HASH'] == hash)
        printTableName()
        print(util.red("\tDeleted: ",record_remote['HASH'],record_remote['DIR']))

    







#print(tables_added)
#print(tables_deleted)








        
