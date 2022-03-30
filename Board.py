
import database as dtb
from Corrector import Corrector
from deprecated import deprecated



class component:
    def __init__(self,cmpConf):
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
        return "{} = X:{}, Y:{}, T:{}, Val:{}, Mod:{}\n".format(self.ref, self.posX, self.posY, self.rot, self.value, self.package)

    @deprecated
    def __assosciateCmpModel(self, model):
        """
        Asociate package with model
        :param model is modDatabase objetc:
        :return:
        """
        self.model = model.findModelWithAlias(self.package)

class Board:
    def __init__(self,name,logger):
        self.cmpDic = {}
        self.name = name
        self.path = "userdata/board/" +  self.name + ".pnpp"
        self.xSize = 100.0
        self.ySize = 80.0
        self.zSize = 1.6
        self.ref1 = "Null"
        self.ref2 = "Null"
        self.corr = Corrector()
        self.logger = logger
        self.filter = {'value':'', 'ref':'', 'package':'', 'model':'', 'placed':'', 'enable':''}

    def __str__(self):
        strOut = ""
        for cmp in self.cmpDic.values():
            strOut += cmp.__str__()
        return strOut


    def buildCorrector(self,ref1XY,ref2XY):
        """
        Buil all corector
        :param refXY, is the mesured position [X,Y]:
        :param posXY, is the CAD position [X,Y]: :
        :return 1 if ref is in cmpDict:
        """
        if self.ref1 in self.cmpDic and self.ref2 in self.cmpDic:
            pos1 = [self.cmpDic[self.ref1].posX, self.cmpDic[self.ref1].posY]
            pos2 = [self.cmpDic[self.ref2].posX, self.cmpDic[self.ref2].posY]
            self.corr.buildCorrector(ref1XY, ref2XY, pos1, pos2)
            return 1
        else:
            self.logger.printCout("Board::buildCorrector() ref is not in cmpDict")
            return 0

    @deprecated
    def __assosciateCmpModel(self,model):
        """
        Asociate package with model
        :param model is modDatabase objetc:
        :return:
        """
        for cmp in self.cmpDic.values():
            cmp.assosciateCmpModel(model)

    def getListOfValue(self):
        """Return a list of all value (100nF)"""
        valListOut = []
        for cmp in self.cmpDic.values():
            if cmp.value not in valListOut:
                valListOut.append(cmp.value)
        return valListOut

    def getCmpFromValue(self, strValue):
        """Return all component wich have selected value"""
        cmpListOut = []
        for cmp in self.cmpDic.values():
            if cmp.value == strValue:
                cmpListOut.append(cmp)
        return cmpListOut

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

        #skip first line.
        for x in range(startLine):
            line = openedFile.readline()

        loop = 1
        while loop:
            line = openedFile.readline()
            if(len(line)):
                paramList = line.split(separator)
                print(paramList)
                cmpParam = {}
                cmpParam['X'] = paramList[dicConf['X']]
                cmpParam['Y'] = paramList[dicConf['Y']]
                cmpParam['T'] = paramList[dicConf['T']]
                cmpParam['REF'] = paramList[dicConf['REF']].replace('\"','')
                cmpParam['VAL'] = paramList[dicConf['VAL']].replace('\"','')
                cmpParam['MOD'] = paramList[dicConf['MOD']].replace('\"','')

                self.cmpDic[cmpParam['REF'].replace('\"','')] = component(cmpParam)
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

    def _setxOffset(self, value):
        self.corr.xOffset = value

    def _setyOffset(self, value):
        self.corr.yOffset = value

    def _setangleCorr(self, value):
        self.corr.angleCorr = value

    def _getxOffset(self):
        return self.corr.xOffset

    def _getyOffset(self):
        return self.corr.yOffset

    def _getangleCorr(self):
        return self.corr.angleCorr

    xOffset = property(fset=_setxOffset, fget=_getxOffset)
    yOffset = property(fset=_setyOffset, fget=_getyOffset)
    angleCorr = property(fset=_setangleCorr, fget=_getangleCorr)