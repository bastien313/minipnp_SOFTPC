import math
import os.path

from . import database as dtb
from deprecated import deprecated
import copy
from utils import misc
from machine.basePlate import BasePlate


class Component:
    def __init__(self, cmpConf):
        self.posX = float(cmpConf['posX']) if 'posX' in cmpConf else 0.0
        self.posY = float(cmpConf['posY']) if 'posY' in cmpConf else 0.0
        self.rot = float(cmpConf['angle']) if 'angle' in cmpConf else 0.0
        self.ref = cmpConf['ref'] if 'ref' in cmpConf else 'noname'
        self.originalRef = cmpConf['originalRef'] if 'originalRef' in cmpConf else cmpConf[
            'ref'] if 'ref' in cmpConf else 'noname'
        self.value = cmpConf['value'] if 'value' in cmpConf else ''
        self.package = cmpConf['package'] if 'package' in cmpConf else ''
        self.model = cmpConf['model'] if 'model' in cmpConf else 'Null'
        self.feeder = cmpConf['feeder'] if 'feeder' in cmpConf else ''
        self.isPlaced = int(cmpConf['placed']) if 'placed' in cmpConf else 0
        self.isEnable = int(cmpConf['enable']) if 'enable' in cmpConf else 0
        self.isOriginal = int(cmpConf['original']) if 'original' in cmpConf else 1

        self.rot = misc.normalizeAngle(self.rot)

    def __str__(self):
        return "{} = X:{}, Y:{}, T:{}, Val:{}, Mod:{}\n".format(self.ref, self.posX, self.posY, self.rot, self.value,
                                                                self.package)

    @deprecated
    def __associateCmpModel(self, model):
        """
        Asociate package with model
        :param model is modDatabase object:
        :return:
        """
        self.model = model.findModelWithAlias(self.package)


class Board:
    def __init__(self, path, logger):
        self.cmpDic = {}
        #self.name = name
        self.path = path
        self.tableTopPath = ''
        self.xSize = 100.0
        self.ySize = 80.0
        self.zSize = 1.6
        self.localBasePlate = BasePlate({})

        self.ref1 = "Null"
        self.ref2 = "Null"
        # self.ref1RealPos = {'X': 0, 'Y': 0}
        # self.ref2RealPos = {'X': 0, 'Y': 0}
        self.logger = logger
        self.filter = {'value': '', 'ref': '', 'package': '', 'model': '', 'placed': '', 'enable': ''}

    def __str__(self):
        strOut = ""
        for cmp in self.cmpDic.values():
            strOut += cmp.__str__()
        return strOut

    def importFromCSV(self, openedFile, separator, startLine, dicConf):
        """
        Delete all component and Import all component from csv
        :param openedFile is the csvFile opened:
        :param seperator is the separator of each value:
        :param startLine is the first line wich contain data:
        :param dicConf how data is writen ex ({'X': 1, 'Y':2, 'T':3, 'REF': 0, 'VAL':4, 'MOD':5})
        :return:
        """
        self.cmpDic = {}

        # skip first line.
        for x in range(startLine):
            line = openedFile.readline()

        loop = 1
        while loop:
            line = openedFile.readline()
            if len(line):
                paramList = line.split(separator)
                print(paramList)
                cmpParam = {}
                cmpParam['posX'] = paramList[dicConf['X']]
                cmpParam['posY'] = paramList[dicConf['Y']]
                cmpParam['angle'] = paramList[dicConf['T']]
                cmpParam['originalRef'] = paramList[dicConf['REF']].replace('\"', '')
                cmpParam['ref'] = cmpParam['originalRef']
                cmpParam['value'] = paramList[dicConf['VAL']].replace('\"', '')
                cmpParam['package'] = paramList[dicConf['MOD']].replace('\"', '')

                self.cmpDic[cmpParam['originalRef'].replace('\"', '')] = Component(cmpParam)
            else:
                loop = 0
        self.__importOffset()

    def __importOffset(self):
        """
        Function used After Import for replace all component in positive cordinate.
        Function try to place the furthest negative component to (0,0)
        :return:
        """
        xMin = self.cmpDic[self.cmpDic.__iter__().__next__()].posX
        yMin = self.cmpDic[self.cmpDic.__iter__().__next__()].posY
        for cmp in self.cmpDic.values():
            if cmp.posX < xMin:
                xMin = cmp.posX
            if cmp.posY < yMin:
                yMin = cmp.posY

        for cmp in self.cmpDic.values():
            cmp.posX += xMin * -1.0
            cmp.posY += yMin * -1.0

    def getMachineCmpPos(self, ref):
        realRef1Pos = self.localBasePlate.getRealRef(0)
        theoreticalMachineCompPos = {
            'X': (self.cmpDic[ref].posX - self.cmpDic[self.ref1].posX) + realRef1Pos['X'],
            'Y': (self.cmpDic[ref].posY - self.cmpDic[self.ref1].posY) + realRef1Pos['Y'],
            'Z': realRef1Pos['Z'],
        }
        realPos = self.localBasePlate.getPointCorrected(theoreticalMachineCompPos)
        realPos['C'] = self.cmpDic[ref].rot + math.degrees(self.localBasePlate.getRotationOffset())
        realPos['C'] = misc.normalizeAngle(realPos['C'])
        return realPos

    def __calcAngle(self):
        """
        Return angle correction in degree.
        """
        return math.degrees(self.localBasePlate.getRotationOffset())

    def save(self):
        dtb.boardSave(self, self.path)

    def saveAs(self, path):
        if not '.pnpp' in path:
            path += '.pnpp'
       # self.name = os.path.basename(path)
        #self.name = os.path.splitext(self.name)[0]
        self.path = path
        self.save()

    def __getitem__(self, index):
        """Cette méthode spéciale est appelée quand on fait objet[index]
        Elle redirige vers self._dictionnaire[index]"""

        return self.cmpDic[index]

    def __setitem__(self, index, valeur):
        """Cette méthode est appelée quand on écrit objet[index] = valeur
        On redirige vers self._dictionnaire[index] = valeur"""

        self.cmpDic[index] = valeur

    def __len__(self):
        return len(self.cmpDic)

    def __iter__(self):
        return self.cmpDic.__iter__()

    def __next__(self):
        return self.cmpDic.__next__()

    def values(self):
        return self.cmpDic.values()

    def horizontalMirror(self):
        """
        Apply an horizontal mirror of entire board
        """
        for cmp in self.cmpDic.values():
            cmp.posY = 0.0 - cmp.posY
            cmp.rot += 180.0
            cmp.rot = misc.normalizeAngle(cmp.rot)
        self.__importOffset()
        self.logger.printCout('Horizontal mirror done.')

    def verticalMirror(self):
        """
        Apply an vertical mirror of entire board
        """
        for cmp in self.cmpDic.values():
            cmp.posX = 0.0 - cmp.posX
            cmp.rot += 180.0
            cmp.rot = misc.normalizeAngle(cmp.rot)
        self.__importOffset()
        self.logger.printCout('Vertical mirror done.')

    def boardRotation(self, angleInDeg):
        """
        Apply a rotation of entire board.
        """
        angleRad = math.radians(angleInDeg)
        for cmp in self.cmpDic.values():
            oldX = cmp.posX
            oldY = cmp.posY
            cmp.posX = oldX * math.cos(angleRad) + oldY * math.sin(angleRad)
            cmp.posY = oldY * math.cos(angleRad) - oldX * math.sin(angleRad)
            cmp.rot += angleInDeg
            cmp.rot = misc.normalizeAngle(cmp.rot)
        self.logger.printCout('Rotation done.')

    def panelize(self, countX, countY, offsetX, offsetY):
        """
        Modifi component list to take care of needed copy for panelization.
        """
        countX = 1 if countX < 1 else countX
        countY = 1 if countY < 1 else countY
        cmpOriginalDict = {}
        for ref, cmp in self.cmpDic.items():
            if cmp.isOriginal:
                cmpOriginalDict[ref] = cmp

        self.cmpDic = {}
        for cmp in cmpOriginalDict.values():
            for x in range(countX):
                for y in range(countY):
                    newCmp = copy.deepcopy(cmp)
                    newCmp.posX += x * offsetX
                    newCmp.posY += y * offsetY
                    newCmp.isOriginal = 1 if x == 0 and y == 0 else 0
                    ref = f'{newCmp.originalRef}_{x}{y}' if countX > 1 or countY > 1 else newCmp.originalRef
                    newCmp.ref = ref
                    self.cmpDic[ref] = newCmp
        self.logger.printCout('Panelize done.')

    angleCorr = property(fget=__calcAngle)
