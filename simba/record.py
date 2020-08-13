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


def record(parser,config,simbaPath,scripts,mode="status"):
    database = "results.db"

    parser = argparse.ArgumentParser(description='Sift through outputs')
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
            if '-' in sec:
                raise Exception("Table name "+sec+" contains a hyphen; hyphens are not allowed.")
            table = {"name":sec, "match":config[sec]["match"]}
            tables.append(table)

    db = sqlite3.connect(args.database if args.database.endswith('.db') else args.database+'.db')
    db.text_factory = str
    cur= db.cursor()

    for table in tables:
        types = dict()
        directories = sorted(glob.glob(table["match"]))


        #
        # Scan metadata files to determine columns
        #
        for directory in directories:
            if not os.path.isfile(directory+'/metadata'):
                continue            
            data = scripts.parseOutputDir(directory)
            if data:
                types.update(simba.getTypes(data))
        

        #
        # Update/create the chosen table so all the values are represented
        #
        simba.updateTable(cur,table['name'],types,"results",False)
        entries = simba.getTableEntries(cur,table['name'])

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
            dirhash = scripts.getHash(directory)
            dirname = os.path.abspath(directory)
            data = scripts.parseOutputDir(directory)
            if not data:
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
                    print('\033[32madded        ',dirname,'\033[1;0m')
                    simba.updateRecord(cur,table['name'],data,dirhash,dirname,False)
                if status == "moved":
                    print('\033[33mmoved     ',moved[-1][0],'\033[1;0m')
                    print('\033[33m             ⮡',moved[-1][1],'\033[1;0m')
                    simba.updateRecord(cur,table['name'],data,dirhash,dirname,False)

        if mode == "status":
            if len(new)>0 or len(moved)>0 or len(bad)>0:
                for n in new:
                    print('\033[32mnew       ',n,'\033[1;0m')
                for m in moved:
                    print('\033[33mmoved     ',m[0],'\033[1;0m')
                    print('\033[33m             ⮡',m[1],'\033[1;0m')
                for b in bad:
                    print('\033[31mbad       ',b,'\033[1;0m')
            





    
    db.commit()
    db.close()
    