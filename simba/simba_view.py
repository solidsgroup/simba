#!/usr/bin/env python3
import argparse
import sqlite3
import hashlib
import os
import re
import simba
import configparser
import glob
import importlib.util
import pathlib

from simba import util
from simba import simba

simbaPath = util.getSimbaDir(pathlib.Path.cwd())
config    = util.getConfigFile(simbaPath)
scripts   = util.getScripts(config)

parser = argparse.ArgumentParser(description='Sift through outputs')
parser.add_argument('mode')
parser.add_argument('table',nargs='?',default=None)
parser.add_argument('filters',nargs='*')

parser.add_argument('-d','--database', default=str(simbaPath/'results.db'), help='Name of database')
#parser.add_argument('-r','--remove', nargs='*', help='Tables to remove')
parser.add_argument('-t','--tag', default=None, help='Table name in database')
#parser.add_argument('-a','--all', action='store_true', default=False, help='Force update of ALL records')
args=parser.parse_args()
print(args.database)
#tables = []
#if (simbaPath/"data.ini").is_file():
#    config = configparser.ConfigParser()
#    config.read(simbaPath/"data.ini")
#    for sec in config.sections():
#        multisecs = glob.glob(str(simbaPath/sec))
#        if len(multisecs) > 0:
#            print(util.red(simbaPath/sec))
#            for subsec in multisecs:
#                #print("\t",util.green(simbaPath/subsec))
#                #print("\t\t",(simbaPath/subsec).name)
#                if "name" in config[sec]:
#                    tablename = config[sec]["name"].replace("$VARDIR",str((simbaPath/subsec).name))
#                else:
#                    tablename = str((simbaPath/subsec).name)
#
#                #tablename = tablename.replace('-','_')
#                tablematch = config[sec]["match"].replace("$VARPATH",str(simbaPath/subsec))
#
#                table = {"name":tablename, "match":tablematch}
#                tables.append(table)
#        else:
#            if '-' in sec:
#                raise Exception("Table name "+sec+" contains a hyphen; hyphens are not allowed.")
#            table = {"name":sec, "match":config[sec]["match"]}
#            tables.append(table)
#
from terminaltables import SingleTable

db = sqlite3.connect(args.database if args.database.endswith('.db') else args.database+'.db')
db.text_factory = str
cur= db.cursor()

cur.execute('SELECT NAME,Description from "__tables__" WHERE NAME LIKE "{}"'.format(args.table if args.table else '%'))
entries = cur.fetchall()
print(SingleTable([('Table','Description')]+entries).table)
tables = [e[0] for e in entries]

for table in tables:
    fs = []
    for f in args.filters:
        s = f.split('=')
        fs.append('"{}" LIKE "{}"'.format(s[0],s[1]))
    print(" AND ".join(fs))

    print(table)
    cols = [('DIR','Description','Tags')]
    cur.execute('SELECT {} FROM "{}" {}'.format(','.join(cols[0]),table,"WHERE "+" AND ".join(fs) if fs else ""))
    entries = cur.fetchall()
    print(SingleTable(cols + entries).table)
    if args.tag:
        print(args.tag)


#
#for table in tables:
#    types = dict()
#    directories = sorted(glob.glob(str(simbaPath/table["match"])))
#
#
#    #
#    # Scan metadata files to determine columns
#    #
#    for directory in directories:
#        data = scripts.parseOutputDir(directory)
#        if data:
#            types.update(simba.getTypes(data))
#        
#    #
#    # Update/create the chosen table so all the values are represented
#    #
#    simba.updateTable(cur,table['name'],types,"results",False)
#    entries = simba.getTableEntries(cur,table['name'])
#
#    #
#    # If there are tables to delete, delete them
#    # TODO
#    #if args.remove:
#    #    for tab in list(args.remove):
#    #        cur.execute('DROP TABLE ' + tab)
#
#
#    #
#    # Scan each metadata file and add an entry to the table, skipping any
#    # records that already exist.
#    #
#    new = []
#    moved = []
#    bad = []
#    for directory in directories:
#        dirhash = scripts.getHash(directory)
#        dirname = os.path.abspath(directory)
#        data = scripts.parseOutputDir(directory)
#        if not data or not dirhash:
#            bad.append(dirname)
#            continue
#        
#        status = "new"
#        for e in entries:
#            if dirhash == e[0] and dirname == e[1]:
#                status = "old"
#                break
#            elif dirhash == e[0] and not dirname == e[1]:
#                status = "moved"
#                moved.append([e[1],dirname])
#                break
#        if status == "new":
#            new.append(dirname)
#
#        if not dirhash:
#            raise Exception("parseOutputDir.parse MUST include a HASH in its output")
#        if args.mode == "add":
#            if status == "new":
#                print('\033[32madded        ',dirname,'\033[1;0m')
#                simba.updateRecord(cur,table['name'],data,dirhash,dirname,False)
#            if status == "moved":
#                print('\033[33mmoved     ',moved[-1][0],'\033[1;0m')
#                print('\033[33m             ⮡',moved[-1][1],'\033[1;0m')
#                simba.updateRecord(cur,table['name'],data,dirhash,dirname,False)
#
#    if args.mode == "status":
#        if len(new)>0 or len(moved)>0 or len(bad)>0:
#            for n in new:
#                print('\033[32mnew       ',n,'\033[1;0m')
#            for m in moved:
#                print('\033[33mmoved     ',m[0],'\033[1;0m')
#                print('\033[33m             ⮡',m[1],'\033[1;0m')
#            for b in bad:
#                print('\033[31mbad       ',b,'\033[1;0m')
#    
#db.commit()
#db.close()
    
