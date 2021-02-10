#!/usr/bin/env python3
import os,sys
import argparse
#import sqlite3
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
    
if sys.argv[2] == "pull":
    print("Pulling")
    with open(simbaPath/"remote") as remotefile:
        stuff = remotefile.readlines()
        print(stuff)
        usr = stuff[0].replace('\n','')
        host = stuff[1].replace('\n','')
        path = stuff[2].replace('\n','')
        matches = stuff[3].replace('\n','').split(' ')
        localrootpath = stuff[4].replace('\n','')
    print(usr)
    print(host)
    print(path)
    print(matches)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print("HERE",host,usr)
        ssh.connect(host,username=usr)
    except paramiko.ssh_exception.SSHException as e:
        pwd = getpass.getpass(prompt='Password: ',stream=None)
        ssh.connect(host,username=usr,password=pwd)
    
    times = []
    files = []
    for match in matches:
        cmd = "cd " + path + r"; find . -maxdepth 3 -name " + match + r" -exec stat -c '%Y %n' {} \;"
        print(cmd)
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
        if ssh_stdout:
            for s in ssh_stdout.readlines():
                times.append(int(s.split(' ')[0]))
                files.append(s.split(' ')[1].replace('\n',''))
                #tocopy.append(s.replace('\n','').replace(path,'./'))
                #print(times[-1],files[-1])
            for s in ssh_stderr.readlines():
                sys.stderr.write(s)

    ftp_client = ssh.open_sftp()

    copied = 0
    uptodate = 0
    for t, f in zip(times,files):
        # directory location
        localpath = localrootpath + '/'.join(f.split('/')[:-1])
        remotepath = path+'/'+f
        os.makedirs(localpath,exist_ok=True)
        
        needsupdate = False
        if (not os.path.isfile(localrootpath+f)):
            needsupdate = True
        elif (int(os.stat(localrootpath+f).st_mtime) < t): 
            needsupdate = True
        else:
            needsupdate = False

#        print(localpath,remotepath)
        if needsupdate:
            print('\033[32mcopying       ',f,'\033[1;0m')
            res = ftp_client.get(remotepath,localrootpath+f)
            copied += 1
        else:
            print('\033[90mup-to-date    '+f+'\033[0m')
            uptodate += 1
    print()
    print('\033[32mcopied:       ',copied,'\033[1;0m')
    print('\033[90mup-to-date:   ',uptodate,'\033[1;0m')

    ftp_client.close()            

