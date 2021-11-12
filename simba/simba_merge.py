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


print("\n\n### SIMBA MERGE ###")


db_local  = simba.open(filename=sys.argv[5],database=sys.argv[2])
db_base = simba.open(filename=sys.argv[5],database=sys.argv[3])
db_remote = simba.open(filename=sys.argv[5],database=sys.argv[4])
db_merge = simba.open(filename=sys.argv[5],database=sys.argv[5])


# Start off looking at all of the tables
# LOCAL
tables_local = set(db_local.getTableNames())
# BASE
tables_base = set(db_base.getTableNames())
# REMOTE
tables_remote = set(db_remote.getTableNames())

tables_all = tables_local & tables_base & tables_remote
tables_added_by_local  = tables_local - tables_base - tables_remote
tables_added_by_remote = tables_remote - tables_base - tables_local
tables_added_by_both   = (tables_local - tables_base) & (tables_remote - tables_base)

print(tables_all)
print(tables_added_by_local)
print(tables_added_by_remote)
print(tables_added_by_both)

if tables_added_by_local:
    print(util.green(str(len(tables_added_by_local)) + " tables were added by LOCAL. Add them?"))
    ch = input(util.green("\tOPTIONS: y=add all, n=add none, a=ask for each [a]: "))    
    if ch in ['y','yes','Y','Yes','YES']:
        for table in tables_added_by_local: 
            print(util.green("\tAdding: " + table))
            table_local = db_local.getTable(table)
            db_merge.copyTable(table_local)
            print(db_merge.getTableNames())
    elif ch in ['a','A']:
        for table in tables_added_by_local: 
            table_local = db_local.getTable(table)
            ch = input(util.green("\t\tAdd " + table + "? [yN]: "))
            if ch in ['y','yes','Y','Yes','YES']:
                db_merge.copyTable(table_local)
                print(db_merge.getTableNames())
    elif ch not in ['n','N','no','No','NO']:
        raise Exception(ch + " is not valid.")    
if tables_added_by_remote:
    print(util.green(str(len(tables_added_by_remote)) + " tables were added by REMOTE. Add them?"))
    ch = input(util.green("\tOPTIONS: y=add all, n=add none, a=ask for each [a]: "))    
    if ch in ['y','yes','Y','Yes','YES']:
        for table in tables_added_by_remote: 
            print(util.green("\tAdding: " + table))
            table_remote = db_remote.getTable(table)
            db_merge.copyTable(table_remote)
            print(db_merge.getTableNames())
    elif ch in ['a','A']:
        for table in tables_added_by_remote: 
            table_remote = db_remote.getTable(table)
            ch = input(util.green("\t\tAdd " + table + "? [yN]: "))
            if ch in ['y','yes','Y','Yes','YES']:
                db_merge.copyTable(table_remote)
                print(db_merge.getTableNames())
    elif ch not in ['n','N','no','No','NO']:
        raise Exception(ch + " is not valid.")    
if tables_added_by_both:
    for table in tables_added_by_both:
        ch = input(util.green("Table "+table+" added by LOCAL and REMOTE. Add and merge? [yN]: "))
        if ch in ['n','N','no','No','NO']: continue
        table_local = db_local.getTable(table)
        table_remote = db_remote.getTable(table)
        records_local = table_local.get()
        records_remote = table_remote.get()
        hashes_local = set([rec['HASH'] for rec in records_local])
        hashes_remote = set([rec['HASH'] for rec in records_remote])

        hashes_both = hashes_local & hashes_remote
        hashes_local_only = hashes_local - hashes_remote
        hashes_remote_only = hashes_remote - hashes_local

        print(hashes_both)
        print(hashes_local_only)
        print(hashes_remote)
        print(hashes_remote_only)

        records_merged = []
        for myhash in hashes_local_only:  
            print("Adding local only " + myhash)
            records_merged = records_merged + [item for item in records_local  if item['HASH'] == myhash]
        for myhash in hashes_remote_only: 
            print("Adding remote only " + myhash)
            print([item for item in records_remote if item['HASH'] == myhash])
            records_merged = records_merged + [item for item in records_remote if item['HASH'] == myhash]
        for myhash in hashes_both:
            rec_merged = dict()
            rec_local  = next(item for item in records_local  if item['HASH'] == myhash)
            rec_remote = next(item for item in records_remote  if item['HASH'] == myhash)
            cols = set(rec_local.keys()) | set(rec_remote.keys())
            for col in cols:
                if col not in rec_local.keys():         rec_merged[col] = rec_remote[col]
                elif col not in rec_remote.keys():      rec_merged[col] = rec_local[col]
                elif rec_remote[col] == rec_local[col]: rec_merged[col] = rec_local[col]
                else:
                    print("\t"+col+":\tLocal = [" + util.blue(rec_local[col]) + "], Remote = [" + util.green(rec_remote[col]) + "]")
                    ch = input("\t\tOPTIONS: " + util.blue("l=use local, ") + util.green("r=use remote") + " c= combine, i=ignore [l]: ")
                    if   ch in ['l','L']: rec_merged[col] = rec_local[col]
                    elif ch in ['r','R']: rec_merged[col] = rec_remote[col]
                    elif ch in ['c','C']: rec_merged[col] = str(rec_local[col]) + " " + str(rec_remote[col])
                    elif ch in ['i','I']: continue
                    else: raise Exception(ch + " is not an acceptable answer")
            records_merged.append(rec_merged)
        table_merged = db_merge.addTable(table)
        for rec in records_merged:
            table_merged.update(rec)
            





exit()


if len(tables_added):
    print(util.green("\nAdded tables"))
    for table in tables_added: print("\t" + util.green(table)) 
if len(tables_deleted):
    print(util.red("\nDeleted tables"))
    for table in tables_deleted: print("\t" + util.red(table)) 

for table in sorted(tables_both):
    quiet = True
    def printTableName(quiet): 
        if quiet: print(util.yellow("\nModified table: " + table)); 
        return False
    cur_local.execute('PRAGMA table_info("' + table + '")')
    columns_local = set([d[1] for d in cur_local.fetchall()])
    cur_remote.execute('PRAGMA table_info("' + table + '")')
    columns_remote = set([d[1] for d in cur_remote.fetchall()])

    columns_both = columns_local & columns_remote
    columns_added = columns_local - columns_remote
    columns_deleted = columns_remote - columns_local

    ## Do this if columns have been added. To be implemented.
    if columns_added:   
        quiet = printTableName(quiet)
        print(util.green("\tColumns added: " + " ".join(columns_added)))
    if columns_deleted: 
        quiet = printTableName(quiet)
        #print(util.red("\tColumns deleted: " + " ".join(columns_deleted)))
    
    ## Do this if columns are exactly the same
    query = 'SELECT ' + ','.join(['"'+c+'"' for c in columns_local]) + ' FROM "' + table + '"'
    ## Get local records
    cur_local.execute(query)
    data_local = [list(d) for d in cur_local.fetchall()]
    records_local = []
    for data in data_local:
        item=dict()
        for c,d in zip(columns_local,data): item[c] = d
        records_local.append(item)
    ## Get remote records
    query = 'SELECT ' + ','.join(['"'+c+'"' for c in columns_remote]) + ' FROM "' + table + '"'
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
        

    if hashes_added: 
        quiet = printTableName(quiet)
    for myhash in sorted(list(hashes_added)):
        record_local = next(item for item in records_local if item['HASH'] == myhash)
        quiet = printTableName(quiet)
        print(util.green("\tAdded record: "+str(record_local['HASH'])+" "+str(record_local['DIR'])))
    if hashes_deleted: 
        quiet = printTableName(quiet)
    for myhash in sorted(list(hashes_deleted)):
        record_remote = next(item for item in records_remote if item['HASH'] == myhash)
        quiet = printTableName(quiet)
        print(util.red("\tDeleted record: "+str(record_remote['HASH'])+" "+str(record_remote['DIR'])))

    for myhash in hashes_both:
        recordquiet = True
        def printRecordName(recordquiet):
            if recordquiet: print(util.yellow("\tModified record: "+str(myhash) + " " + str(record_local['DIR'])))
            return False
        record_local = next(item for item in records_local if item['HASH'] == myhash)
        record_remote = next(item for item in records_remote if item['HASH'] == myhash)
        for key in record_local.keys():
            if (record_local[key] != record_remote[key]):
                quiet = printTableName(quiet)
                recordquiet = printRecordName(recordquiet)
                print("\t\t",key,": ", util.darkgray(record_remote[key])," --> ",util.green(record_local[key]))

    



db_local.close()
db_remote.close()



#print(tables_added)
#print(tables_deleted)








        
