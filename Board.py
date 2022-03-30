import math

import database as dtb
from Corrector import Corrector
from deprecated import deprecated


class component:
    def __init__(self, cmpConf):
        self.posX = float(cmpConf['X'])
        self.posY = float(cmpConf['Y'])
        self.rot = float(cmpConf['T'])
        self.ref = cmpConf['REF']
        self.value = cmpConf['VAL']
        self.package = cmpConf['MOD']
        self.model = "Null"
        self.feeder = "Null"
        self.isPlaced = 0
        self.isEnable = 1

    def __str__(self):
        return "{} = X:{}, Y:{}, T:{}, Val:{}, Mod:{}\n".format(self.ref, self.posX, self.posY, self.rot, self.value,
                                                                self.package)

    @deprecated
    def __assosciateCmpModel(self, model):
        """
        Asociate package with model
        :param model is modDatabase objetc:
        :return:
        """
        self.model = model.findModelWithAlias(self.package)


class Board:
    def __init__(self, name, logger):
        self.cmpDic = {}
        self.name = name
        self.path = "userdata/board/" + self.name + ".pnpp"
        self.xSize = 100.0
        self.ySize = 80.0
        self.zSize = 1.6
        self.ref1 = "Null"
        self.ref2 = "Null"
        self.ref1RealPos = {'X': 0, 'Y': 0}
        self.ref2RealPos = {'X': 0, 'Y': 0}
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
            if (len(line)):
                paramList = line.split(separator)
                print(paramList)
                cmpParam = {}
                cmpParam['X'] = paramList[dicConf['X']]
                cmpParam['Y'] = paramList[dicConf['Y']]
                cmpParam['T'] = paramList[dicConf['T']]
                cmpParam['REF'] = paramList[dicConf['REF']].replace('\"', '')
                cmpParam['VAL'] = paramList[dicConf['VAL']].replace('\"', '')
                cmpParam['MOD'] = paramList[dicConf['MOD']].replace('\"', '')

                self.cmpDic[cmpParam['REF'].replace('\"', '')] = component(cmpParam)
            else:
                loop = 0
        self.__importOffset()

    def __importOffset(self):
        """
        Function used After Import for replace all component in positive cordinate.
        Function try to place the farest negativ component to (0,0)
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
        """
        Return the machine coord position of component.
        :return:
        """
        theoreticalPosRef1 = {'X': self.cmpDic[self.ref1].posY, 'Y': self.cmpDic[self.ref1].posY}
        theoreticalPosRef2 = {'X': self.cmpDic[self.ref2].posX, 'Y': self.cmpDic[self.ref2].posY}
        realPosRef1 = self.ref1RealPos
        realPosRef2 = self.ref2RealPos

        # Recaled position of ref2 when ref1 = 0,0
        theoreticalPosRef2Recal = {'X': theoreticalPosRef2['X'] - theoreticalPosRef1['X'],
                                   'Y': theoreticalPosRef2['Y'] - theoreticalPosRef1['Y']}
        realPosRef2Recal = {'X': realPosRef2['X'] - realPosRef1['X'],
                            'Y': realPosRef2['Y'] - realPosRef1['Y']}

        theoreticalAngle = math.atan2(theoreticalPosRef2Recal['Y'], theoreticalPosRef2Recal['X'])
        realAngleLastPoint = math.atan2(realPosRef2Recal['Y'], realPosRef2Recal['X'])
        angleOffset = realAngleLastPoint - theoreticalAngle

        cmpPosTheoretical = {'X': self.cmpDic[ref], 'Y': self.cmpDic[ref]}
        cmpPosTheoreticalRecaled = {'X': cmpPosTheoretical['X'] - theoreticalPosRef1['X'],
                                    'Y': cmpPosTheoretical['Y'] - theoreticalPosRef1['Y']}

        cmpHypot = math.sqrt(cmpPosTheoreticalRecaled['X'] * cmpPosTheoreticalRecaled['X']
                             + cmpPosTheoreticalRecaled['Y'] * cmpPosTheoreticalRecaled['Y'])

        theoreticalAngleCmp = math.atan2(cmpPosTheoreticalRecaled['Y'] , cmpPosTheoreticalRecaled['X'])
        realAngleCmp = theoreticalAngleCmp + angleOffset

        # Compute corrected position
        correctedCmpPos = {'X': math.cos(realAngleCmp) * cmpHypot, 'Y': math.sin(realAngleCmp) * cmpHypot}
        #Recal to machine coord
        correctedCmpPos['X'] += realPosRef1['X']
        correctedCmpPos['Y'] += realPosRef1['Y']
        correctedCmpPos['C'] = self.cmpDic[ref].rot + math.degrees(angleOffset)

        return correctedCmpPos

    def __calcAngle(self):
        theoreticalPosRef1 = {'X': self.cmpDic[self.ref1].posY, 'Y': self.cmpDic[self.ref1].posY}
        theoreticalPosRef2 = {'X': self.cmpDic[self.ref2].posX, 'Y': self.cmpDic[self.ref2].posY}
        realPosRef1 = self.ref1RealPos
        realPosRef2 = self.ref2RealPos

        # Recaled position of ref2 when ref1 = 0,0
        theoreticalPosRef2Recal = {'X': theoreticalPosRef2['X'] - theoreticalPosRef1['X'],
                                   'Y': theoreticalPosRef2['Y'] - theoreticalPosRef1['Y']}
        realPosRef2Recal = {'X': realPosRef2['X'] - realPosRef1['X'],
                            'Y': realPosRef2['Y'] - realPosRef1['Y']}

        theoreticalAngle = math.atan2(theoreticalPosRef2Recal['Y'], theoreticalPosRef2Recal['X'])
        realAngleLastPoint = math.atan2(realPosRef2Recal['Y'], realPosRef2Recal['X'])
        angleOffset = realAngleLastPoint - theoreticalAngle
        return angleOffset

    def setRef1(self, ref, pos):
        self.ref1 = ref
        self.ref1RealPos = pos

    def setRef2(self, ref, pos):
        self.ref2 = ref
        self.ref2RealPos = pos

    def save(self):
        dtb.boardSave(self, self.path)

    def saveAs(self, path):
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

    angleCorr = property(fget=__calcAngle)