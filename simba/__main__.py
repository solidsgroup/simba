print("Simba 2020.08.11.05")

import pathlib
import argparse
import configparser

import record
import web
import rt

parser = argparse.ArgumentParser()
parser.add_argument("mode",help="Select mode",choices=["record","web","rt"])
parser.add_argument("-v","--verbose",action="store_true",default="False")
args, unknown = parser.parse_known_args()

#
# Look recursively for a .simba directory in this or a parent path
#
def getSimbaDir(path):
    """
    Recursive function to find a .simba directory in this or a parent path
    """
    if (path/".simba").is_dir():
        return (path/".simba").absolute()
    else:
        if (path == path.parent):
            raise(Exception("No .simba directory found"))
        else:
            return(getSimbaDir(path.parent))
simbaPath = getSimbaDir(pathlib.Path.cwd())
print(simbaPath)

#
# Read in arguments from a config file
#
def getIncludedFiles(configfile):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(configfile.parent/configfile)
    ret = []
    if "include" in config.sections():
        for f in config["include"]:
            if (configfile.parent/f).is_file():
                ret += getIncludedFiles(configfile.parent/f)
            else: 
                raise(Exception("Could not find file {}".format(f)))
    ret += [configfile]
    return ret
config = configparser.ConfigParser(allow_no_value=True)
config.read(getIncludedFiles(simbaPath/"config"))
config.remove_section("include")

#
# Launch the program
#
if args.mode == "record":
    record.record(parser,config,simbaPath)
if args.mode == "web":
    web.web(parser,config,simbaPath)
if args.mode == "rt":
    rt.rt(parser,config,simbaPath)