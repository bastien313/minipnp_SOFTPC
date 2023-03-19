
from ..utils import xmledit as xe
from .feeder import *
from .basePlate import *


class FeederNotFound(Exception):
    pass


class MotorConf:
    """
    Contain configuration information of motor
    axis: name of axis ex ('Y')
    step: step/mm (X,Y,Z) or step/° (C)
    speed: mm/min (X,Y,Z) or °/min  (C)
    accel: mm/s²  (X,Y,Z) or °/s²   (C)
    """

    def __init__(self, axis, step, speed, accel):
        self.axis = axis
        self.step = float(step)
        self.speed = float(speed)
        self.accel = float(accel)

    def __repr__(self):
        return '{}: step = {}, speed = {}, accel = {}'.format(self.axis, self.step, self.speed, self.accel)

    def saveInLxml(self, rootLxml):
        """
        Put data in lxlm object.
        :param rootLxml:
        :return:
        """
        axisRoot = etree.SubElement(rootLxml, self.axis)
        etree.SubElement(axisRoot, 'step').text = str(self.step)
        etree.SubElement(axisRoot, 'speed').text = str(self.speed)
        etree.SubElement(axisRoot, 'accel').text = str(self.accel)


class MachineConf:
    """
    Contain all information of the machine.
    Motor parameters.
    Feeder list and parameters.
    ...
    """

    def __init__(self, pathFile, logger, driver):
        self.axisConfArray = {'X': MotorConf('X', 1.0, 1.0, 1.0),
                              'Y': MotorConf('Y', 1.0, 1.0, 1.0),
                              'Z': MotorConf('Z', 1.0, 1.0, 1.0),
                              'C': MotorConf('C', 1.0, 1.0, 1.0)}
        self.scanPosition = {'X': 1.0, 'Y': 1.0, 'Z': 1.0}
        self.boardRefPosition = {'X': 1.0, 'Y': 1.0, 'Z': 1.0}
        self.trashPosition = {'X': 1.0, 'Y': 1.0, 'Z': 1.0}
        self.zHead = 1.0
        self.zLift = 10.0
        self.pathFile = pathFile
        self.feederList = []
        self.basePlateList = []
        self.logger = logger
        self._driver = driver

        self.__loadFromXml(self.pathFile)

    def __str__(self):
        strOut = 'Machine: ScanX = {}, ScanY = {}, scanZ = {}, zhead = {}'.format(self.scanPosition['X'],
                                                                                  self.scanPosition['Y'],
                                                                                  self.scanPosition['Z'], self.zHead)
        strOut += '\n'
        for axis in self.axisConfArray.values():
            strOut += repr(axis)
            strOut += '\n'
        for feeder in self.feederList:
            strOut += repr(feeder)
            strOut += '\n'

        return strOut

    def setAxisAccel(self, accelData):
        """
        Set acceleration
        :param accelData: dict which contain accel for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is accelValue
        :return:
        """
        for axis, data in accelData.items():
            self.axisConfArray[axis].accel = data

    def getAxisAccel(self):
        """
        Get acceleration
        :return: :dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        accelOut = {}
        for axis in self.axisConfArray.values():
            accelOut[axis.axis] = axis.accel

    def setAxisStep(self, stepData):
        """
        Set step of axis
        :param stepData: dict which contain step value for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is accelValue
        :return:
        """
        for axis, data in stepData.items():
            self.axisConfArray[axis].step = data

    def getAxisStep(self):
        """
        Get step
        :return: :dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        stepOut = {}
        for axis in self.axisConfArray.values():
            stepOut[axis.axis] = axis.step

    def setAxisSpeed(self, speedData):
        """
        Set maximum speed of axis
        :param speedData: dict which contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is accelValue
        :return:
        """
        for axis, data in speedData.values():
            self.axisConfArray[axis].speed = data

    def getAxisSpeed(self):
        """
        Get max speed
        :return: :dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        speedOut = {}
        for axis in self.axisConfArray.values():
            speedOut[axis.axis] = axis.speed

    def saveToXml(self):
        root = etree.Element("root")

        # Write machine parameters
        machineRoot = etree.SubElement(root, 'machine')
        etree.SubElement(machineRoot, 'zHead').text = str(self.zHead)
        etree.SubElement(machineRoot, 'zLift').text = str(self.zLift)

        # Write scan position
        xe.addPosToXml(machineRoot, 'scan_position', self.scanPosition['X'], self.scanPosition['Y'],
                       self.scanPosition['Z'])

        xe.addPosToXml(machineRoot, 'boardRef_position', self.boardRefPosition['X'], self.boardRefPosition['Y'],
                       self.boardRefPosition['Z'])

        xe.addPosToXml(machineRoot, 'trash_position', self.trashPosition['X'], self.trashPosition['Y'],
                       self.trashPosition['Z'])

        # Write axis parameters
        axisRoot = etree.SubElement(machineRoot, 'axis')
        for param in self.axisConfArray.values():
            param.saveInLxml(axisRoot)

        # Write feeder parameters
        feederRoot = etree.SubElement(machineRoot, 'feeder')
        for feeder in self.feederList:
            feeder.saveInLxml(feederRoot)

        basePlateRoot = etree.SubElement(machineRoot, 'basePlate')
        for bp in self.basePlateList:
            bp.saveInLxml(basePlateRoot)

        with open(self.pathFile, 'wb') as fileOut:
            fileOut.write(etree.tostring(root, pretty_print=True))

    def __feederLoadFromXml(self, idFeeder, feederRoot):
        """
        Load one feeder from xml file.
        Create selected object and insert in self.feederList.
        :param idFeeder: id of feeder
        :param feederRoot:
        :return: none
        """
        feederData = {'basePlateId': '0'}
        # load default base plate id for compatibility with old feeder.
        # import dara from xml
        for element in feederRoot:
            feederData[element.tag] = element.text

        if 'basePlate_0' in feederData:
            bpObject = self.__basePlateLoadFromXml(idBp=0, bpRoot=feederRoot.find('basePlate_0'),
                                                   addTobasePlateList=False)
            feederData['localBasePlate'] = bpObject
        # else:
        #    del feederData['basePlate_0']

        feederData['id'] = int(idFeeder)
        # create feeder
        if feederData['type'] == 'feeder':
            self.addFeeder(Feeder(paramList=feederData, machine=self))
        elif feederData['type'] == 'reelfeeder':
            self.addFeeder(ReelFeeder(paramList=feederData, machine=self))
        elif feederData['type'] == 'stripfeeder':
            self.addFeeder(StripFeeder(paramList=feederData, machine=self))
        elif feederData['type'] == 'mechanicalfeeder':
            self.addFeeder(MechanicalFeeder(paramList=feederData, machine=self, driver=self._driver))
        elif feederData['type'] == 'compositefeeder':
            feederData['feederList'] = self.makeFilteredFeederList(feederData['feederListStr'])
            self.addFeeder(CompositeFeeder(paramList=feederData, machine=self))

    def __basePlateLoadFromXml(self, idBp, bpRoot, addTobasePlateList=True):
        """
        Load one basePlate from xml file.
        Create selected object and insert in self.basePlateList.
        :param idBp: id of basePlate
        :param bpRoot:
        :return: basePlate object
        """
        basePlateData = {}
        # import dara from xml
        for element in bpRoot:
            basePlateData[element.tag] = element.text

        basePlateData['id'] = int(idBp)
        # create feeder
        bpObject = None
        if basePlateData['type'] == 'BasePlate':
            bpObject = BasePlate(basePlateData)
        elif basePlateData['type'] == 'StripFeederBasePlate':
            bpObject = BasePlateForStripFeeder(basePlateData)

        if addTobasePlateList:
            self.addBasePlate(bpObject)

        return bpObject

    def __axisLoadFromXml(self, axis, axisRoot):
        """
        Load one axis conf from xml file.
        Create selected object and insert in self.motorConfArray.
        :param axis: string of axis (ex: 'X')
        :param axisRoot: root xml of axis
        :return: none
        """
        feederData = {}
        # import dara from xml
        for element in axisRoot:
            feederData[element.tag] = element.text
        # Create object
        self.axisConfArray[axis] = MotorConf(axis, feederData['step'], feederData['speed'], feederData['accel'])

    def loadFromXml(self, pathFile):
        try:
            self.__loadFromXml(pathFile)
            self.pathFile = pathFile
        except:
            self.logger.printCout(f"Loading machine conf '{pathFile}' error!")
            self.__loadFromXml(self.pathFile)

    def __loadFromXml(self, pathFile):
        """
        Load data from xml file pointed by self.pathFile
        :return:
        """
        # reset feederList
        self.feederList = []
        # try:
        root = etree.parse(pathFile).getroot()
        # except:
        #    self.logger.printCout("Error file don't exist: Make new model file")
        #    self.saveToXml()
        # self.__makeNewFile()
        # else:
        self.logger.printCout(f"Load machine configuration '{pathFile}'")
        machineRoot = root.find('machine')
        self.zHead = float(xe.getXmlValue(machineRoot, 'zHead', 0.0))
        self.zLift = float(xe.getXmlValue(machineRoot, 'zLift', 10.0))
        self.scanPosition = xe.getPosFromXml(machineRoot.find('scan_position'))
        self.boardRefPosition = xe.getPosFromXml(machineRoot.find('boardRef_position'))
        self.trashPosition = xe.getPosFromXml(machineRoot.find('trash_position'))

        axisRoot = machineRoot.find('axis')
        for axis in axisRoot:
            self.__axisLoadFromXml(axis.tag, axisRoot.find(axis.tag))

        basePlateRoot = machineRoot.find('basePlate')
        if len(basePlateRoot):
            for basePlate in basePlateRoot:
                self.__basePlateLoadFromXml(basePlate.tag.split('_')[1], basePlateRoot.find(basePlate.tag))

        feederRoot = machineRoot.find('feeder')
        for feeder in feederRoot:
            self.__feederLoadFromXml(feeder.tag.split('_')[1], feederRoot.find(feeder.tag))

    def __makeNewFile(self):
        """
        Make a new XML file which is void.
        :return:
        """
        fileOut = open(self.pathFile, 'wb')
        root = etree.Element("root")
        fileOut.write(etree.tostring(root, pretty_print=True))
        fileOut.close()

    def deleteFeeder(self, feederId):
        idFound = 'None'
        for feederPos in range(len(self.feederList)):
            if self.feederList[feederPos].id == feederId:
                idFound = feederPos
        if type(idFound) is int:
            del self.feederList[idFound]

    def deleteBasePlate(self, feederId):
        idFound = 'None'
        for bpPos in range(len(self.basePlateList)):
            if self.basePlateList[bpPos].id == feederId:
                idFound = bpPos
        if type(idFound) is int:
            del self.basePlateList[idFound]

    def addFeeder(self, newFeeder):
        """
        Add feeder to machine , self.feederList.
        If id exist feeder will be replaced.
        :param newFeeder: feeder object
        :return: 1 if feeder was overwriten else 0
        """
        for feederPos in range(len(self.feederList)):
            if self.feederList[feederPos].id == newFeeder.id:
                self.feederList[feederPos] = newFeeder
                return 1
        self.feederList.append(newFeeder)

    def addBasePlate(self, newBasePlate):
        """
        Add BasePlate to machine , self.basePlateList.
        If id exist BasePlate will be replaced.
        :param newBasePlate: BasePlate object
        :return: 1 if BasePlate was overwriten else 0
        """
        for bpPos in range(len(self.basePlateList)):
            if self.basePlateList[bpPos].id == newBasePlate.id:
                self.basePlateList[bpPos] = newBasePlate
                return 1
        self.basePlateList.append(newBasePlate)

    def getFeederById(self, idFeeder):
        for feeder in self.feederList:
            if feeder.id == idFeeder:
                return feeder
        self.logger.printCout('Mconf: feeder {} not found'.format(idFeeder))

    def getBasePlateById(self, idBp):
        for basePlate in self.basePlateList:
            if basePlate.id == idBp:
                return basePlate
        self.logger.printCout('Mconf: basePlate {} not found'.format(idBp))

    def makeFilteredFeederList(self, strFilt):
        """
        Return a feder list of feeder contained in strFilt ex: '1|3|5'
        :param strFilt:
        :return:
        """
        strSplit = strFilt.split('|')
        feederListOut = []
        for idFeed in strSplit:
            feeder = self.getFeederById(int(idFeed))
            if feeder:
                feederListOut.append(feeder)
            else:
                self.logger.printCout('Filtered list feeder not found {}'.format(idFeed))
        return feederListOut
