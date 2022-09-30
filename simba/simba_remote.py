#!/usr/bin/env python3
import os,sys
import argparse
import sqlite3
#import hashlib
#import os
#import re
import simba
#import configparser
#from glob import *
#from os.path import *
#import importlib.util
import pathlib
import getpass
import paramiko
import stat

#For deploy mode
#from . import util
#from . import simba
#For local mode
from simba import util
from simba import simba

simbaPath = util.getSimbaDir(pathlib.Path.cwd())
config    = util.getConfigFile(simbaPath)
scripts   = util.getScripts(config)

if (len(sys.argv) < 3):
    print("Need to specify a mode for remote")
    
if sys.argv[2] == "add":
    print("Add remote origin")
    parser = argparse.ArgumentParser(description='Sift through outputs')
    parser.add_argument('mode',nargs=2,help='Remote function')
    parser.add_argument('remote',help='SSH Remote Directory')
    parser.add_argument('--match',nargs='*',default='*')
    parser.add_argument('--localpath',default='./')
    parser.add_argument('--maxdepth',default=3)
    args=parser.parse_args()
    print(args.match)
    if len(args.remote.split('@')) == 1: 
        usr = getpass.getuser()
        rest = args.remote
    else:
        usr = args.remote.split('@')[0]
        rest = args.remote.split('@')[1]

    if len(rest.split(':')) == 1:
        host = rest
        path = '~'
    else:
        host, path = rest.split(':')

    print(usr)
    print(host)
    print(path)

    remotefile = open(simbaPath/"remote","w")
    remotefile.write(usr+'\n')
    remotefile.write(host+'\n')
    remotefile.write(path+'\n')
    remotefile.write(' '.join(args.match)+'\n')
    remotefile.write(args.localpath+'\n')
    remotefile.write(str(args.maxdepth)+'\n')
    
if sys.argv[2] == "pull":
    parser = argparse.ArgumentParser(description='Sift through outputs')
    parser.add_argument('mode',nargs=2,help='Remote function')
    parser.add_argument('filters',nargs='*',help='Filter remotes')
    parser.add_argument('-t','--table',default=None)
    args=parser.parse_args()

    print("Pulling")
    with open(simbaPath/"remote") as remotefile:
        stuff = remotefile.readlines()
        print(stuff)
        usr = stuff[0].replace('\n','')
        host = stuff[1].replace('\n','')
        remotePath = stuff[2].replace('\n','')
        matches = stuff[3].replace('\n','').split(' ')
        localrootpath = stuff[4].replace('\n','')
        maxdepth = stuff[5].replace('\n','')
    print(usr)
    print(host)
    print(remotePath)
    print(matches)

    #
    # Open the SSH connection using paramiko
    #
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("HERE",host,usr)
        ssh.connect(host,username=usr)
    except paramiko.ssh_exception.SSHException as e:
        pwd = getpass.getpass(prompt='Password: ',stream=None)
        ssh.connect(host,username=usr,password=pwd)
    
    #
    # Using the SSH connection, get the hash, name, and modification time for
    # all files on the remote server using the remote server's SimBA.
    # TODO: we need to check the remote simba version to make sure that we don't
    # get bizarre behavior due to the remote 'simba find' not working properly.
    #
    #times = []
    #files = []
    recs = []
    for match in matches:
        # note: it is necessary to do "bash --login -c" in order to source the user's local
        #       .bashrc file. Otherwise, you will not be able to find simba this way.
        if args.table:
            cmd = "cd " + str(remotePath) + r"; bash --login -c 'simba find {} --match {}'".format(args.table,match)
        else:
            cmd = "cd " + str(remotePath) + r"; bash --login -c 'simba find --match {}'".format(match)
            
        print(cmd)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd,get_pty=False)
        if ssh_stdout:
            for s in ssh_stdout.readlines():
                #time, f = s.split(' ')
                print(s)
                rec = dict()
                rec["hash"], rec["path"], rec["time"] = s.replace('\n','').split(' ')
                rec["time"] = float(rec["time"])
                doit = True
                if len(args.filters):
                    doit = False
                    for expression in args.filters:
                        if expression in rec["table"]:
                            doit = True
                            continue
                if doit:
                    recs.append(rec)
            for s in ssh_stderr.readlines():
                sys.stderr.write(s)


    #
    # Git dictionary mapping current hashes to current directories
    #
    hash_dir_map = dict()
    db = sqlite3.connect(str(simbaPath/'results.db'))
    db.text_factory = str
    cur= db.cursor()
    cur.execute('SELECT NAME,Description from "__tables__" WHERE NAME LIKE "{}"'.format(args.table if args.table else '%'))
    tables = [e[0] for e in cur.fetchall()]
    fs = []
    for f in args.filters:
        s = f.split('=')
        fs.append('"{}" LIKE "{}"'.format(s[0],s[1]))
    for table in tables:
        cols = [('HASH','DIR')]
        cur.execute('SELECT {} FROM "{}" {}'.format(','.join(cols[0]),table,"WHERE "+" AND ".join(fs) if fs else ""))
        entries = cur.fetchall()
        for entry in entries:
            hash = entry[0]
            path = simbaPath/".."/entry[1]
            hash_dir_map[hash] = path

    
    ftp_client = ssh.open_sftp()
    copied = 0
    uptodate = 0
    for rec in recs:
        remotepath = remotePath+"/"+rec['path']
        remoterelpath = rec['path']
        remotereldir  = os.path.dirname(rec['path'])

        if rec['hash'] in hash_dir_map.keys():
            localdir = hash_dir_map[rec['hash']]
            localreldir = os.path.relpath(localdir,simbaPath/"..")

            if (remotereldir != localreldir):
                print("The remote directory \n       ",localreldir,"\n"
                      "has been renamed to  \n       ",remotereldir)
                response = input("Do you want to rename your local copy? If you do not, nothing will be copied. (yN): ")
                if response in ['y','Y','yes','Yes','YES']:
                    print("Ok, doing it now.")
                    os.system("mv {} {}".format(localreldir,remotereldir))
                    localreldir = remotereldir
                    localdir    = str(simbaPath/".."/localreldir)
                    hash_dir_map[rec['hash']] = localdir
                else:
                    print("Skipping...")
                    continue
            localrelpath = str(localreldir+"/"+os.path.basename(rec['path']))
            localpath = str(str(localdir)+"/"+os.path.basename(rec['path']))
        else:
            localreldir = remotereldir
            localdir = os.path.abspath(simbaPath/".."/localreldir)
            localrelpath = remoterelpath
            localpath = os.path.abspath(simbaPath/".."/localrelpath)
            os.makedirs(localdir,exist_ok=True)

        needsupdate = False
        if (not os.path.isfile(localpath)):
            needsupdate = True
        elif (float(os.path.getmtime(localpath)) < float(rec['time'])): 
            needsupdate = True

        if needsupdate:
            print('\033[32mcopying       ',remotepath,"-->",localpath,'\033[1;0m')
            res = ftp_client.get(remotepath,localpath)
            copied += 1
        else:
            print('\033[90mup-to-date    '+remoterelpath+'\033[0m')
            uptodate += 1
    print()
    print('\033[32mcopied:       ',copied,'\033[1;0m')
    print('\033[90mup-to-date:   ',uptodate,'\033[1;0m')

    ftp_client.close()            

