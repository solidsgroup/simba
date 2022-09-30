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
parser.add_argument('-t','--tag', default=None, help='Table name in database')
parser.add_argument('-m','--match',nargs='*')
args=parser.parse_args()

db = sqlite3.connect(args.database if args.database.endswith('.db') else args.database+'.db')
db.text_factory = str
cur= db.cursor()

cur.execute('SELECT NAME,Description from "__tables__" WHERE NAME LIKE "{}"'.format(args.table if args.table else '%'))
entries = cur.fetchall()
#print(SingleTable([('Table','Description')]+entries).table)
tables = [e[0] for e in entries]

for table in tables:
    fs = []
    for f in args.filters:
        s = f.split('=')
        fs.append('"{}" LIKE "{}"'.format(s[0],s[1]))

    cols = [('HASH','DIR')]
    cur.execute('SELECT {} FROM "{}" {}'.format(','.join(cols[0]),table,"WHERE "+" AND ".join(fs) if fs else ""))
    entries = cur.fetchall()
    for entry in entries:
        hash = entry[0]
        path = simbaPath/".."/entry[1]
        for match in args.match:
            for rec in sorted(glob.glob(str(path/match))):
                print(hash, rec, os.path.getmtime(rec))


