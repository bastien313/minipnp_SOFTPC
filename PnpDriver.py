# coding: utf-8
import threading, queue

import serial
import serial.tools.list_ports
import time
from deprecated import deprecated

from timerThread import Intervallometre


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
        if self._serialAccess.is_open:
            try:
                self.__receive()
                self.__emission()
            except:
                self._logger.printCout('Serial error, close.')
                self._serialAccess.close()
                self._receiveBuffer = ""
        else:
            self.__searchAndConnectDevice()
            time.sleep(0.500)

        time.sleep(0.020)

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
            if 'minipnp' in port.product:
                self._serialAccess.baudrate = 115200
                # self._serialAccess.timeout = None
                try:
                    self._serialAccess.port = port  # this action call .open()
                except:
                    self._serialAccess.close()

    def __emission(self):
        while not self._emissionBufferQueue.empty():
            lineOut = self._queue.get()
            if lineOut[-1] != self._endLineCaracter:
                lineOut += self._endLineCaracter
            self._serialAcces.write(str.encode('utf-8'))

    def __receive(self):
        """
        Called from timer.
        Proces low level recption of serial port.
        :return:
        """
        while not self.killThread:
            if self._serialAcces:
                byteIn = self._serialAcces.read(size=100)
                byteIn = byteIn.decode("utf-8")
                for byte in byteIn:
                    self._receiveBuffer += byte
                    if byte == self._endLineCaracter:
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


class pnpDriver:

    def __init__(self, logger):
        self._relativeMode = 'A'
        # self._bufferLineInputPipe0 = []
        self._speed = 100.0
        self._GcodeLine = ''
        self.logger = logger
        self.feederList = {}
        self._serManage = SerialManager(self.logger)
        self._serManage.setRecpetionPipeCallBack(pipe=0, callback=self.__pipe0DataReception)
        self._serManage.setRecpetionPipeCallBack(pipe=1, callback=self.__pipe1DataReception)
        self.__statusPipeCallBack = lambda: None
        self._commadUnackited = 0  # Number of bomand is unackited
        self._queue = queue.Queue()
        self.status = {'X': '00', 'Y': '00', 'Z': '00', 'C': '00'}

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
            self._GcodeLine += 'G91 '
        else:
            self._GcodeLine += 'G90 '

        self.__sendGcodeLine()
        self.readLine()

    def __setSpeed(self, speed):
        """Add Speed to gcode if needed 'Fxxxx.x' """
        self._GcodeLine += "F{} ".format(float(speed))

    def setAccel(self, accelData):
        """
        Set acceleration
        :param accelData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is accelValue
        :return:
        """
        self._GcodeLine += 'M201 '
        for key, value in accelData.items():
            self._GcodeLine += "{}{} ".format(key, float(value))

        self.__sendGcodeLine()
        self.readLine()

    def setStepConf(self, stepData):
        """
        Set step/mm or step/deg
        :param speedData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is stepValue
        :return:
        """
        self._GcodeLine += 'M92 '
        for key, value in stepData.items():
            self._GcodeLine += "{}{} ".format(key, float(value))

        self.__sendGcodeLine()
        self.readLine()

    def setMaxSpeed(self, speedData):
        """
        Set max speed of axis
        :param speedData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is maxSpeed
        :return:
        """
        self._GcodeLine += 'M203 '
        for key, value in speedData.items():
            self._GcodeLine += "{}{} ".format(key, float(value))

        self.__sendGcodeLine()
        self.readLine()

    def isBusy(self):
        """
        Check if machine if busy.
        :return:
        """
        if not self.isConnected():
            return 1
        self._GcodeLine = 'R400'
        self.__sendGcodeLine()
        line = self.readLine()
        return 1 if line != '0' else 0

    def stopMachine(self):
        """
        Send stop Request
        :return:
        """
        self._GcodeLine = 'S99'
        self.__sendGcodeLine()

    def makeScan(self):
        self._GcodeLine = 'R500'
        self.__sendGcodeLine()
        response = self.readLine()
        return int(response)

    def makeScanLine(self, axis, speed, lengt, nbMesure):
        self._GcodeLine = 'R501 A{} N{} L{} F{}'.format(axis, nbMesure, lengt, speed)
        self.__sendGcodeLine()
        nb = int(self.readLine(timeOut=20))
        arrayOut = []
        for mes in range(nb):
            lineMes = self.readLine().split()
            print(lineMes)
            arrayOut.append((float(lineMes[0]), int(lineMes[1])))
        return arrayOut

    def getPresure(self):
        self._GcodeLine = 'R600'
        self.__sendGcodeLine()
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

    @deprecated
    def setScanRef(self, scanData):
        """
        set scan position refrence of hardware.
        :param scanData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z'.readHardwarePos
        :return:
        """
        self._GcodeLine += 'M330 '
        for key, value in scanData.items():
            self._GcodeLine += "{}{} ".format(key, float(value))
        self.__sendGcodeLine()
        self.readLine()

    @deprecated
    def setBoardRef(self, boardData):
        """
        set board position refrence of hardware.
        :param boardData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z'.
                          Value is maxSpeed
        :return:
        """
        self._GcodeLine += 'M331 '
        for key, value in boardData.items():
            self._GcodeLine += "{}{} ".format(key, float(value))
        self.__sendGcodeLine()
        self.readLine()

    @deprecated
    def setHeadZ(self, zPos):
        """
        set head Z position refrence of hardware.
        :param zPos: Z position of head
        :return:
        """
        self._GcodeLine += "M332 Z{}".format(zPos)
        self.__sendGcodeLine()
        self.readLine()

    def saveFlashConf(self):
        """
        Save setting of hardware in FLASH
        :return:
        """
        self._GcodeLine = 'M500'
        self.__sendGcodeLine()
        self.readLine()

    def moveX(self, value, mode='A', speedMode='P'):
        tabOut = {}
        tabOut['X'] = value
        self.moveAxis(moveData=tabOut, mode=mode, speedMode=speedMode)

    def moveY(self, value, mode='A', speedMode='P'):
        tabOut = {}
        tabOut['Y'] = value
        self.moveAxis(moveData=tabOut, mode=mode, speedMode=speedMode)

    def moveZ(self, value, mode='A', speedMode='P'):
        tabOut = {}
        tabOut['Z'] = value
        self.moveAxis(moveData=tabOut, mode=mode, speedMode=speedMode)

    def moveC(self, value, mode='A', speedMode='P'):
        tabOut = {}
        tabOut['C'] = value
        self.moveAxis(moveData=tabOut, mode=mode, speedMode=speedMode)

    def moveAxis(self, moveData, speed=10, mode='A', speedMode='P'):
        """ moveData must be an dict.
            Key must be 'X' , 'Y, 'Z' or 'C'.
            Value is displacement
            Mode is the mode of displacement, 'A' = absolute, 'R'= relative
            Speed must be 'P' for (parametric speed)G1 or 'H' (Hight speed)G0"""

        self.__setCoordMode(mode)

        if speedMode == 'P':
            self._GcodeLine += 'G1 '
        else:
            self._GcodeLine += 'G0 '

        self.__setSpeed(speed)

        for key, value in moveData.items():
            self._GcodeLine += "{}{} ".format(key, float(value))

        self.__sendGcodeLine()

        # return self.readLine(20)

    def stopAxis(self, axis):
        """
        Send stop function.
        :param axis: must contain 'ALL' or 'X' or 'Y' or 'Z' or 'C' or composition of axis ex('XYC'):
        :return:
        """
        axis = axis.upper()
        self._GcodeLine = 'S99 '
        if axis != 'ALL':
            if axis.find('X') >= 0:
                self._GcodeLine += 'X '
            if axis.find('Y') >= 0:
                self._GcodeLine += 'Y '
            if axis.find('Z') >= 0:
                self._GcodeLine += 'Z '
            if axis.find('C') >= 0:
                self._GcodeLine += 'C'
        self.__sendGcodeLine()

    def motorEnable(self):
        """
        Enable driver motor.
        :return:
        """
        self._GcodeLine = 'S11'
        self.__sendGcodeLine()

    def motorDisable(self):
        """
        Enable driver motor.
        :return:
        """
        self._GcodeLine = 'S00'
        self.__sendGcodeLine()

    def watchDogEnable(self):
        """
        Enable Watchdog mode, if enable the program must feed the watchdog formotor move.
        :return:
        """
        self._GcodeLine = 'S21'
        self.__sendGcodeLine()

    def watchDogDisable(self):
        """
        Disable Watchdog mode.
        :return:
        """
        self._GcodeLine = 'S20'
        self.__sendGcodeLine()

    def watchDogFeed(self):
        """
        Disable Watchdog mode.
        :return:
        """
        self._GcodeLine = 'S22'
        self.__sendGcodeLine()

    def statusModeEnable(self):
        """
        Enable status mode, machine will send status data over pipe 1 at 400ms.
        :return:
        """
        self._GcodeLine = 'S31'
        self.__sendGcodeLine()

    def statusModeDisable(self):
        """
        Disable status mode.
        :return:
        """
        self._GcodeLine = 'S30'
        self.__sendGcodeLine()

    def homeAxis(self, axis):
        """
        Send home function.
        :param axis must contain 'ALL' or 'X' or 'Y' or 'Z' or 'C' or composition of axis ex('XYC'):
        :return:
        """
        self._GcodeLine += 'G28 '
        if axis != 'ALL':
            if axis.find('X') >= 0:
                self._GcodeLine += 'X '
            if axis.find('Y') >= 0:
                self._GcodeLine += 'Y '
            if axis.find('Z') >= 0:
                self._GcodeLine += 'Z '
            if axis.find('C') >= 0:
                self._GcodeLine += 'C'

        self.__sendGcodeLine()

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
            self._GcodeLine += 'M64 {}'.format(line)
        else:
            self._GcodeLine += 'M65 {}'.format(line)

        self.__sendGcodeLine()

    @deprecated
    def readConf(self):
        """
        Return all configuration  of hardware exept feeder.
        :return: A dict wich this key ('ACCEL', 'MAXSPEED', 'STEPBYMM', 'SCANREF', 'BOARDREF', 'HEADREF')
        """
        dicOut = {}
        dicOut['ACCEL'] = self.readAccel()
        dicOut['MAXSPEED'] = self.readMaxSpeed()
        dicOut['STEPBYMM'] = self.readStepConf()
        dicOut['SCANREF'] = self.readScanRef()
        dicOut['BOARDREF'] = self.readBoardRef()
        dicOut['HEADREF'] = self.readHeadZ()

        return dicOut

    def readAccel(self):
        """
        Get acceleration from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        dicOut = {}
        self._GcodeLine = 'R201'
        self.__sendGcodeLine()
        dicOut = self.coordParse(self.readLine())
        return dicOut

    def readStepConf(self):
        """
        Get step/mm from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        dicOut = {}
        self._GcodeLine = 'R92'
        self.__sendGcodeLine()
        dicOut = self.coordParse(self.readLine())
        return dicOut

    def readMaxSpeed(self):
        """
        Get maxSpeed from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C':250.4}
        """
        dicOut = {}
        self._GcodeLine = 'R203'
        self.__sendGcodeLine()
        dicOut = self.coordParse(self.readLine())
        return dicOut

    @deprecated
    def readScanRef(self):
        """
        Get ScanRef from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5}
        """
        dicOut = {}
        self._GcodeLine = 'R330'
        self.__sendGcodeLine()
        dicOut = self.coordParse(self.readLine())
        return dicOut

    @deprecated
    def readBoardRef(self):
        """
        Get Board Ref from hardware
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5}
        """
        dicOut = {}
        self._GcodeLine = 'R331'
        self.__sendGcodeLine()
        dicOut = self.coordParse(self.readLine())
        return dicOut

    @deprecated
    def readHeadZ(self):
        """
        Get Board Ref from hardware
        :return dict like this {'Z':-5.5}
        """
        dicOut = {}
        self._GcodeLine = 'R332'
        self.__sendGcodeLine()
        dicOut = self.coordParse(self.readLine())
        return dicOut

    def readHardwarePos(self):
        """
        Get Axis position
        :return dict like this {'X':2.4, 'Y':1.2, 'Z':-5.5, 'C';32.5}
        """
        dicOut = {}
        self._GcodeLine = 'R114'
        self.__sendGcodeLine()
        dicOut = self.coordParse(self.readLine())
        return dicOut

    def _getListAvailableFaddress(self):
        """
        Send a feeder scan request to pnp hardware.
        pnp hardwares respond a list of adress available.
        :return array of adress available:
        """

        self._GcodeLine = "FA "
        self.__sendGcodeLine()
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
        return dataFeeder;

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
            self._GcodeLine = 'FM {}'.format(addr)
            self.__sendGcodeLine()
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
        return cmdLine

    def __sendGcodeLine(self):
        """
        Send self._GcodeLine over sertial port and clear GcodeLine.
        :return:
        """
        if self.isConnected():
            if self._GcodeLine != 'R400':
                self.logger.printDirectConsole('TX: ' + self._GcodeLine)
                self.logger.printCout('TX: ' + self._GcodeLine)

            self._commadUnackited += 1
            self._serManage.sendLine(self._GcodeLine)

            self._GcodeLine = ''

    def externalGcodeLine(self, cmd):
        self._GcodeLine = cmd
        self.__sendGcodeLine()
