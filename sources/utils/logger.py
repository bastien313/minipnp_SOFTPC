import sys
from datetime import datetime


def _getStrTime():
    myDatetime = datetime.now()
    myStr = '<'
    myStr += myDatetime.strftime('%Y-%m-%d %H:%M:%S')
    myStr += '> '
    return myStr


class Logger:
    def __init__(self):
        self.ihmDirect = 0
        self.logFile = open("../log.txt", "w")

    def printDirectConsole(self, str):
        self.ihmDirect.insertToConsole(str)

    def printCerr(self, str):
        sys.stderr.write(_getStrTime() + str + '\n')

    def printCout(self, str):
        sys.stdout.write(_getStrTime() + str + '\n')
        self.printLogFile(str)

    def printLogFile(self, str):
        self.logFile.write(_getStrTime() + str + '\n')
        self.logFile.flush()
