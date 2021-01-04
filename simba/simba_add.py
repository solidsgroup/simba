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

#For deploy mode
#from . import util
#from . import simba
#For local mode
from simba import util
from simba import simba

simbaPath = util.getSimbaDir(pathlib.Path.cwd())
config    = util.getConfigFile(simbaPath)
scripts   = util.getScripts(config)

parser = argparse.ArgumentParser(description='Sift through outputs')
parser.add_argument('mode')
parser.add_argument('directories', nargs='*', help='List of directories containing ALAMO output')
parser.add_argument('-d','--database', default=str(simbaPath/'results.db'), help='Name of database')
parser.add_argument('-r','--remove', nargs='*', help='Tables to remove')
parser.add_argument('-t','--table', default='simulation_data', help='Table name in database')
parser.add_argument('-a','--all', action='store_true', default=False, help='Force update of ALL records')
args=parser.parse_args()

tables = []
if (simbaPath/"data.ini").is_file():
    config = configparser.ConfigParser()
    config.read(simbaPath/"data.ini")
    for sec in config.sections():
        if len(sec.split(' ')) == 1:
            # option 1: name only
            if '-' in sec:
                raise Exception("Table name "+sec+" contains a hyphen; hyphens are not allowed.")
            names = [sec]
        elif "for" in sec.split(' '):
            # option 2: execute python query
            exec("names = [" + sec + "]")
        else:
            # option 3: treat as list of names
            names = sec.split(' ')

        match = config[sec]['match']
        
        for name in names:
            if config.has_option(sec,'name'): tablename = config[sec]['name'].replace("$NAME",name)
            else: tablename = name


            table = {"name":tablename, "match":match.replace("$NAME",name)}
            tables.append(table)

else:
    print("No data.ini file found")
        

db = sqlite3.connect(args.database if args.database.endswith('.db') else args.database+'.db')
db.text_factory = str
cur= db.cursor()

for table in tables:
    types = dict()
    #directories = sorted(glob(str(simbaPath/".."/table["match"])))
    directories = sorted(glob(str(table["match"])))

    #
    # Scan metadata files to determine columns
    #
    for directory in directories:
        data = scripts.parseOutputDir(str(simbaPath)+"/../"+directory)
        if data:
            types.update(simba.getTypes(data))
        
    #
    # Update/create the chosen table so all the values are represented
    #
    entries = simba.getTableEntries(cur,table['name'])
    if len(entries) > 0 or len(directories) > 0:
        simba.updateTable(cur,table['name'],types,"results",False)

    #
    # If there are tables to delete, delete them
    # TODO
    #if args.remove:
    #    for tab in list(args.remove):
    #        cur.execute('DROP TABLE ' + tab)


    #
    # Scan each metadata file and add an entry to the table, skipping any
    # records that already exist.
    #
    new = []
    moved = []
    bad = []
    for directory in directories:
        dirhash = scripts.getHash(str(simbaPath)+"/../"+directory)
        dirname = directory
        data = scripts.parseOutputDir(str(simbaPath)+"/../"+directory)
        if not data or not dirhash:
            bad.append(dirname)
            continue
        
        status = "new"
        for e in entries:
            if dirhash == e[0] and dirname == e[1]:
                status = "old"
                break
            elif dirhash == e[0] and not dirname == e[1]:
                status = "moved"
                moved.append([e[1],dirname])
                break
        if status == "new":
            new.append(dirname)

        if not dirhash:
            raise Exception("parseOutputDir.parse MUST include a HASH in its output")
        if args.mode == "add":
            if status == "new":
                print('\033[32madded        ',dirname,'\033[1;0m')
                simba.updateTable(cur,table['name'],types,"results",False) ## TODO remove this
                simba.updateRecord(cur,table['name'],data,dirhash,dirname,False)
            elif status == "moved":
                print('\033[33mmoved     ',moved[-1][0],'\033[1;0m')
                print('\033[33m             ⮡',moved[-1][1],'\033[1;0m')
                simba.updateRecord(cur,table['name'],data,dirhash,dirname,False)
            elif args.all:
                print('\033[32mupdated      ',dirname,'\033[1;0m')
                simba.updateRecord(cur,table['name'],data,dirhash,dirname,False)
    if args.mode == "status":
        if len(new)>0 or len(moved)>0 or len(bad)>0:
            for n in new:
                print('\033[32mnew       ',n,'\033[1;0m')
            for m in moved:
                print('\033[33mmoved     ',m[0],'\033[1;0m')
                print('\033[33m             ⮡',m[1],'\033[1;0m')
            for b in bad:
                print('\033[31mbad       ',b,'\033[1;0m')
    
    if len(entries) > 0 or len(directories) > 0:
        simba.updateTable(cur,table['name'],types,"results",False)

    
    entries = simba.getTableEntries(cur,table['name'])
    for e in entries:
        directory = e[1]

        if directory == 'null': continue

        tablehash = e[0]
        dirhash   = scripts.getHash(directory)

        ghost = False
        if not dirhash: ghost = True
        if tablehash != dirhash: ghost = True

        if ghost:
            print('\033[90mghost      ('+tablehash+') \033[9m'+directory+'\033[0m')
            simba.updateRecord(cur,table['name'], None, tablehash, 'null')
        


db.commit()
db.close()
    
