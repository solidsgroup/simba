import pathlib
import argparse
import src.record

#
# Look recursively for a .simba directory in this or a parent path
#
def getSimbaDir(path):
    if (path/".simba").is_dir():
        return (path/".simba").absolute()
    else:
        if (path == path.parent):
            raise(Exception("No .simba directory found"))
        else:
            return(getSimbaDir(path.parent))
simbaPath = getSimbaDir(pathlib.Path.cwd())
print(simbaPath)

#parser = argparse.ArgumentParser()
#parser.add_argument("mode")
#args = parser.parse_args()


