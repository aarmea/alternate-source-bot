import os

PID = os.getpid()
def printWithPid(item):
    print(str(PID) + ": " + str(item))
