import pathlib
import argparse
import configparser
import importlib

#import record
#import web
#import rt

#parser = argparse.ArgumentParser()
#parser.add_argument("mode",help="Select mode",choices=["status","add","web","rt"])
#parser.add_argument("-v","--verbose",action="store_true",default="False")
#args, unknown = parser.parse_known_args()

#
# Colors
#
#    reset = "\033[0m"
#    red   = "\033[31m"
#    green   = "\033[32m"
#    lightgray = "\033[37m"
#    boldgray = "\033[1m\033[37m"
#    boldgreen   = "\033[1m\033[32m"
#    boldyellow   = "\033[1m\033[33m"
#    boldred   = "\033[1m\033[31m"
#    bggray = "\033[47m\033[30m"
    
def bold(str):  return "\033[1m{}\033[0m".format(str)
def red(str):   return "\033[31m{}\033[0m".format(str)
def blue(str):   return "\033[34m{}\033[0m".format(str)
def green(str): return "\033[32m{}\033[0m".format(str)
def cyan(str): return "\033[36m{}\033[0m".format(str)
def yellow(str): return "\033[33m{}\033[0m".format(str)
def lightgray(str): return "\033[37m{}\033[0m".format(str)
def darkgray(str): return "\033[90m{}\033[0m".format(str)

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
            return None
        else:
            return(getSimbaDir(path.parent))

#
# Look recursively for a .git directory in this or a parent path
#
def getGitDir(path):
    """
    Recursive function to find a .git directory in this or a parent path
    """
    if (path.absolute()/".git").is_dir(): return (path.absolute()/".git")
    else:
        if (path.absolute() == path.absolute().parent): return None
        else: return(getGitDir(path.absolute().parent))


#
# Read in arguments from a config file
#
def getConfigFile(simbaPath):
    def getIncludedFiles(configfile):
        config = configparser.SafeConfigParser(allow_no_value=True)
        config.optionxform = str
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

    config = configparser.SafeConfigParser(allow_no_value=True)
    config.optionxform = str

    for f in getIncludedFiles(simbaPath/"config"):
        tmpconfig = configparser.SafeConfigParser(allow_no_value=True)
        tmpconfig.optionxform = str
        tmpconfig.read(f)
        for sec in tmpconfig:
            if len(tmpconfig[sec])==0: continue
            for s in tmpconfig[sec]:
                if not sec in config: config.add_section(sec)
                if tmpconfig[sec][s]: 
                    if ((f.parent/tmpconfig[sec][s]).is_file()):
                        config[sec][s] = str(f.parent/tmpconfig[sec][s])
                    else:
                        config[sec][s] = tmpconfig[sec][s]
                else: 
                    config[sec][s] = None
    config.remove_section("include")
    return config

#
# Read in user-defined path to a file
#
def getScripts(config):
    def module_from_file(module_name, file_path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    class scripts:
        parseOutputDir = module_from_file("parseOutputDir",config["scripts"]["parseOutputDir"]).parseOutputDir
        getHash        = module_from_file("getHash",       config["scripts"]["getHash"])       .getHash

    return scripts()

##
## Launch the program
##
#if args.mode == "add":
#    record.record(parser,config,simbaPath,scripts(),"add")
#if args.mode == "status":
#    record.record(parser,config,simbaPath,scripts(),"status")
#if args.mode == "web":
#    web.web(parser,config,simbaPath)
#if args.mode == "rt":
#    rt.rt(parser,config,simbaPath)

