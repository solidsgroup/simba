#!/usr/bin/env python3
import argparse
import os
import re
import simba
import configparser
import glob
import importlib.util
import pathlib

from simba import util
from simba import simba

parser = argparse.ArgumentParser(description='Sift through outputs')
parser.add_argument('mode')
parser.add_argument('-i','--include', default=None, help='Path to include')
#parser.add_argument('-r','--remove', nargs='*', help='Tables to remove')
#parser.add_argument('-t','--table', default='simulation_data', help='Table name in database')
#parser.add_argument('-a','--all', action='store_true', default=False, help='Force update of ALL records')
args=parser.parse_args()

print("Hello!")

try:
    os.mkdir(".simba")
except FileExistsError:
    print("Note: .simba directory already exists")

if args.include:
    print("including!")
    configfile = open(".simba/config","w")
    if not os.path.isdir(args.include):
        raise(Exception(args.include + " is not a valid path"))
    if not os.path.isdir(args.include + "/.simba"):
        raise(Exception(args.include + " does not contain a .simba directory"))
    if not os.path.isfile(args.include + "/.simba/config"):
        raise(Exception(args.include + "/.simba/ does not contain config file"))

    configfile.write("[include]\n")
    configfile.write(str(pathlib.Path(args.include + "/.simba/config\n").absolute()))
else:
    if not os.path.isfile(".simba/config"):
        configfile = open(".simba/config","w")
        configfile.write("""
[scripts]
parseOutputDir=./parseOutputDir.py
getHash=./getHash.py
""")
        configfile.close()

    if not os.path.isfile(".simba/parseOutputDir.py"):
        podfile  = open(".simba/parseOutputDir.py","w")
        podfile.write("""
def parseOutputDir(self,directory):
    print("WARNING: This is the default parseOutputDir script!")
    print("         I cannot do anything!")
    return None
""")
        podfile.close()
    else:
        print("Note: parseOutputDir.py already in place")
    

        
    if not os.path.isfile(".simba/getHash.py"):
        ghfile = open(".simba/getHash.py","w")
        ghfile.write("""
def getHash(self,directory):
    print("WARNING: This is the default getHash script!")
    print("         I cannot do anything!")
""")
        ghfile.close()
    else:
        print("Note: getHash.py already in place")

                 
if not os.path.isfile(".simba/data.ini"):
    datafile = open(".simba/data.ini","w")
    datafile.write(
"""
##
## This is the data.ini file, where you tell SimBA how to
## locate important output directories and store them in a
## table.
##
## ======================
## Minimal example:
## ======================
##
## Suppose you have the following output directories
##
## ./test/output001
## ./test/output002
## ./test/output003
## 
## Instruct SimBA to find them by uncommenting the following:
## 
#[Tests]
#match = test/output*
##


## ======================
## Complex example
## ======================
##
## Suppose you have multiple types of outputs, e.g.
## ./test/Fracture/output001
## ./test/Fracture/output002
## ./test/Fracture/output003
## ./test/Microstructure/output001
## ./test/Microstructure/output002
## ./test/Microstructure/output003
##
## There are three options:
##
## (A) Explicit
#
#[Fracture]
#match = test/Fracture/output*
#[Microstructure]
#match = test/Microstructure/output*
#
## (B) Compact
#
#[Fracture Microstructure]
#match = test/$NAME/output*
#
## (C) Automatic with python
#
#[basename(res) for res in glob("tests/*")]
#match = test/$NAME/output*
#
""")
else:
    print("Note: data.ini already exists")


gitDir = util.getGitDir(pathlib.Path('.'))
if gitDir:
    print("Git directory root: " + str(gitDir.parent))
    configFile = open(gitDir/"config","a")
    configFile.write('\n\n')
    configFile.write('[diff "simba-diff"]\n')
    configFile.write('        name = simba diff\n')
    configFile.write('        tool = simba diff\n')
    configFile.write('        command = simba diff\n')
    configFile.write('\n')
    configFile.write('[mergetool "simba-merge"]\n')
    configFile.write('        name = simba merge\n')
    configFile.write('        command = simba merge\n')
    configFile.close()

    attributeFile = open(".simba/.gitattributes","a")
    attributeFile.write('\n*.db diff=simba-diff merge=simba-merge')
    attributeFile.close()