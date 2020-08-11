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

def module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def record(parser,config,simbaPath):
    database = "results.db"

    parser = argparse.ArgumentParser(description='Sift through outputs')
    parser.add_argument('directories', nargs='*', help='List of directories containing ALAMO output')
    parser.add_argument('-d','--database', default='results.db', help='Name of database')
    parser.add_argument('-r','--remove', nargs='*', help='Tables to remove')
    parser.add_argument('-t','--table', default='simulation_data', help='Table name in database')
    args=parser.parse_args()



    if (simbaPath/"parseOutputDir.py").is_file:
        parseOutputDir = module_from_file("parseOutputDir",simbaPath/"parseOutputDir.py")

    tables = []
    if (simbaPath/"data.ini").is_file():
        config = configparser.ConfigParser()
        config.read(simbaPath/"data.ini")
        for sec in config.sections():
            print(sec)
            table = {"name":sec, "match":config[sec]["match"]}
            print(table)
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
            print(directory)
            if not os.path.isfile(directory+'/metadata'):
                continue            
            #data = simba.parse(directory)
            data = parseOutputDir.parse(directory)
            if data:
                types.update(simba.getTypes(data))
        

        #
        # Update/create the chosen table so all the values are represented
        #
        simba.updateTable(cur,args.table,types)

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
        for directory in directories:
            data = parseOutputDir.parse(directory)

            if not data:
                print(u'  \u251C\u2574\033[1;31mSkipping\033[1;0m:  ' + directory)
                continue
            
            data['DIR'] = os.path.abspath(directory)
            if not 'HASH' in data:
                raise Exception("parseOutputDir.parse MUST include a HASH in its output")

            simba.updateRecord(cur,args.table,data,data['HASH'])

        print(u'  \u2514\u2574' + 'Done')
    
    db.commit()
    db.close()
    