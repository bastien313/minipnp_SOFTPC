import math
import deprecated
from lxml import etree
import xmledit as xe
import logger as lg
import Corrector as cr

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


class Feeder:
    def __init__(self, paramList, saveMachineFunction):
        self.type = 'feeder'
        self.id = int(paramList['id']) if 'id' in paramList else 0
        self.name = paramList['name'] if 'name' in paramList else 'noname'
        self.pos = {'X': float(paramList['xPos']) if 'xPos' in paramList else 1.0,
                    'Y': float(paramList['yPos']) if 'yPos' in paramList else 1.0,
                    'Z': float(paramList['zPos']) if 'zPos' in paramList else 1.0}
        self._haveComponent = True
        self.saveMachineFunction = saveMachineFunction

    def setPosition(self, positionDict):
        """
        Set the first pickup position.
        :param positionDict: Dictionary contain position {'X': posx, 'Y': posy, 'Z':posz}
        :return:
        """
        self.pos = positionDict

    def prepareNextComponent(self):
        return

    def nextComponentIsReady(self):
        return 1

    def haveComponent(self):
        return self._haveComponent

    def reload(self):
        self._haveComponent = True

    def getComponentPosition(self):
        """
        Get the position of the next component to be picked up.
        :return: position of component {'X': posx, 'Y': posy, 'Z':posz, 'C': theta correction}
        """
        return self.pos

    def saveInLxml(self, rootLxml):
        """
        Save feeder parameter in xml.
        :param rootLxml:
        :return: return the created root for inherited class.
        """
        feederRoot = etree.SubElement(rootLxml, 'feeder_' + str(self.id))
        etree.SubElement(feederRoot, 'name').text = self.name
        etree.SubElement(feederRoot, 'type').text = self.type
        etree.SubElement(feederRoot, 'xPos').text = str(self.pos['X'])
        etree.SubElement(feederRoot, 'yPos').text = str(self.pos['Y'])
        etree.SubElement(feederRoot, 'zPos').text = str(self.pos['Z'])
        return feederRoot

class CompositeFeeder(Feeder):
    def __init__(self, paramList, saveMachineFunction):
        Feeder.__init__(self, paramList, saveMachineFunction)
        self.type = 'compositefeeder'
        self.feederList = paramList['feederList'] if 'feederList' in paramList else []
        self._precedentFeederPickup = 0 # last feeder which user request position.

    def saveInLxml(self, rootLxml):
        feederRoot = Feeder.saveInLxml(self, rootLxml)
        etree.SubElement(feederRoot, 'feederListStr').text = self.feederListToStr()
        return feederRoot

    def getPositionById(self, cmpId, feederId):
        if feederId < len(self.feederList):
            return self.feederList[feederId].getPositionById(cmpId)
        raise FeederNotFound

    def getComponentPosition(self):
        """
        Get the position of the next component to be picked up.
        :return: position of component {'X': posx, 'Y': posy, 'Z':posz, 'C': theta correction}
        """
        for idFeeder in range(len(self.feederList)):
            if self.feederList[idFeeder].haveComponent():
                self._precedentFeederPickup = self.feederList[idFeeder]
                return self.feederList[idFeeder].getComponentPosition()
        raise FeederNotFound

    def haveComponent(self):
        for feeder in self.feederList:
            if feeder.haveComponent():
                return True
        return False

    def prepareNextComponent(self):
        """
        Remove one component from feeder.
        Call this when the machine pickup the component.
        :return: 0 if more component are présent, otherwise return 1
        """
        if self.haveComponent():
            self._precedentFeederPickup.prepareNextComponent()
            return 0 if self.haveComponent() else 1
        return 1

    def feederListToStr(self):
        feederListStr = ''
        for feeder in self.feederList:
            feederListStr += '{}|'.format(feeder.id)
        return feederListStr[:-1]


class StripFeeder(Feeder):
    def __init__(self, paramList, saveMachineFunction):
        Feeder.__init__(self, paramList, saveMachineFunction)
        self.type = 'stripfeeder'
        self.componentPerStrip = int(paramList['componentPerStrip']) if 'componentPerStrip' in paramList else 1
        self.endPos = {'X': float(paramList['xEndPos']) if 'xEndPos' in paramList else 1.0,
                       'Y': float(paramList['yEndPos']) if 'yEndPos' in paramList else 1.0}

        # Adress of next component to be picked up
        self.nextComponent = int(paramList['idAddress']) if 'idAddress' in paramList else 0

    def saveInLxml(self, rootLxml):
        feederRoot = Feeder.saveInLxml(self, rootLxml)
        etree.SubElement(feederRoot, 'componentPerStrip').text = str(self.componentPerStrip)
        etree.SubElement(feederRoot, 'nextComponent').text = str(self.nextComponent)
        etree.SubElement(feederRoot, 'xEndPos').text = str(self.endPos['X'])
        etree.SubElement(feederRoot, 'yEndPos').text = str(self.endPos['Y'])
        etree.SubElement(feederRoot, 'yEndPos').text = str(self.endPos['Y'])




    def __getCorrectedPositionLinear(self, cmpId):
        xRamp = (self.endPos['X'] - self.pos['X']) / (self.componentPerStrip-1)
        yRamp = (self.endPos['Y'] - self.pos['Y']) / (self.componentPerStrip-1)

        correctedCmpPos = {}
        correctedCmpPos['X'] = self.pos['X'] + cmpId * xRamp
        correctedCmpPos['Y'] = self.pos['Y'] + cmpId * yRamp


        theoreticalPosLastPoint = {'X':self.stripStep * float(self.stripAmount - 1),
                                   'Y':self.cmpStep * float(self.componentPerStrip - 1)}  # Ramene la referance a 0
        realPosLastPoint = {'X': self.endPos['X']- self.pos['X'], 'Y': self.endPos['Y']- self.pos['Y']}

        # Get angle aof reference, real and theoretical
        theoreticalAngleLastPoint = math.atan(theoreticalPosLastPoint['Y'] / (theoreticalPosLastPoint['X']+0.000001))
        realAngleLastPoint = math.atan(realPosLastPoint['Y'] / (realPosLastPoint['X']+0.000001))

        # compute angle offset of real referance position
        angleOffset = realAngleLastPoint - theoreticalAngleLastPoint

        correctedCmpPos['C'] = math.degrees(angleOffset)

        return correctedCmpPos

    def getPositionById(self, cmpId):
        recalculatePosition = self.__getCorrectedPositionLinear(cmpId)
        return {'X': recalculatePosition['X'], 'Y': recalculatePosition['Y'], 'Z': self.pos['Z'], 'C': recalculatePosition['C']}

    def getComponentPosition(self):
        """
        Get the position of the next component to be picked up.
        :return: position of component {'X': posx, 'Y': posy, 'Z':posz, 'C': theta correction}
        """
        return self.getPositionById(self.nextComponent)

    def prepareNextComponent(self):
        """
        Remove one component from feeder.
        Call this when the machine pickup the component.
        :return: 0 if more component are présent, otherwise return 1
        """
        if self._haveComponent:
            self.nextComponent += 1

            if self.nextComponent >= self.componentPerStrip:  # Change strip
                self.nextComponent = 0
                self._haveComponent = False

            self.saveMachineFunction()
            return 0 if self._haveComponent else 1
        return 1

    def reload(self):
        self.nextComponent = 0
        self._haveComponent = True



class ReelFeeder(Feeder):
    def __init__(self, paramList, saveMachineFunction):
        Feeder.__init__(self, paramList, saveMachineFunction)
        self.type = 'reelfeeder'
        self.I2Caddr = int(paramList['I2Caddr']) if 'I2Caddr' in paramList else 0xFF
        self.step = float(paramList['step']) if 'step' in paramList else 1.0
        self.compByStep = float(paramList['compByStep']) if 'compByStep' in paramList else 1.0

    def saveInLxml(self, rootLxml):
        feederRoot = Feeder.saveInLxml(self, rootLxml)
        etree.SubElement(feederRoot, 'I2Caddr').text = str(self.I2Caddr)
        etree.SubElement(feederRoot, 'step').text = str(self.step)
        etree.SubElement(feederRoot, 'compByStep').text = str(self.compByStep)

    def __repr__(self):
        return '{} {}: name = {}, X = {}, Y = {}, Z = {} \n  address = {}, step = {}, compByStep = {}'.format(self.type,
                                                                                                              self.id,
                                                                                                              self.name,
                                                                                                              self.pos[
                                                                                                                  'X'],
                                                                                                              self.pos[
                                                                                                                  'Y'],
                                                                                                              self.pos[
                                                                                                                  'Z'],
                                                                                                              self.I2Caddr,
                                                                                                              self.step,
                                                                                                              self.compByStep)


class MachineConf:
    """
    Contain all information of the machine.
    Motor parameters.
    Feeder list and parameters.
    ...
    """

    def __init__(self, pathFile, logger):
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
        self.logger = logger

        self.__loadFromXml()

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
        :param accelData: dict wich contain accel for axis
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
        :param stepData: dict wich contain step value for axis
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
        :param speedData: dict wich contain maxSpeed for axis
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
        feederData = {}
        # import dara from xml
        for element in feederRoot:
            feederData[element.tag] = element.text

        feederData['id'] = int(idFeeder)
        # create feeder
        if feederData['type'] == 'feeder':
            self.addFeeder(Feeder(feederData, self.saveToXml))
        elif feederData['type'] == 'reelfeeder':
            self.addFeeder(ReelFeeder(feederData, self.saveToXml))
        elif feederData['type'] == 'stripfeeder':
            self.addFeeder(StripFeeder(feederData, self.saveToXml))
        elif feederData['type'] == 'compositefeeder':
            feederData['feederList'] = self.makeFilteredFeederList(feederData['feederListStr'])
            self.addFeeder(CompositeFeeder(feederData, self.saveToXml))

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

    def __loadFromXml(self):
        """
        Load data from xml file pointed by self.pathFile
        :return:
        """
        # reset feederList
        self.feederList = []
        try:
            root = etree.parse(self.pathFile).getroot()
        except:
            self.logger.printCout("Error file don't exist: Make new model file")
            self.saveToXml()
            # self.__makeNewFile()
        else:
            self.logger.printCout("Load machine configuration")
            machineRoot = root.find('machine')
            self.zHead = float(xe.getXmlValue(machineRoot, 'zHead', 0.0))
            self.zLift = float(xe.getXmlValue(machineRoot, 'zLift', 10.0))
            self.scanPosition = xe.getPosFromXml(machineRoot.find('scan_position'))
            self.boardRefPosition = xe.getPosFromXml(machineRoot.find('boardRef_position'))
            self.trashPosition = xe.getPosFromXml(machineRoot.find('trash_position'))

            axisRoot = machineRoot.find('axis')
            for axis in axisRoot:
                self.__axisLoadFromXml(axis.tag, axisRoot.find(axis.tag))

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

    def deleteFeeder(self, id):
        idFound = 'None'
        for feederPos in range(len(self.feederList)):
            if self.feederList[feederPos].id == id:
                idFound = feederPos

        if type(idFound) is int:
            del self.feederList[idFound]

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

    def getFeederById(self, idFeeder):
        for feeder in self.feederList:
            if feeder.id == idFeeder:
                return feeder
        self.logger.printCout('Mconf: feeder {} not found'.format(idFeeder))

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

log = lg.logger()
mach = MachineConf('userdata/conf/machine.xml', log)

# mach.addFeeder(ReelFeeder({'id': 5, 'name': 'feederTest', 'xPos': 18.5, 'yPos': -2.5, 'zPos': 44.5, 'I2Caddr': 25, 'step':22, 'compByStep': 99}))

# mach.saveToXml()
print(mach)
