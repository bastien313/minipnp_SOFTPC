# coding: utf-8
import threading, queue

import serial
import serial.tools.list_ports
import time
from deprecated import deprecated


class SerialManager(threading.Thread):
    def __init__(self, logger, endLineCharacter='\r'):
        threading.Thread.__init__(self)
        self._receiveBuffer = ""
        self._emissionBufferQueue = queue.Queue()
        self._endLineCharacter = endLineCharacter
        self._serialAccess = serial.Serial()
        self._logger = logger
        self._funcPipe = {0: lambda: None, 1: lambda: None}

    def run(self):
        while 1:
            if self._serialAccess.is_open:
                error = 0
                try:
                    error = 1
                    self.__receive()
                    error = 2
                    self.__emission()

                except:
                    if error == 1:
                        self._logger.printCout('Serial read error, close.')
                    else:
                        self._logger.printCout('Serial write error, close.')
                    self._serialAccess.close()
                    self._receiveBuffer = ""

            else:
                self.__searchAndConnectDevice()
                time.sleep(0.500)

            # time.sleep(0.00002)

    def setRecpetionPipeCallBack(self, pipe, callback):
        self._funcPipe[pipe] = callback

    def sendLine(self, str):
        """
        Put string to send in queue
        :param str: string to send
        :return:
        """
        self._emissionBufferQueue.put(str)

    def clearBuffer(self, pipe):
        self._receiveBuffer = ""
        # self._bufferLineInput[pipe] = []

    def isConnected(self):
        return self._serialAccess.is_open

    def __searchAndConnectDevice(self):
        listCom = serial.tools.list_ports.comports()
        for port in listCom:
            if port.serial_number is not None:
                if 'MPNP' in port.serial_number:
                    self._serialAccess.baudrate = 115200
                    self._serialAccess.timeout = 0
                    try:
                        self._serialAccess.port = port.device  # this action call .open()
                        self._serialAccess.open()
                    except:
                        self._serialAccess.close()

    def __emission(self):
        while not self._emissionBufferQueue.empty():
            lineOut = self._emissionBufferQueue.get()
            if lineOut[-1] != self._endLineCharacter:
                lineOut += self._endLineCharacter
            # print(lineOut.encode('utf-8'))
            self._serialAccess.write(lineOut.encode('utf-8'))

    def __receive(self):
        """
        Called from timer.
        Proces low level recption of serial port.
        :return:
        """
        byteIn = self._serialAccess.read(size=64)
        byteIn = byteIn.decode("utf-8")
        for byte in byteIn:
            self._receiveBuffer += byte
            if byte == self._endLineCharacter:
                if self._receiveBuffer[0] == '0':
                    self._funcPipe[0](self._receiveBuffer[1:-1])
                elif self._receiveBuffer[0] == '1':
                    self._funcPipe[1](self._receiveBuffer[1:-1])
                else:
                    if len(self._receiveBuffer):
                        self._logger.printCout(
                            'Pipe {} on {} doesnt exist, data discarded'.format(self._receiveBuffer[0],
                                                                                self._receiveBuffer))
                    else:
                        self._logger.printCout('Void command')
                self._receiveBuffer = ""


class PnpDriver:

    def __init__(self, logger):
        self._relativeMode = 'A'
        # self._bufferLineInputPipe0 = []
        self._speed = 100.0
        # self._GcodeLine = ''
        self.logger = logger
        self.feederList = {}
        self._serManage = SerialManager(self.logger)
        self._serManage.setRecpetionPipeCallBack(pipe=0, callback=self.__pipe0DataReception)
        self._serManage.setRecpetionPipeCallBack(pipe=1, callback=self.__pipe1DataReception)
        self.__statusPipeCallBack = lambda: None
        self._commadUnackited = 0  # Number of bomand is unackited
        self._queue = queue.Queue()
        self.status = {'X': '00', 'Y': '00', 'Z': '00', 'C': '00'}
        self._jobHaveControl = False

    def jobTakeControl(self):
        self._jobHaveControl = True

    def jobReleaseControl(self):
        self._jobHaveControl = False

    def jobHaveControl(self):
        return self._jobHaveControl

    def isConnected(self):
        return self._serManage.isConnected()

    def setStatusPipeCallBack(self, callback):
        self.__statusPipeCallBack = callback

    def __lineIsPresent(self):
        """
        :return: Int, ammount of line can be read.
        """
        return not self._queue.empty()
        # return len(self._bufferLineInputPipe0)

    def __getLine(self, delete=True):
        """
        Return first line recepted et delete it.
        :param delete: set to False if delete is not needed
        :return: First line recepted
        """
        return self._queue.get()
        # ret = self._bufferLineInputPipe0[0]
        # if delete:
        #    del self._bufferLineInputPipe0[0]
        # return ret

    def __pipe1DataReception(self, data):
        self.status = self.coordParse(data)
        # self.__statusPipeCallBack(dicOut)

    def __pipe0DataReception(self, data):
        self._queue.put(data)
        # self._bufferLineInputPipe0.append(data)
        # self.logger.printCout('RX: ' + data)
        # self.logger.printDirectConsole('RX: ' + data)

    def startDiscoveringDevice(self):
        self._serManage.start()

    def __setCoordMode(self, mode):
        """Add relative or absolute to Gcode line if neeeded
            Relative = G90, Absolute = G91"""

        # if self._relativeMode != mode:
        self._relativeMode = mode
        if self._relativeMode == 'R':
            line = 'G91 '
        else:
            line = 'G90 '

        self.__sendGcodeLine(line)
        self.readLine()

    def setAccel(self, accelData):
        """
        Set acceleration
        :param accelData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is accelValue
        :return:
        """
        line = 'M201 '
        for key, value in accelData.items():
            line += "{}{} ".format(key, float(value))

        self.__sendGcodeLine(line)
        self.readLine()

    def setStepConf(self, stepData):
        """
        Set step/mm or step/deg
        :param stepData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is stepValue
        :return:
        """
        line = 'M92 '
        for key, value in stepData.items():
            line += "{}{} ".format(key, float(value))

        self.__sendGcodeLine(line)
        self.readLine()

    def setMaxSpeed(self, speedData):
        """
        Set max speed of axis
        :param speedData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is maxSpeed
        :return:
        """
        line = 'M203 '
        for key, value in speedData.items():
            line += "{}{} ".format(key, float(value))

        self.__sendGcodeLine(line)
        self.readLine()

    def isBusy(self):
        """
        Check if machine if busy.
        :return:
        """
        if not self.isConnected():
            return 1
        self.__sendGcodeLine('R400')
        line = self.readLine()
        return 1 if line != '0' else 0

    def stopMachine(self):
        """
        Send stop Request
        :return:
        """
        self.__sendGcodeLine('S99')

    def makeScan(self):
        self.__sendGcodeLine('R500')
        response = self.readLine()
        return int(response)

    def makeScanLine(self, axis, speed, lengt, nbMesure):
        line = 'R501 A{} N{} L{} F{}'.format(axis, nbMesure, lengt, speed)
        self.__sendGcodeLine(line)
        nb = int(self.readLine(timeOut=20))
        arrayOut = []
        for mes in range(nb):
            lineMes = self.readLine().split()
            print(lineMes)
            arrayOut.append((float(lineMes[0]), int(lineMes[1])))
        return arrayOut

    def getPresure(self):
        self.__sendGcodeLine('R600')
        response = self.readLine()
        return float(response)

    def sendMachineConf(self, machine):
        self.setMaxSpeed({
            'X': machine.axisConfArray['X'].speed,
            'Y': machine.axisConfArray['Y'].speed,
            'Z': machine.axisConfArray['Z'].speed,
            'C': machine.axisConfArray['C'].speed})

        self.setStepConf({
            'X': machine.axisConfArray['X'].step,
            'Y': machine.axisConfArray['Y'].step,
            'Z': machine.axisConfArray['Z'].step,
            'C': machine.axisConfArray['C'].step})

        self.setAccel({
            'X': machine.axisConfArray['X'].accel,
            'Y': machine.axisConfArray['Y'].accel,
            'Z': machine.axisConfArray['Z'].accel,
            'C': machine.axisConfArray['C'].accel})

    def saveFlashConf(self):
        """
        Save setting of hardware in FLASH
        :return:
        """
        self.__sendGcodeLine('M500')
        self.readLine()

    def moveX(self, value, mode='A', speedMode='P'):
        tabOut = {'X': value}
        self.moveAxis(moveData=tabOut, mode=mode, speedMode=speedMode)

    def moveY(self, value, mode='A', speedMode='P'):
        tabOut = {'Y': value}
        self.moveAxis(moveData=tabOut, mode=mode, speedMode=speedMode)

    def moveZ(self, value, mode='A', speedMode='P'):
        tabOut = {'Z': value}
        self.moveAxis(moveData=tabOut, mode=mode, speedMode=speedMode)

    def moveC(self, value, mode='A', speedMode='P'):
        tabOut = {'C': value}
        self.moveAxis(moveData=tabOut, mode=mode, speedMode=speedMode)

    def moveAxis(self, moveData, speed=10, speedRot=None, mode='A', speedMode='P'):
        """ moveData must be an dict.
            Key must be 'X' , 'Y, 'Z' or 'C'.
            Value is displacement
            Mode is the mode of displacement, 'A' = absolute, 'R'= relative
            Speed must be 'P' for (parametric speed)G1 or 'H' (Hight speed)G0"""

        self.__setCoordMode(mode)

        if self._relativeMode == 'A' and 'C' in moveData:
            moveData['C'] = moveData['C'] + float(self.status['C'])

        if speedMode == 'P':
            line = 'G1 '
        else:
            line = 'G0 '

        line += "FF{} ".format(float(speed))
        if speedRot:
            line += "FR{} ".format(float(speedRot))

        for key, value in moveData.items():
            line += "{}{} ".format(key, float(value))

        self.__sendGcodeLine(line)

        # return self.readLine(20)

    def stopAxis(self, axis):
        """
        Send stop function.
        :param axis: must contain 'ALL' or 'X' or 'Y' or 'Z' or 'C' or composition of axis ex('XYC'):
        :return:
        """
        axis = axis.upper()
        line = 'S99 '
        if axis != 'ALL':
            if axis.find('X') >= 0:
                line += 'X '
            if axis.find('Y') >= 0:
                line += 'Y '
            if axis.find('Z') >= 0:
                line += 'Z '
            if axis.find('C') >= 0:
                line += 'C'
        self.__sendGcodeLine(line)

    def motorEnable(self):
        """
        Enable driver motor.
        :return:
        """
        self.__sendGcodeLine('S11')

    def motorDisable(self):
        """
        Enable driver motor.
        :return:
        """
        self.__sendGcodeLine('S00')

    def watchDogEnable(self):
        """
        Enable Watchdog mode, if enable the program must feed the watchdog formotor move.
        :return:
        """
        self.__sendGcodeLine('S21')

    def watchDogDisable(self):
        """
        Disable Watchdog mode.
        :return:
        """
        self.__sendGcodeLine('S20')

    def watchDogFeed(self):
        """
        Disable Watchdog mode.
        :return:
        """
        self.__sendGcodeLine('S22')

    def statusModeEnable(self):
        """
        Enable status mode, machine will send status data over pipe 1 at 400ms.
        :return:
        """
        self.__sendGcodeLine('S31')

    def statusModeDisable(self):
        """
        Disable status mode.
        :return:
        """
        self.__sendGcodeLine('S30')

    def homeAxis(self, axis):
        """
        Send home function.
        :param axis must contain 'ALL' or 'X' or 'Y' or 'Z' or 'C' or composition of axis ex('XYC'):
        :return:
        """
        line = 'G28 '
        if axis != 'ALL':
            if axis.find('X') >= 0:
                line += 'X '
            if axis.find('Y') >= 0:
                line += 'Y '
            if axis.find('Z') >= 0:
                line += 'Z '
            if axis.find('C') >= 0:
                line += 'C'

        self.__sendGcodeLine(line)

    def ctrlPump(self, state):
        self.__ctrlDigitalOuput(0, state)

    def ctrlEv(self, state):
        self.__ctrlDigitalOuput(1, 0 if state else 1)

    def ctrlExt(self, state):
        self.__ctrlDigitalOuput(2, state)

    def __ctrlDigitalOuput(self, line, state):
        """
        Activate opr desactivate digital ouput.
        :param line the number of digital ouput:
        :param state the state of digital output:
        :return:
        """

        if state:
            line = 'M64 {}'.format(line)
        else:
            line = 'M65 {}'.format(line)

        self.__sendGcodeLine(line)

    @deprecated
    def readConf(self):
        """
        Return all configuration  of hardware exept feeder.
        :return: A dict wich this key ('ACCEL', 'MAXSPEED', 'STEPBYMM', 'SCANREF', 'BOARDREF', 'HEADREF')
        """
        dicOut = {'ACCEL': self.readAccel(), 'MAXSPEED': self.readMaxSpeed(), 'STEPBYMM': self.readStepConf(),
                  'SCANREF': self.readScanRef(), 'BOARDREF': self.readBoardRef(), 'HEADREF': self.readHeadZ()}

        return dicOut

    def readAccel(self):
        """
        Get acceleration from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        self.__sendGcodeLine('R201')
        dicOut = self.coordParse(self.readLine())
        return dicOut

    def readStepConf(self):
        """
        Get step/mm from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        self.__sendGcodeLine('R92')
        dicOut = self.coordParse(self.readLine())
        return dicOut

    def readMaxSpeed(self):
        """
        Get maxSpeed from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        self.__sendGcodeLine('R203')
        dicOut = self.coordParse(self.readLine())
        return dicOut

    @deprecated
    def readScanRef(self):
        """
        Get ScanRef from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5}
        """
        self.__sendGcodeLine('R330')
        dicOut = self.coordParse(self.readLine())
        return dicOut

    @deprecated
    def readBoardRef(self):
        """
        Get Board Ref from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5}
        """
        self.__sendGcodeLine('R331')
        dicOut = self.coordParse(self.readLine())
        return dicOut

    @deprecated
    def readHeadZ(self):
        """
        Get Board Ref from hardware
        :return dict like this {'Z':-5.5}
        """
        self.__sendGcodeLine('R332')
        dicOut = self.coordParse(self.readLine())
        return dicOut

    def readHardwarePos(self):
        """
        Get Axis position
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C';32.5}
        """
        self.__sendGcodeLine('R114')
        dicOut = self.coordParse(self.readLine())
        return dicOut

    def _getListAvailableFaddress(self):
        """
        Send a feeder scan request to pnp hardware.
        pnp hardwares respond a list of adress available.
        :return array of adress available:
        """
        self.__sendGcodeLine("FA ")
        adrOut = self.readLine().split(' ')
        return adrOut

    @deprecated
    def _getFeederParam(self, address):
        """
        Send a feeder information request to pnp hardware.
        :param address address of the feeder:
        :return an array with parametres of feeder:
        """
        self._GcodeLine = "FG {}".format(address)
        self.__sendGcodeLine()
        dicData = self.coordParse(self.readLine())

        dataFeeder = [dicData['N'], float(dicData['X']), float(dicData['Y']), float(dicData['Z']), int(dicData['S']),
                      int(dicData['C'])]
        return dataFeeder

    @deprecated
    def feederGoTo(self, addr, speed=0):
        """
        Move hardware to feeder postion
        :param addr: string of address
        :return:
        """
        if addr in self.feederList:
            feed = self.feederList[addr]
            if speed != 0:
                self.__setSpeed(speed)
            self.moveZ(feed.zPos + 20)

            self.moveAxis({'X': feed.xPos, 'Y': feed.yPos})
        else:
            self.logger.printCout("FeederGoTo() Error: address {} doesn't exist".format(addr))

    @deprecated
    def feederPickup(self, addr, moveSpeed, speedPick, delay):
        """
        Pickup a component with slsected speed and delay
        :param addr:
        :param speed:
        :param delay in ms:
        :return:
        """
        self.feederGoTo(addr, speed=moveSpeed)
        self.__setSpeed(speedPick)
        self.moveZ(feed.zPos)
        time.sleep(delay / 1000.0)
        self.moveZ(feed.zPos + 20)

    @deprecated
    def feederConfigure(self, addr, feedConf):
        """
        Update local feeder information and sent it to hardware feeder
        :param addr: string of address
        :param feedConf: feeder class wich contain data
        :return:
        """
        if addr in self.feederList:
            self.feederList[addr] = feedConf
            self._GcodeLine = 'FS {} N{} X{} Y{} Z{} S{} C{}'.format(addr, feedConf.name, feedConf.xPos,
                                                                     feedConf.yPos, feedConf.zPos, feedConf.step,
                                                                     feedConf.compByStep)
            self.__sendGcodeLine();
            self.readLine()
        else:
            self.logger.printCout("feederConfigure() Error: address {} doesn't exist".format(addr))

    @deprecated
    def feederFlashSave(self, addr):
        if addr in self.feederList:
            self._GcodeLine = 'FF {}'.format(addr)
            self.__sendGcodeLine()
            self.readLine()
        else:
            self.logger.printCout("feederFlashSave() Error: address {} doesn't exist".format(addr))

    def feederMakeStep(self, addr):
        if addr in self.feederList:
            line = 'FM {}'.format(addr)
            self.__sendGcodeLine(line)
            self.readLine()
        else:
            self.logger.printCout("feederFlashSave() Error: address {} doesn't exist".format(addr))

    @deprecated
    def findFeederAddress(self, name):
        for addr, data in self.feederList.items():
            if data.name == name:
                return addr
        return 0

    @deprecated
    def feederUpdate(self):
        """
        Update the dictionary of feeder.
        :return the dictionary of feeder:
        """
        self.feederList.clear()
        addrList = self._getListAvailableFaddress()
        for addr in addrList:
            paramF = self._getFeederParam(addr)
            self.feederList[addr] = feeder(int(addr), paramF)

        return self.feederList

    def coordParse(self, str):
        """
        Return dict with axis information.
        :param str: X101.5 Y104.5 Z25.2 C-2.4
        :return: {'X':101.5, 'Y':104.5, 'Z':25.2, 'C':-2.4}
        """
        dicOut = {}
        splitList = str.split(' ')
        for word in splitList:
            dicOut[word[0]] = word[2:]

        return dicOut

    def readLine(self, timeOut=1.0):
        """
        Get line from serial buffer
        :param timeOut: timeOut in  S. raise exception if elapsed
        :return: strig of line
        """
        start = time.time()
        loop = True
        while not self.__lineIsPresent():
            # while not self._queue.empty():
            #    self._bufferLineInputPipe0.append(self._queue.get())
            # if self.__lineIsPresent():
            #    loop = False
            # if (time.time() - start) > timeOut:
            if 0:
                raise RuntimeError

                return ""

        self._commadUnackited -= 1
        cmdLine = self.__getLine()
        # print('time = {}'.format(time.time() - start))
        return cmdLine

    def __sendGcodeLine(self, line):
        """
        Send self._GcodeLine over sertial port and clear GcodeLine.
        :return:
        """

        if self.isConnected():
            if line != 'R400':
                self.logger.printDirectConsole('TX: ' + line)
                self.logger.printCout('TX: ' + line)

            self._commadUnackited += 1
            self._serManage.sendLine(line)

            # self._GcodeLine = ''

    def externalGcodeLine(self, cmd):
        self._GcodeLine = cmd
        self.__sendGcodeLine()
