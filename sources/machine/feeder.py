from .basePlate import *
from lxml import etree
from .machine import FeederNotFound


class Feeder:
    def __init__(self, paramList, machine):
        self.type = 'feeder'
        self.id = int(paramList['id']) if 'id' in paramList else 0
        self.basePlateId = int(paramList['basePlateId']) if 'basePlateId' in paramList else 0
        self.localBasePlate = paramList['localBasePlate'] if 'localBasePlate' in paramList else BasePlate(
            {'name': 'Local'})
        self.name = paramList['name'] if 'name' in paramList else 'noname'
        self._haveComponent = True
        self._machine = machine

    def prepareBeforePick(self):
        return

    def prepareAfterPick(self):
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
        return {'X': 0, 'Y': 0, 'Z': 0, 'C': 0}

    def saveInLxml(self, rootLxml):
        """
        Save feeder parameter in xml.
        :param rootLxml:
        :return: return the created root for inherited class.
        """
        feederRoot = etree.SubElement(rootLxml, 'feeder_' + str(self.id))
        etree.SubElement(feederRoot, 'name').text = self.name
        etree.SubElement(feederRoot, 'type').text = self.type
        etree.SubElement(feederRoot, 'basePlateId').text = str(self.basePlateId)
        self.localBasePlate.saveInLxml(feederRoot)
        return feederRoot


class MechanicalFeeder(Feeder):
    def __init__(self, paramList, machine, driver):
        Feeder.__init__(self, paramList=paramList, machine=machine)
        self.type = 'mechanicalfeeder'
        self._pickupPos = paramList['pickupPos'] if 'pickupPos' in paramList else {'X': 0.0, 'Y': 0.0, 'Z': 0.0,
                                                                                   'C': 0.0}
        self._leverLowPos = paramList['leverLowPos'] if 'nextCmpPos' in paramList else {'X': 0.0, 'Y': 0.0, 'Z': 0.0,
                                                                                        'C': 0.0}
        if 'C' not in self._pickupPos:
            self._pickupPos['C'] = 0.0
        if 'C' not in self._leverLowPos:
            self._leverLowPos['C'] = 0.0

        self._driver = driver

    def saveInLxml(self, rootLxml):
        feederRoot = Feeder.saveInLxml(self, rootLxml)
        etree.SubElement(feederRoot, 'pickupPosX').text = str(self._pickupPos['X'])
        etree.SubElement(feederRoot, 'pickupPosY').text = str(self._pickupPos['Y'])
        etree.SubElement(feederRoot, 'pickupPosZ').text = str(self._pickupPos['Z'])
        etree.SubElement(feederRoot, 'pickupPosC').text = str(self._pickupPos['C'])
        etree.SubElement(feederRoot, 'leverLowPosX').text = str(self._leverLowPos['X'])
        etree.SubElement(feederRoot, 'leverLowPosY').text = str(self._leverLowPos['Y'])
        etree.SubElement(feederRoot, 'leverLowPosZ').text = str(self._leverLowPos['Z'])
        etree.SubElement(feederRoot, 'leverLowPosC').text = str(self._leverLowPos['C'])
        return feederRoot

    def haveComponent(self):
        return True

    def getPositionById(self, cmpId=0):
        """
        Return position of selected component.
        'C' contain the  rotation correction.
        """
        return self._pickupPos

    def getComponentPosition(self):
        """
        Get the position of the next component to be picked up.
        :return: position of component {'X': posx, 'Y': posy, 'Z':posz, 'C': theta correction}
        """
        return self.getPositionById()

    def prepareAfterPick(self):
        while self._driver.isBusy():
            pass
        self._driver.moveAxis(moveData={'Z': self._machine.zLift})

        while self._driver.isBusy():
            pass
        self._driver.moveAxis(moveData={'X': self._leverLowPos['X'], 'Y': self._leverLowPos['X']})

        while self._driver.isBusy():
            pass
        self._driver.moveAxis(moveData={'Z': self._leverLowPos['Z']})

        while self._driver.isBusy():
            pass
        self._driver.moveAxis(moveData={'Z': self._machine.zLift})

        while self._driver.isBusy():
            pass


class CompositeFeeder(Feeder):
    def __init__(self, paramList, machine):
        Feeder.__init__(self, paramList=paramList, machine=machine)
        self.type = 'compositefeeder'
        self.feederList = paramList['feederList'] if 'feederList' in paramList else []
        self._precedentFeederPickup = 0  # last feeder which user request position.

    def saveInLxml(self, rootLxml):
        feederRoot = Feeder.saveInLxml(self, rootLxml)
        etree.SubElement(feederRoot, 'feederListStr').text = self.feederListToStr()
        return feederRoot

    def getPositionById(self, cmpId):
        cmpOfFeeder = cmpId
        for feeder in self.feederList:
            # feeder = self._machine.getFeederById(feederId)
            if (cmpOfFeeder - feeder.componentPerStrip) >= 0:
                cmpOfFeeder -= feeder.componentPerStrip
            else:
                return feeder.getPositionById(cmpOfFeeder)

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

    def prepareAfterPick(self):
        """
        Remove one component from feeder.
        Call this when the machine pickup the component.
        :return: 0 if more component are présent, otherwise return 1
        """
        if self.haveComponent():
            self._precedentFeederPickup.prepareAfterPick()
            return 0 if self.haveComponent() else 1
        return 1

    def feederListToStr(self):
        feederListStr = ''
        for feeder in self.feederList:
            feederListStr += '{}|'.format(feeder.id)
        return feederListStr[:-1]


class StripFeeder(Feeder):
    def __init__(self, machine, paramList):
        Feeder.__init__(self, machine=machine, paramList=paramList)
        self.type = 'stripfeeder'
        self.componentPerStrip = int(paramList['componentPerStrip']) if 'componentPerStrip' in paramList else 1
        self.localBasePlate = paramList['localBasePlate'] if 'localBasePlate' in paramList else BasePlateForStripFeeder(
            {'name': 'Local'})
        self.componentStep = float(paramList['componentStep']) if 'componentStep' in paramList else 1
        self.stripIdInBasePlate = int(paramList['stripIdInBasePlate']) if 'stripIdInBasePlate' in paramList else 0
        # Adress of next component to be picked up
        self.nextComponent = int(paramList['nextComponent']) if 'nextComponent' in paramList else 0

    def saveInLxml(self, rootLxml):
        feederRoot = Feeder.saveInLxml(self, rootLxml)
        etree.SubElement(feederRoot, 'componentPerStrip').text = str(self.componentPerStrip)
        etree.SubElement(feederRoot, 'componentStep').text = str(self.componentStep)
        etree.SubElement(feederRoot, 'nextComponent').text = str(self.nextComponent)
        etree.SubElement(feederRoot, 'stripIdInBasePlate').text = str(self.stripIdInBasePlate)

    """
        def __getCorrectedPositionLinear(self, cmpId):
        xRamp = (self.endPos['X'] - self.pos['X']) / (self.componentPerStrip - 1)
        yRamp = (self.endPos['Y'] - self.pos['Y']) / (self.componentPerStrip - 1)

        correctedCmpPos = {}
        correctedCmpPos['X'] = self.pos['X'] + cmpId * xRamp
        correctedCmpPos['Y'] = self.pos['Y'] + cmpId * yRamp

        theoreticalPosLastPoint = {'X': 0,
                                   'Y': math.sqrt(xRamp * xRamp + yRamp * yRamp) * float(
                                       self.componentPerStrip - 1)}  # Ramene la referance a 0
        realPosLastPoint = {'X': self.endPos['X'] - self.pos['X'], 'Y': self.endPos['Y'] - self.pos['Y']}

        # Get angle aof reference, real and theoretical
        theoreticalAngleLastPoint = math.atan(theoreticalPosLastPoint['Y'] / (theoreticalPosLastPoint['X'] + 0.000001))
        realAngleLastPoint = math.atan(realPosLastPoint['Y'] / (realPosLastPoint['X'] + 0.000001))

        # compute angle offset of real referance position
        angleOffset = realAngleLastPoint - theoreticalAngleLastPoint

        correctedCmpPos['C'] = math.degrees(angleOffset)

        return correctedCmpPos
    """

    def getPositionById(self, cmpId):
        """
        Return the réal position of selected component.
        'C' contain the  rotation correction.
        """
        basePlate = self.localBasePlate if self.basePlateId == 0 else self._machine.getBasePlateById(self.basePlateId)
        firstCmpPosTheor = basePlate.getTheoreticalFirstCmpPosition(self.stripIdInBasePlate)
        firstCmpPosTheor['Y'] -= cmpId * self.componentStep
        realPoint = basePlate.getPointCorrected(firstCmpPosTheor)
        realPoint['C'] = basePlate.getRotationOffset()
        return realPoint

    def getComponentPosition(self):
        """
        Get the position of the next component to be picked up.
        :return: position of component {'X': posx, 'Y': posy, 'Z':posz, 'C': theta correction}
        """
        return self.getPositionById(self.nextComponent)

    def prepareAfterPick(self):
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

            self._machine.saveToXml()
            return 0 if self._haveComponent else 1
        return 1

    def reload(self):
        self.nextComponent = 0
        self._haveComponent = True


class ReelFeeder(Feeder):
    def __init__(self, paramList, machine):
        Feeder.__init__(self, paramList=paramList, machine=machine)
        self.type = 'reelfeeder'
        self.I2Caddr = int(paramList['I2Caddr']) if 'I2Caddr' in paramList else 0xFF
        self.step = float(paramList['step']) if 'step' in paramList else 1.0
        self.compByStep = float(paramList['compByStep']) if 'compByStep' in paramList else 1.0

    def saveInLxml(self, rootLxml):
        feederRoot = Feeder.saveInLxml(self, rootLxml)
        etree.SubElement(feederRoot, 'I2Caddr').text = str(self.I2Caddr)
        etree.SubElement(feederRoot, 'step').text = str(self.step)
        etree.SubElement(feederRoot, 'compByStep').text = str(self.compByStep)