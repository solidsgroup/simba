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
from simba import database
#simbaPath = util.getSimbaDir(pathlib.Path.cwd())

def add(simbaPath, config, scripts, mode='add', __directories=None, databasename=None, remove=None, specifictable=None, updateall=False,verbose=True,locations=None):
    retlist = []

    from glob import glob
    from os.path import basename
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
                os.chdir(str(simbaPath)+'/../')
                exeret = dict()
                exec("from glob import glob; from os.path import basename; names = [" + sec + "]",exeret)
                names = exeret['names']
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
            
    
    if not databasename: databasename = simbaPath/"results.db"
    db = sqlite3.connect(str(databasename))
    db.text_factory = str
    cur= db.cursor()

    num_add = 0
    num_moved = 0
    num_bad = 0
    num_undead = 0 
    num_ghost = 0
    
    # 
    # If the locations optional argument is specified, we will restrict our directory search to the
    # specified paths.
    # Here, identify all the possible parent directories or directories in which to search, then
    # store in 'abslocations'
    #
    if locations:
        abslocations = set()
        for locationset in [glob(l) for l in locations]:
            for location in locationset:
                abslocations.add(pathlib.Path(location).absolute())

    
    for table in tables:
        if specifictable:
            if not table['name'] == specifictable:
                continue
        
        ret = dict()
        
        types = dict()
        directories = set([d.replace(str(simbaPath)+'/../','') for d in sorted(glob(str(str(simbaPath)+"/../"+table["match"])))])
                
        #
        # If optional locations argument is provided, filter out those directories not
        # included. Otherwise, continue with all directories specified.
        #
        if locations:
            keep = set()
            for dir in directories:
                for abslocation in abslocations:
                    if abslocation in pathlib.Path(dir).absolute().parents or abslocation == pathlib.Path(dir).absolute():
                        keep.add(dir)
            directories = keep
            
        #
        # Scan metadata files to determine columns
        #
        for directory in directories:
            try:
                data = scripts.parseOutputDir(str(simbaPath)+"/../"+directory)
            except Exception as e:
                data = None
                print("Error in ", directory)
                print(e)
            if data:
                types.update(database.getTypes(data))
            
        #
        # Update/create the chosen table so all the values are represented
        #
        entries = database.getTableEntries(cur,table['name'])
        if (len(entries) > 0 or len(directories) > 0) and mode=='add' :
            database.updateTable(cur,table['name'],types,"results",False)
    
        #
        # If there are tables to delete, delete them
        # TODO
        #if args.remove:
        #    for tab in list(args.remove):
        #        cur.execute('DROP TABLE ' + tab)
    
    
        entries = database.getTableEntries(cur,table['name'])
    
        #
        # Scan each metadata file and add an entry to the table, skipping any
        # records that already exist.
        #
        new = []
        moved = []
        bad = []
        undead = []
        for directory in directories:
            dirname = directory
            try:
                dirhash = scripts.getHash(str(simbaPath)+"/../"+directory)
                data = scripts.parseOutputDir(str(simbaPath)+"/../"+directory)
            except Exception as e:
                data = None
    
            if not data or not dirhash:
                if dirname in [e[1] for e in entries]:
                    undead.append(dirname)
                else:
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
            if mode == "add":
                if status == "new":
                    if(verbose): print('\033[32madded        ',dirname,'\033[1;0m')
                    database.updateTable(cur,table['name'],types,"results",False) ## TODO remove this
                    database.updateRecord(cur,table['name'],data,dirhash,dirname,False)
                elif status == "moved":
                    if(verbose): print('\033[33mmoved     ',moved[-1][0],'\033[1;0m')
                    if(verbose):print('\033[33m             ⮡',moved[-1][1],'\033[1;0m')
                    database.updateRecord(cur,table['name'],data,dirhash,dirname,False)
                elif updateall:
                    if(verbose):print('\033[32mupdated      ',dirname,'\033[1;0m')
                    database.updateRecord(cur,table['name'],data,dirhash,dirname,False)
        if mode == "status":
            if len(new)>0 or len(moved)>0 or len(bad)>0:
                for n in new:
                    if(verbose): print('\033[32mnew       ',n,'\033[1;0m')
                for m in moved:
                    if(verbose): print('\033[33mmoved     ',m[0],'\033[1;0m')
                    if(verbose): print('\033[33m             ⮡',m[1],'\033[1;0m')
                for b in bad:
                    if(verbose): print('\033[31mbad       ',b,'\033[1;0m')
        
        if (len(entries) > 0 or len(directories) > 0) and mode=='add':
            database.updateTable(cur,table['name'],types,"results",False)
    
        
        entries = database.getTableEntries(cur,table['name'])
        for e in entries:
            directory = e[1]
    
            if directory == 'null': continue
    
            tablehash = e[0]
            try:
                dirhash   = scripts.getHash(directory)
            except Exception as e:
                dirhash = None
    
            ghost = False
            if not dirhash: ghost = True
            if tablehash != dirhash: ghost = True
    
            if ghost:
                if directory in undead:
                    if(verbose): print('\033[90mundead     '+directory+' missing metadata file ('+tablehash+')')
                else:
                    if(verbose): print('\033[90mghost      ('+tablehash+') \033[9m'+directory+'\033[0m')
                    num_ghost += 1
                #if mode == 'add': ## Let's NOT do this. 
                #    database.updateRecord(cur,table['name'], None, tablehash, 'null')
    
        num_add += len(new)
        num_moved += len(moved)
        num_bad += len(bad) 
        num_undead += len(undead)   

        ret['new'] = new
        ret['moved'] = moved
        ret['bad'] = bad
        ret['undead'] = undead
        retlist.append(ret)

    if(verbose): print()
    if(verbose): print('\033[32mnew:          ',num_add,'\033[1;0m')
    if(verbose): print('\033[33mmove:         ',num_moved,'\033[1;0m')
    if(verbose): print('\033[31mbad:          ',num_bad,'\033[1;0m')
    if(verbose): print('\033[90mundead:       ',num_undead,'\033[1;0m')
    if(verbose): print('\033[90mghost:        ',num_ghost,'\033[1;0m')
    
    db.commit()
    db.close()

    return retlist
    


        
