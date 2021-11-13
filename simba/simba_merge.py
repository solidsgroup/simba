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
db_base   = simba.open(filename=sys.argv[5],database=sys.argv[3])
db_remote = simba.open(filename=sys.argv[5],database=sys.argv[4])
db_merge  = simba.open(filename=sys.argv[5],database=sys.argv[5])

tables_local  = set(db_local.getTableNames())
tables_base   = set(db_base.getTableNames())
tables_remote = set(db_remote.getTableNames())

tables_all = tables_local & tables_base & tables_remote
tables_added_by_local  = tables_local - tables_base - tables_remote
tables_added_by_remote = tables_remote - tables_base - tables_local
tables_added_by_both   = (tables_local - tables_base) & (tables_remote - tables_base)

if tables_added_by_local:
    quiet = True
    for table in tables_added_by_local: 
        if quiet: 
            print(util.green("\nAdding tables from LOCAL"))
            quiet = False
        print(util.green("\t" + table))
        table_local = db_local.getTable(table)
        db_merge.copyTable(table_local)
if tables_added_by_remote:
    quiet = True
    for table in tables_added_by_remote: 
        if quiet: 
            print(util.green("\nAdding tables from REMOTE"))
            quiet = False
        print(util.green("\t" + table))
        table_remote = db_remote.getTable(table)
        db_merge.copyTable(table_remote)

if tables_added_by_both:
    quiet = True
    for table in tables_added_by_both:
        if quiet: 
            print(util.green("\nAdding tables from LOCAL and REMOTE"))
            quiet = False
        print(util.green("\t" + table))
        table_merge = db_merge.addTable(table)
        
        table_local = db_local.getTable(table)
        table_remote = db_remote.getTable(table)
        records_local = table_local.get()
        records_remote = table_remote.get()
        hashes_local = set([rec['HASH'] for rec in records_local])
        hashes_remote = set([rec['HASH'] for rec in records_remote])

        hashes_both = hashes_local & hashes_remote
        hashes_local_only = hashes_local - hashes_remote
        hashes_remote_only = hashes_remote - hashes_local

        for myhash in hashes_local_only:  
            rec = next(item for item in records_local  if item['HASH'] == myhash)
            print(util.green("\t\tAdding (LOCAL): "+rec['HASH']+', '+rec['DIR']))
            table_merge.update(red)
        for myhash in hashes_remote_only: 
            rec = next(item for item in records_remote if item['HASH'] == myhash)
            print(util.green("\t\tAdding (REMOTE): "+rec['HASH']+', '+rec['DIR']))
            table_merge.update(rec)
        for myhash in hashes_both:
            rec_merged = dict()
            rec_local  = next(item for item in records_local  if item['HASH'] == myhash)
            rec_remote = next(item for item in records_remote  if item['HASH'] == myhash)
            print(util.green("\t\tAdding (REMOTE and LOCAL): "+rec['HASH']))
            cols = set(rec_local.keys()) | set(rec_remote.keys())
            for col in cols:
                if col not in rec_local.keys():         rec_merged[col] = rec_remote[col]
                elif col not in rec_remote.keys():      rec_merged[col] = rec_local[col]
                elif rec_remote[col] == rec_local[col]: rec_merged[col] = rec_local[col]
                else:
                    print(util.yellow('\t\t\tMerge conflict: '+col+' = '))
                    print("\t\t\t\t"+util.blue(rec_local[col])+" (LOCAL)")
                    print("\t\t\t\t"+util.green(rec_remote[col])+" (REMOTE)")
                    ch = input("\t\t\t\tOPTIONS: " + util.blue("1=LOCAL") + ", " + util.green("2=REMOTE") + ", 3=Concatenate, 4=ignore: ")
                    if ch == '1': rec_merged[col] = rec_local[col]
                    elif ch == '2': rec_merged[col] = rec_remote[col]
                    elif ch == '3': rec_merged[col] = str(rec_local[col]) + " " + str(rec_remote[col])
                    elif ch == '4': rec_merged[col] = ''
            table_merge.update(rec_merged)

if tables_all:
    print(util.yellow("\nUpdating tables from BASE and LOCAL and REMOTE"))
    for table in tables_all:
        quiet = True
        def printTable(quiet):
            print(util.yellow('\t' + table))
            return False        

        table_local = db_local.getTable(table)
        table_remote = db_remote.getTable(table)
        table_base = db_base.getTable(table)
        table_merged = db_merge.getTable(table)
        
        records_local = table_local.get()
        records_remote = table_remote.get()
        records_base = table_base.get()

        hashes_local = set([rec['HASH'] for rec in records_local])
        hashes_remote = set([rec['HASH'] for rec in records_remote])
        hashes_base = set([rec['HASH'] for rec in records_base])

        hashes_nochange = hashes_local & hashes_remote & hashes_base
        hashes_remote_and_local = (hashes_remote - hashes_base) & (hashes_local-hashes_base)
        hashes_base_and_local = (hashes_base & hashes_local) - hashes_remote
        hashes_base_and_remote = (hashes_base & hashes_remote)- hashes_local
        
        for myhash in hashes_base_and_local:  
            rec = next(item for item in records_local  if item['HASH'] == myhash)
            quiet = printTable(quiet)
            print(util.green("\t\tAdding (LOCAL): "+rec['HASH']+', '+rec['DIR']))
            table_merge.update(rec)
        for myhash in hashes_base_and_remote: 
            rec = next(item for item in records_remote if item['HASH'] == myhash)
            quiet = printTable(quiet)
            print(util.green("\t\tAdding (REMOTE): "+rec['HASH']+', '+rec['DIR']))
            table_merge.update(rec)
        for myhash in hashes_remote_and_local:
            hashquiet = True
            rec_remote = next(item for item in records_remote  if item['HASH'] == myhash)
            rec = next(item for item in records_local  if item['HASH'] == myhash)
            print(util.green("\t\tAdding (REMOTE and LOCAL): "+myhash))
            cols = set(rec_local.keys()) | set(rec_remote.keys())
            for col in cols:
                if col not in rec_local.keys():         rec_merged[col] = rec_remote[col]
                elif col not in rec_remote.keys():      rec_merged[col] = rec_local[col]
                elif rec_remote[col] == rec_local[col]: rec_merged[col] = rec_local[col]
                else:
                    quiet=printTable(quiet)
                    if hashquiet: 
                        print(util.yellow('\t\tUpdating: '+str(myhash)))
                        hashquiet = False
                    print(util.yellow('\t\t\tMerge conflict: '+col+' = '))
                    print("\t\t\t\t"+util.blue(rec_local[col])+" (LOCAL)")
                    print("\t\t\t\t"+util.green(rec_remote[col])+" (REMOTE)")
                    ch = input("\t\t\t\tOPTIONS: " + util.blue("1=LOCAL") + ", " + util.green("2=REMOTE") + ", 3=Concatenate, 4=ignore: ")
                    if ch == '1': rec_merged[col] = rec_local[col]
                    elif ch == '2': rec_merged[col] = rec_remote[col]
                    elif ch == '3': rec_merged[col] = str(rec_local[col]) + " " + str(rec_remote[col])
                    elif ch == '4': rec_merged[col] = ''
            table_merge.update(rec_merged)
        for myhash in hashes_nochange:
            hashquiet = True
            rec_merged = dict()
            rec_local  = next(item for item in records_local  if item['HASH'] == myhash)
            rec_remote = next(item for item in records_remote  if item['HASH'] == myhash)
            rec_base   = next(item for item in records_base  if item['HASH'] == myhash)
            cols_local = set(rec_local.keys())
            cols_remote = set(rec_remote.keys())
            cols_base = set(rec_base.keys())
            for col in cols_local | cols_remote | cols_base:
                # if column shows up in all three?
                if col in cols_base and col in cols_remote and col in cols_local: 
                    if rec_base[col] == rec_local[col] and rec_base[col] == rec_remote[col]: rec_merged[col] = rec_base[col]
                    else:
                        quiet=printTable(quiet)
                        if hashquiet: 
                            print(util.yellow('\t\tUpdating: '+str(myhash)))
                            hashquiet = False
                        print(util.yellow('\t\t\tMerge conflict: '+col+' = '))
                        print("\t\t\t\t"+util.cyan(rec_base[col])+" (BASE)")
                        print("\t\t\t\t"+util.blue(rec_local[col])+" (LOCAL)")
                        print("\t\t\t\t"+util.green(rec_remote[col])+" (REMOTE)")
                        ch = input("\t\t\t\tOPTIONS: " + util.cyan("0=BASE") + ", " + util.blue("1=LOCAL") + ", " + util.green("2=REMOTE") + ", 3=Concatenate, 4=ignore: ")
                        if ch == '0': rec_merged[col] = rec_base[col]
                        elif ch == '1': rec_merged[col] = rec_local[col]
                        elif ch == '2': rec_merged[col] = rec_remote[col]
                        elif ch == '3': rec_merged[col] = str(rec_base[col]) + " " + str(rec_local[col]) + " " + str(rec_remote[col])
                        elif ch == '4': rec_merged[col] = ''
                # if column is in BASE and REMOTE only but not LOCAL?
                elif col in (cols_base & cols_remote):
                    rec_merged[col] = rec_remote[col]
                # if column is BASE and LOCAL but not in REMOTE?
                elif col in (cols_base & cols_local):
                    rec_merged[col] = rec_local[col]
                # if column is in REMOTE and LOCAL but not in BASE?
                elif cols in (cols_base & cols_local):
                    quiet=printTable(quiet)
                    print(util.yellow('\t\t\tMerge conflict: '+col+' = '))
                    print("\t\t\t\t"+util.blue(rec_local[col])+" (LOCAL)")
                    print("\t\t\t\t"+util.green(rec_remote[col])+" (REMOTE)")
                    ch = input("\t\t\t\tOPTIONS: " + util.blue("1=LOCAL") + ", " + util.green("2=REMOTE") + ", 3=Concatenate, 4=ignore: ")
                    if ch == '1': rec_merged[col] = rec_local[col]
                    elif ch == '2': rec_merged[col] = rec_remote[col]
                    elif ch == '3': rec_merged[col] = str(rec_local[col]) + " " + str(rec_remote[col])
                    elif ch == '4': rec_merged[col] = ''
            table_merged.update(rec_merged)


print("")

db_base.close()
db_local.close()
db_remote.close()
db_merge.close()



        
