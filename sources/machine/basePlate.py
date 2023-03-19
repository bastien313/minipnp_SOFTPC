from lxml import etree
import math


class BasePlate:
    """
    Represent a plate put on machine with an offset(X, Y, Z) and an orientation.
    """

    def __init__(self, paramList):
        """
        Initialise base plate from paramList
        """
        self._type = None
        self._rotationOffset = None
        self._zRamp = None
        self._name = None
        self._id = None
        self._realRef = None
        self._vectorRef = None
        self.buildBasePlateFromConfDict(paramList)

    def configureFromXml(self, xmlRoot):
        basePlateData = {}
        for element in xmlRoot:
            basePlateData[element.tag] = element.text
        self.buildBasePlateFromConfDict(basePlateData)

    def buildBasePlateFromConfDict(self, confDict):
        self._realRef = [
            confDict['realRef1'] if 'realRef1' in confDict else {'X': 0.0, 'Y': 0.0, 'Z': 0.0},
            confDict['realRef2'] if 'realRef2' in confDict else {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        ]
        self._vectorRef = confDict['vectorRef'] if 'vectorRef' in confDict else {'X': 0.0, 'Y': 0.0, 'Z': 0.0}
        self._vectorRef['Z'] = 0.0 if 'Z' not in self._vectorRef else self._vectorRef['Z']
        self._id = int(confDict['id']) if 'id' in confDict else 0
        self._name = confDict['name'] if 'name' in confDict else 'Noname'
        self._zRamp = float(confDict['zRamp']) if 'zRamp' in confDict else 0.0
        self._rotationOffset = float(confDict['rotationOffset']) if 'rotationOffset' in confDict else 0.0
        self._type = 'BasePlate'

        self._realRef[0]['X'] = float(confDict['ref0X']) if 'ref0X' in confDict else self._realRef[0]['X']
        self._realRef[0]['Y'] = float(confDict['ref0Y']) if 'ref0Y' in confDict else self._realRef[0]['Y']
        self._realRef[0]['Z'] = float(confDict['ref0Z']) if 'ref0Z' in confDict else self._realRef[0]['Z']
        self._realRef[1]['X'] = float(confDict['ref1X']) if 'ref1X' in confDict else self._realRef[1]['X']
        self._realRef[1]['Y'] = float(confDict['ref1Y']) if 'ref1Y' in confDict else self._realRef[1]['Y']
        self._realRef[1]['Z'] = float(confDict['ref1Z']) if 'ref1Z' in confDict else self._realRef[1]['Z']
        self._vectorRef['X'] = float(confDict['vectorX']) if 'vectorX' in confDict else self._vectorRef['X']
        self._vectorRef['Y'] = float(confDict['vectorY']) if 'vectorY' in confDict else self._vectorRef['Y']
        self._vectorRef['Z'] = float(confDict['vectorZ']) if 'vectorZ' in confDict else self._vectorRef['Z']

    def setRealRef(self, position, refId):
        self._realRef[refId] = position

    def getRealRef(self, refId):
        return self._realRef[refId]

    def setTheorVector(self, vector):
        self._vectorRef = vector

    def getTheorVector(self):
        return self._vectorRef

    def computeFromRef(self):
        """
        Compute rotationOffset and z ramp from loaded referances.
        """
        angleTheorical = math.acos(self._vectorRef['X'] / math.hypot(self._vectorRef['X'], self._vectorRef['Y']))
        recaledPos = {'X': self._realRef[1]['X'] - self._realRef[0]['X'],
                      'Y': self._realRef[1]['Y'] - self._realRef[0]['Y'],
                      'Z': self._realRef[1]['Z'] - self._realRef[0]['Z']}
        realAngle = math.acos(recaledPos['X'] / math.hypot(self._vectorRef['X'], self._vectorRef['Y']))

        self._rotationOffset = realAngle - angleTheorical
        self._zRamp = (self._realRef[1]['Z'] - self._realRef[0]['Z']) / math.hypot(self._vectorRef['X'],
                                                                                   self._vectorRef['Y'])

    def computeFromAngle(self):
        """
        Compute ref 2 from loaded correction.
        """
        theorRef2Pos = {
            'X': self._realRef[0]['X'] + self._vectorRef['X'],
            'Y': self._realRef[0]['Y'] + self._vectorRef['Y'],
            'Z': self._realRef[0]['Z'] + self._vectorRef['Z'],
        }
        self._realRef[1] = self.getPointCorrected(theorRef2Pos)

    def setZramp(self, ramp):
        """
        Set z ramp value.
        """
        self._zRamp = ramp

    def getZramp(self):
        """
        Return z ramp value.
        """
        return self._zRamp

    def setRotation(self, rot):
        """
        Set rotation value, WARNING rotation must be in radians.
        """
        self._rotationOffset = rot

    def getRotationOffset(self):
        """
        Return rotation offset in radians.
        """
        return self._rotationOffset

    def getPointCorrected(self, point):
        """
        Get the réal position of the théorical point position.
        Point position must be on global system coordinate.
        :param point: position of théorical point.
        Return new position in global system coordinate.
        """
        pointRecaled = {
            'X': point['X'] - self._realRef[0]['X'],
            'Y': point['Y'] - self._realRef[0]['Y'],
            'Z': point['Z'] - self._realRef[0]['Z']
        }

        newPoint = {
            'X': (pointRecaled['X'] * math.cos(self._rotationOffset)) - (
                    pointRecaled['Y'] * math.sin(self._rotationOffset)),
            'Y': (pointRecaled['X'] * math.sin(self._rotationOffset)) + (
                    pointRecaled['Y'] * math.cos(self._rotationOffset)),
            'Z': pointRecaled['Z'] +
                 self._zRamp * ((math.hypot(pointRecaled['X'], pointRecaled['Y'])) /
                                (math.hypot(self._vectorRef['X'], self._vectorRef['Y'])))
        }

        return {
            'X': newPoint['X'] + self._realRef[0]['X'],
            'Y': newPoint['Y'] + self._realRef[0]['Y'],
            'Z': newPoint['Z'] + self._realRef[0]['Z']
        }

    def saveInLxml(self, rootLxml):
        """
        Save feeder parameter in xml.
        :param rootLxml:
        :return: return the created root for inherited class.
        """
        bpRoot = etree.SubElement(rootLxml, 'basePlate_' + str(self._id))
        etree.SubElement(bpRoot, 'name').text = self._name
        etree.SubElement(bpRoot, 'type').text = self._type
        etree.SubElement(bpRoot, 'ref0X').text = str(self._realRef[0]['X'])
        etree.SubElement(bpRoot, 'ref0Y').text = str(self._realRef[0]['Y'])
        etree.SubElement(bpRoot, 'ref0Z').text = str(self._realRef[0]['Z'])
        etree.SubElement(bpRoot, 'ref1X').text = str(self._realRef[1]['X'])
        etree.SubElement(bpRoot, 'ref1Y').text = str(self._realRef[1]['Y'])
        etree.SubElement(bpRoot, 'ref1Z').text = str(self._realRef[1]['Z'])
        etree.SubElement(bpRoot, 'vectorX').text = str(self._vectorRef['X'])
        etree.SubElement(bpRoot, 'vectorY').text = str(self._vectorRef['Y'])
        etree.SubElement(bpRoot, 'vectorZ').text = str(self._vectorRef['Z'])
        etree.SubElement(bpRoot, 'zRamp').text = str(self._zRamp)
        etree.SubElement(bpRoot, 'rotationOffset').text = str(self._rotationOffset)
        return bpRoot

    def _getId(self):
        return self._id

    def _getType(self):
        return self._type

    def _getName(self):
        return self._name

    id = property(fget=_getId)
    type = property(fget=_getType)
    name = property(fget=_getName)


class BasePlateForStripFeeder(BasePlate):
    def __init__(self, confDict):
        self._vectorFirstCmp = None
        self._stripStep = None
        if not 'vectorRef' in confDict:
            confDict['vectorRef'] = {'X': 73.2, 'Y': 196.0}
        BasePlate.__init__(self, confDict)
        self.buildBasePlateFromConfDict(confDict)

    def configureFromXml(self, xmlRoot):
        basePlateData = {}
        for element in xmlRoot:
            basePlateData[element.tag] = element.text
        self.buildBasePlateFromConfDict(basePlateData)

    def buildBasePlateFromConfDict(self, confDict):
        BasePlate.buildBasePlateFromConfDict(self, confDict)
        self._stripStep = float(confDict['stripStep']) if 'stripStep' in confDict else 10.6
        self._vectorFirstCmp = confDict['vectorFistCmp'] if 'vectorFistCmp' in confDict else {'X': 6.2295,
                                                                                              'Y': 196.16, 'Z': 0.0}
        self._type = 'StripFeederBasePlate'
        self._vectorFirstCmp['X'] = float(confDict['vectorCmpX']) if 'vectorX' in confDict else self._vectorFirstCmp[
            'X']
        self._vectorFirstCmp['Y'] = float(confDict['vectorCmpY']) if 'vectorY' in confDict else self._vectorFirstCmp[
            'Y']
        self._vectorFirstCmp['Z'] = float(confDict['vectorCmpZ']) if 'vectorZ' in confDict else self._vectorFirstCmp[
            'Z']

    def getTheoreticalFirstCmpPosition(self, stripId):
        """
        Return the first component position referance of strip selected.
        The position is theorical , its NOT corrected.
        Note: strip id start from 0.
        """
        return {
            'X': (self._realRef[0]['X'] + self._vectorFirstCmp['X']) + (stripId * self._stripStep),
            'Y': self._realRef[0]['Y'] + self._vectorFirstCmp['Y'],
            'Z': self._realRef[0]['Z'] + self._vectorFirstCmp['Z']
        }

    def saveInLxml(self, rootLxml):
        bpRoot = BasePlate.saveInLxml(self, rootLxml)
        etree.SubElement(bpRoot, 'stripStep').text = str(self._stripStep)
        etree.SubElement(bpRoot, 'vectorCmpX').text = str(self._vectorFirstCmp['X'])
        etree.SubElement(bpRoot, 'vectorCmpY').text = str(self._vectorFirstCmp['Y'])
        etree.SubElement(bpRoot, 'vectorCmpZ').text = str(self._vectorFirstCmp['Z'])
        return bpRoot

    def getStripStep(self):
        return self._stripStep

    def setStripStep(self, step):
        self._stripStep = step

    def getVectorFirstCmp(self):
        return self._vectorFirstCmp

    def setVectorFirstCmp(self, vector):
        self._vectorFirstCmp = vector
