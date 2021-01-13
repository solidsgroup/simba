#!/usr/bin/env python3
import os
import glob
import fnmatch
import sqlite3
import argparse
import getpass
from functools import wraps
from flask import Flask, request, render_template, send_file, redirect, Response, url_for
from flaskext.markdown import Markdown
from flask_frozen import Freezer
import datetime
import webbrowser
from threading import Timer
import pathlib
import webbrowser
import socket

from simba import util
from simba import simba

simbaPath = util.getSimbaDir(pathlib.Path.cwd())
config    = util.getConfigFile(simbaPath)
scripts   = util.getScripts(config)

print("====================================")
print("SIMBA: SIMulation Browser Analysis")
print("====================================")

parser = argparse.ArgumentParser(description='Start a webserver to brows database entries')
parser.add_argument('mode')
parser.add_argument('-i','--ip', default='127.0.0.1', help='IP address of server (default: localhost)')
parser.add_argument('-p','--port', default='5000', help='Port (default: 5000)')
parser.add_argument('-d','--database',default=str(simbaPath/'results.db'),help='Name of database to read from')
parser.add_argument('-s','--safe',dest='safe',action='store_true',help='Safe mode - disallow permanent record deletion')
parser.add_argument('-f','--fast',dest='fast',action='store_true',help='Fast mode - fewer features for working with large datasets')
parser.add_argument('--pwd',default=False,action='store_true')
global args
args=parser.parse_args()

# Thread to open default browser and go to main page
def open_browser(url):
    import webbrowser
    webbrowser.open_new(url)

pwd = None
usr = None
if args.pwd:
    usr = getpass.getuser()
    pwd = getpass.getpass()

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == usr and password == pwd

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if (pwd and usr):
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
        return f(*args, **kwargs)
    return decorated    

def format_datetime(value, format='medium'):
    #t = parser.parse(value)
    #datetime.
    if not value: return value
    
    for fmt in ["%a %b%d %H:%M:%S %Y", "%a %b %d %H:%M:%S %Y"]:
        try:
            dt = datetime.datetime.strptime(str(value),fmt)
            return(dt.strftime("%Y-%m-%d %H:%M:%S (%a)"))
        except ValueError:
            pass
    print("Date parsing failed for string " + value + "")
    return value


if not args.safe and not args.ip == '127.0.0.1' or args.ip == 'localhost':
    print("=============  WARNING =============")
    print("It appears that you are starting    ")
    print("SIMBA on a public server NOT in SAFE")
    print("mode. This could allow malicious    ")
    print("users to alter your records. It is  ")
    print("strongly recommended that you run   ")
    print("with the --safe or -s flags enabled!")
    print("====================================")

script_directory = os.path.realpath(__file__)

app = Flask(__name__)
Markdown(app)

app.jinja_env.filters['datetime'] = format_datetime

@app.route("/", methods=['GET','POST'])
def root():
    #if request.method == 'POST':
    #    items = request.form.items()
    #    for f in items:
    #        print(f)    
    return table(None)

@app.route("/table/", methods=['GET','POST'])
def table_default():
    return table(None)
@app.route("/table/<table>", methods=['GET','POST'])
def table(table):
    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()

    print("HEY EVERYBODY")
    if request.method == 'POST':
        print("POSTING")
        if request.form.get('table-description') and not args.safe:
            print(request.form.get('table-description'))
            cur.execute("UPDATE __tables__ SET Description = ? WHERE NAME = ?;", (request.form.get('table-description'), table))
        elif request.form.get('action') == 'delete-table' and not args.safe:
            table_to_delete=request.form.get('table-name')
            cur.execute('DROP TABLE "{}";'.format(table_to_delete))
            cur.execute('DELETE FROM __tables__ WHERE NAME = "{}";'.format(table_to_delete))
            items = request.form.items()
            for f in items:
                print(f)
                if str(f[0]).startswith('hash_'):
                    hash = str(f[0]).replace('hash_','')
                    dir = str(f[1])
                    print("DELETING ",hash)
                    cur.execute("DELETE FROM " + table + " WHERE HASH = ?;",(hash,))
                    print("DELETING ",dir)
                    os.system('rm -rf ' + dir)

        #
        # DELETE MULITPLE RECORDS
        #
        elif request.form.get('action') == 'delete-records' and not args.safe:
            hashes = ' '.join([h.replace(' ','').replace('hash_','')
                               for h in request.form.get('delete-records-hashes').replace('  ',' ').split(' ')]).split()
            dirs = ' '.join([h.replace(' ','').replace('hash_','')
                               for h in request.form.get('delete-records-hashes').replace('  ',' ').split(' ')]).split()
            tags = request.form.get('apply-tags-tags')#.split(' ')
            for h, d in zip(hashes,dirs):
                print("Deleting record with hash = ", h)
                cur.execute('DELETE FROM "{}" WHERE HASH = ?'.format(table),(h,))
                print("Deleting directory ", d)
                os.system('rm -rf ' + d)

        #
        # APPLY TAGS
        #
        elif request.form.get('action') == 'apply-tags' and not args.safe:
            print("======================================")
            print("    APPLYING TAGS                     ")
            print("======================================")
            hashes = ' '.join([h.replace(' ','').replace('hash_','')
                               for h in request.form.get('apply-tags-hashes').replace('  ',' ').split(' ')]).split()
            tags = request.form.get('apply-tags-tags')#.split(' ')
            print("Applying tags",hashes)
            #print("Applying tags",tags)
            for h in hashes:
                cur.execute('UPDATE "{}" SET Tags = ? WHERE HASH = ?'.format(table),(tags,h))
            
        elif request.form.get('action') == 'append-tags' and not args.safe:
            print("======================================")
            print("    APPENDING TAGS                    ")
            print("======================================")
            hashes = ' '.join([h.replace(' ','').replace('hash_','')
                               for h in request.form.get('apply-tags-hashes').replace('  ',' ').split(' ')]).split()
            tags = request.form.get('apply-tags-tags')#.split(' ')
            for h in hashes:
                cur.execute('UPDATE "{}" SET Tags= CASE WHEN Tags IS NULL THEN ? ELSE Tags||","||? END WHERE HASH = ?'.format(table),(tags,tags,h))

        #
        # SHOULD NEVER GET TO THIS POINT
        #
        else:
            print("I'M POSTING BUT I DON'T KNOW WHAT TO POST")

    cur.execute("SELECT NAME, NumEntries FROM __tables__")
    tables = []
    counts = []
    for d in cur.fetchall():
        tables.append(d[0])
        counts.append(d[1])
    
    if not table: table_name = tables[0]
    else: table_name = table

    if request.method == 'POST':
        if request.form.get('action')=="delete-entry-only" and not args.safe:
            cur.execute("DELETE FROM " + table + " WHERE HASH = ?;",(request.form.get('entry-hash'),))
        if request.form.get('action')=='delete-everything' and not args.safe:
            cur.execute("SELECT DIR FROM " + table + " WHERE HASH = ?",(request.form.get('entry-hash'),))
            os.system('rm -rf ' + cur.fetchall()[0][0])
            cur.execute("DELETE FROM " + table + " WHERE HASH = ?;",(request.form.get('entry-hash'),))


    cur.execute("PRAGMA table_info("+table_name+")")
    columns=[a[1] for a in cur.fetchall()]

    cur.execute("SELECT * FROM " + table_name )
    rawdata = cur.fetchall()

    data = []
    for d in rawdata: data.append(dict(zip(columns,d)))

    cur.execute("SELECT Description FROM __tables__ WHERE Name = \"" + table_name  + "\"")
    desc = list(cur.fetchall()[0])[0]


    status = []
    if ("Status" in columns):
        status = [d["Status"] for d in data]

    db.commit()
    db.close()

    if table==None or table not in tables: table = tables[0]

    numfiles = []
    if not args.fast:
        for d in data:
            find_images(d['DIR'])
            numfiles.append(len(imgfiles))

    columns.insert(0,columns.pop(columns.index('DIR')))
    columns.insert(1,columns.pop(columns.index('Description')))
    columns.insert(1,columns.pop(columns.index('Tags')))
    columns.insert(1,"Thumbnail")

    thumbnails = find_thumbnails([str(simbaPath)+"/../"+d['DIR'] for d in data])
    return render_template('template.html', hostname=socket.gethostname(),
                            tables=tables,
                           counts=counts,
                            table_name=table,
                            table_description=desc,
                            data=data,
                            status=status,
                            numfiles=numfiles,
                            columns=columns,
                            thumbnails=thumbnails)
imgfiles = []
def find_images(path):
    print("Path is ",path)
    global imgfiles
    img_fmts = ['.jpg', '.jpeg', '.png', '.gif','.svg']
    imgfiles = []
    for fmt in img_fmts: imgfiles += glob.glob(path+'/*'+fmt)
    imgfiles.sort()

def find_thumbnails(paths):
    thumbnails = []
    for path in paths:
        img_fmts = ['.jpg', '.jpeg', '.png', '.gif','.svg']
        tmp_files = []
        for fmt in img_fmts: tmp_files += glob.glob(path+'/*'+fmt)
        if len(tmp_files) > 0: thumbnails.append(sorted(tmp_files)[0].replace("/",r"DIRDIR"))
        else: thumbnails.append("")
    return thumbnails

def find_tarballs(path):
    global tarballfiles
    img_fmts = ['.tar.gz']
    tarballfiles = []
    for fmt in img_fmts: tarballfiles += glob.glob(path+'/*'+fmt)
    tarballfiles.sort()

def find_thermo(path):
    global thermofile
    if os.path.isfile(path+'/thermo.dat'): thermofile = path+"/thermo.dat"
    else: thermofile = None

@app.route('/img/<number>')
#@requires_auth
def serve_image(number):
    global imgfiles
    return send_file(imgfiles[int(number)],cache_timeout=-1)

@app.route('/thumbnail/<number>')
#@requires_auth
def serve_thumbnail(number):
    #global thumbnails
    return send_file(number.replace(r"DIRDIR","/"),cache_timeout=-1)
    #return number;

@app.route('/metadata/')
#@requires_auth
def serve_metadata():
    global metadatafile
    response = send_file(metadatafile,cache_timeout=-1,as_attachment=True)
    response.headers["x-filename"] = "metadata"
    response.headers["Access-Control-Expose-Headers"] = 'x-filename'
    return response


@app.route('/thermo/')
#@requires_auth
def serve_thermo():
    global thermofile
    response = send_file(thermofile,cache_timeout=-1,as_attachment=True)
    response.headers["x-filename"] = "thermo.dat"
    response.headers["Access-Control-Expose-Headers"] = 'x-filename'
    return response

@app.route('/tarball/<filename>/<number>')
#@requires_auth
def serve_tarball(filename,number):
    print (filename)
    global tarballfiles
    response = send_file(tarballfiles[int(number)],cache_timeout=-1,as_attachment=True)
    response.headers["x-filename"] = filename
    response.headers["Access-Control-Expose-Headers"] = 'x-filename'
    return response

@app.route('/table/<table>/entry/<a_entry>', methods=['GET','POST'])
#@requires_auth
def table_entry(table,a_entry):
    entry = a_entry.replace(".html","")

    global imgfiles
    global metadatafile
    global thermofile

    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()

    if request.method == 'POST':
        if request.form.get('description'):
            cur.execute("UPDATE " + table + " SET Description = ? WHERE HASH = ?;",
                        (request.form.get('description'), entry));
        if request.form.get('tags'):
            cur.execute("UPDATE " + table + " SET Tags = ? WHERE HASH = ?;",
                        (request.form.get('tags'), entry));

    cur.execute("PRAGMA table_info("+table+")")
    columns=[a[1] for a in cur.fetchall()]

    cur.execute("SELECT * FROM " + table + " WHERE HASH='" + entry + "'")
    d = cur.fetchall()[0]

    data = dict(zip(columns,d))

    find_images(str(simbaPath)+"/../"+data['DIR'])
    #find_images(data['DIR'])
    find_tarballs(data['DIR'])
    metadatafile=data['DIR']+"/metadata"
    find_thermo(data['DIR'])

    db.commit()
    db.close()

    columns.insert(0,columns.pop(columns.index('DIR')))
    columns.insert(1,columns.pop(columns.index('Description')))
    columns.insert(1,columns.pop(columns.index('Tags')))

    return render_template('detail.html',hostname=socket.gethostname(),
                           table=table,
                           entry=entry,
                           columns=columns,
                           data=data,
                           thermofile=thermofile,
                           imgfiles=[os.path.split(im)[1] for im in imgfiles],
                           tarballfiles=[os.path.split(tb)[1] for tb in tarballfiles])

@app.route('/table/<table>/entry/<entry>/stdout.html', methods=['GET','POST'])
#@requires_auth
def table_entry_stdout(table,entry):
    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()
    cur.execute("SELECT STDOUT FROM {} WHERE HASH = ?".format(table),(entry,))
    return cur.fetchall()[0][0]

@app.route('/table/<table>/entry/<entry>/diff.html', methods=['GET','POST'])
#@requires_auth
def table_entry_diff(table,entry):
    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()
    cur.execute("SELECT DIFF FROM {} WHERE HASH = ?".format(table),(entry,))
    return cur.fetchall()[0][0]

@app.route('/table/<table>/entry/<entry>/diff.patch')
#@requires_auth
def table_entry_diff_patch(table,entry):
    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()
    cur.execute("SELECT DIFF_PATCH FROM {} WHERE HASH = ?".format(table),(entry,))
    return Response(cur.fetchall()[0][0],content_type='File')
    #return cur.fetchall()[0][0]

@app.route('/table/<table>/entry/<entry>/stderr.html', methods=['GET','POST'])
#@requires_auth
def table_entry_stderr(table,entry):
    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()
    cur.execute("SELECT STDERR FROM {} WHERE HASH = ?".format(table),(entry,))
    return cur.fetchall()[0][0]

@app.route('/regtest/<regtest>/testentry/<hash>/diff_stdout.html', methods=['GET','POST'])
#@requires_auth
def table_entry_diff_stdout(regtest,hash):
    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()
    cur.execute("SELECT diff_stdout FROM {} WHERE HASH = ?".format(regtest),(hash,))
    return cur.fetchall()[0][0]

@app.route('/regtest/<regtest>/<run>/stdout.html', methods=['GET','POST'])
#@requires_auth
def regtest_run_stdout(regtest,run):
    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()
    cur.execute("SELECT STDIO FROM regtest_runs WHERE RUN = ?",(run,))
    ret = cur.fetchall()
    if len(ret) > 0:
        if len(ret[0]) > 0:
            return ret[0][0]
    else: return "<h2>None</h2>"


@app.route("/regtest/<a_regtest>", methods=['GET','POST'])
#@requires_auth
def regtest(a_regtest):
    regtest = a_regtest.replace(".html","")

    db = sqlite3.connect(args.database)
    db.text_factory = str
    cur= db.cursor()

    if request.method == 'POST':
        print("GOT POST REQUEST")
        print(request.form.get('action'))
        if request.form.get('action')=="delete-regtests" and not args.safe:
            print("ATTEMPTING TO DELETE TABLES")
            items = request.form.items()
            for f in items:
                print(f)
                if str(f[0]).startswith('run_'):
                    run = str(f[0]).replace('run_','')
                    cur.execute("SELECT DIR FROM " + regtest + " WHERE RUN = ?;",(run,))
                    res = cur.fetchall()
                    if len(res)>0:
                        if len(res[0])>0:
                            dir = res[0][0]
                            print("Directory to delete is: ", dir)
                            os.system('rm -rf ' + dir)
                    cur.execute("DELETE FROM regtest_runs WHERE RUN = ?;",(run,))
                    cur.execute("DELETE FROM regtest WHERE RUN = ?;",(run,))
                    db.commit()

    cur.execute("SELECT DISTINCT TEST_NAME FROM {}".format(regtest))
    test_names = [tn[0] for tn in cur.fetchall()]

    cur.execute("SELECT RUN,COMPILECODE FROM regtest_runs ORDER BY RUN DESC".format(regtest))
    runs = cur.fetchall()#sorted([tn[0] for tn in cur.fetchall()],reverse=True)

    cur.execute("PRAGMA table_info({})".format(regtest))
    columns=[a[1] for a in cur.fetchall()]

    cur.execute("SELECT * FROM {}".format(regtest))
    rawdata = cur.fetchall()


    data = []
    for d in rawdata: data.append(dict(zip(columns,d)))

    return render_template('regtest.html',hostname=socket.gethostname(),
                            runs=runs,
                            tests=test_names,
                            data=data,
                            columns=columns)


#freezer = Freezer(app)
#
#@freezer.register_generator
#def regtest():
#    yield '/regtest/regtest.html'
#
#@freezer.register_generator
#def regtest_run_stdout():
#    db = sqlite3.connect(args.database)
#    db.text_factory = str
#    cur= db.cursor()
#    cur.execute("SELECT RUN,COMPILECODE FROM regtest_runs ORDER BY RUN DESC")
#    runs = [tn[0] for tn in cur.fetchall()]#sorted([tn[0] for tn in cur.fetchall()],reverse=True)
#    for run in runs:
#        #print('/regtest/regtest/{}/stdout.html'.format(run))
#        yield '/regtest/regtest/{}/stdout.html'.format(run)
#
#@freezer.register_generator
#def table_entry():
#    db = sqlite3.connect(args.database)
#    db.text_factory = str
#    cur= db.cursor()
#    cur.execute("SELECT TEST_NAME,HASH FROM regtest")
#    for test in cur.fetchall():
#        yield '/table/{}/entry/{}.html'.format(test[0],test[1])
#        yield '/table/{}/entry/{}/stdout.html'.format(test[0],test[1])
#        yield '/table/{}/entry/{}/stderr.html'.format(test[0],test[1])


#if __name__ == '__main__':
    #freezer.freeze()

#Timer(1, open_browser,args=('http://{}:{}/'.format(args.ip,args.port),)).start()        
app.run(debug=True,
            use_reloader=False,
            host=args.ip,
            port=int(args.port))
