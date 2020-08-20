
import os
import sys

def main():
    exepath = os.path.dirname(__file__)

    if len(sys.argv) < 2:
        print("You need to specify a mode")
        exit()

    print("Mode",sys.argv[1])
    print("Script:",exepath+"/simba-"+sys.argv[1]+".py")
    print("Args:",sys.argv[2:])
    print("Script:",exepath+"/simba-"+sys.argv[1]+".py "+" ".join(sys.argv[2:]))

    #os.system("python3 "+exepath+"/simba-"+sys.argv[1]+".py "+" ".join(sys.argv[2:]))
    if sys.argv[1] in ["add","status"]:
        os.system(sys.executable + " " + exepath + "/simba_add.py " + " ".join(sys.argv[1:]))
    if sys.argv[1] in ["web"]:
        os.system(sys.executable + " " + exepath + "/simba_web.py " + " ".join(sys.argv[1:]))


if __name__ == '__main__':
    main()

