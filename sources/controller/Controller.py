# coding: utf-8
import time

from database import Board as brd, database as dtb
from . import Prefrence as pr
from machine import machine as mch
from deprecated import deprecated
from . import job
from utils import Gamepad as gp


class ParamCtrl:
    def __init__(self, driver, machineConf):
        self.ihm = None
        self._driver = driver
        self._machineConf = machineConf

    @deprecated
    def setAccel(self, accelData):
        """
        Set acceleration in machine conf and sent it to hardware
        :param accelData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is accelValue
        :return:
        """
        self._machineConf.setAccel(accelData)
        self._driver.setAccel(accelData)

    @deprecated
    def setStepConf(self, stepData):
        """
        Set axis step in machine conf and sent it to hardware
        :param stepData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is stepData
        :return:
        """
        self._machineConf.setStep(stepData)
        self._driver.setStepConf(stepData)

    @deprecated
    def setMaxSpeed(self, speedData):
        """
        Set maximum speed of axis in machine conf and sent it to hardware
        :param speedData: dict wich contain maxSpeed for axis
                          Key must be 'X' , 'Y, 'Z' or 'C'.
                          Value is accelValue
        :return:
        """
        self._machineConf.setSpeed(speedData)
        self._driver.setMaxSpeed(speedData)

    @deprecated
    def setScanRef(self, scanData):
        """
        Set scan referance position in machine conf.
        :param scanData: {'X': scanXpos, 'Y':scanYpos, 'Z':scanZpos}
        :return:
        """
        self._machineConf.scanPosition = scanData

    @deprecated
    def setBoardRef(self, boardData):
        """
        Set board referance position in machine conf.
        :param boardData: {'X': boardXpos, 'Y':boardYpos, 'Z':boardZpos}
        :return:
        """
        self._machineConf.boardRefPosition = boardData

    @deprecated
    def setTrashRef(self, trashPos):
        """
        Set trash referance position in machine conf.
        :param trashPos: {'X': trashXpos, 'Y':trashYpos, 'Z':trashZpos}
        :return:
        """
        self._machineConf.trashPosRefPosition = trashPos

    @deprecated
    def setHeadZ(self, zPos):
        """
        Set z head in machine conf.
        :param zPos: float
        :return:
        """
        self._machineConf.zHead = zPos

    @deprecated
    def readConf(self):
        """
        Return all configuration  of hardware exept feeder.
        :return: A dict wich this key ('ACCEL', 'MAXSPEED', 'STEPBYMM', 'SCANREF', 'BOARDREF', 'HEADREF')
        """
        return {'ACCEL': self._machineConf.getAxisAccel(), 'MAXSPEED': self._machineConf.getAxisSpeed(),
                'STEPBYMM': self._machineConf.getAxisStep(), 'SCANREF': self._machineConf.scanPosition,
                'BOARDREF': self._machineConf.boardRefPosition, 'HEADREF': self.zHead,
                'TRASHREF': self.trashRefPosition}

    def saveFlashConf(self):
        self._driver.saveFlashConf()

    def sefConfInFile(self):
        self._machineConf.saveToXml()


class DirectCtrl:
    def __init__(self, driver, machineConf):
        self.ihm = 0
        self._driver = driver
        self._machineConf = machineConf
        self._jobRunningCb = lambda: 1
        self._feedRequest = {'X': False, 'Y': False, 'Z': False, 'C': False}

    def IHMposUpdate(self, positionString):
        # coord = self._driver.coordParse(positionString)
        self.ihm.posX = float(positionString['X'][1:])
        self.ihm.posY = float(positionString['Y'][1:])
        self.ihm.posZ = float(positionString['Z'][1:])
        self.ihm.posC = float(positionString['C'][1:])

    def setJobIsRunningCb(self, cb):
        self._jobRunningCb = cb

    def watchDogFeed(self):
        if self._feedRequest['X'] or self._feedRequest['Y'] or self._feedRequest['Z'] or self._feedRequest['C']:
            self._driver.watchDogFeed()
            self.ihm.after(100, self.watchDogFeed)

    def move(self, axis, dist, invert=False):
        if not self._jobRunningCb():
            if self.ihm.getContinueState():
                self._driver.watchDogEnable()
                dist *= -1.0 if invert else 1.0
                self._feedRequest[axis] = True
                self._driver.moveAxis(moveData={axis: dist}, mode='R', speedMode='H',
                                      speed=self._machineConf.axisConfArray[axis].speed)
                self.ihm.after(100, self.watchDogFeed)
            else:
                if not self._driver.isBusy():
                    self._driver.watchDogDisable()
                    dist *= -1.0 if invert else 1.0
                    self._driver.moveAxis(moveData={axis: dist}, mode='R', speedMode='H',
                                          speed=self._machineConf.axisConfArray[axis].speed)

    def xpPress(self, *args):
        self.move(axis='X', dist=9999999.0 if self.ihm.getContinueState() else self.ihm.stepX, invert=False)

    def xmPress(self, *args):
        self.move(axis='X', dist=9999999.0 if self.ihm.getContinueState() else self.ihm.stepX, invert=True)

    def xRelease(self, *args):
        if not self._jobRunningCb():
            if self.ihm.getContinueState() and self._feedRequest['X']:
                self._driver.stopAxis('X')
                self._feedRequest['X'] = False

    def ypPress(self, *args):
        self.move(axis='Y', dist=9999999.0 if self.ihm.getContinueState() else self.ihm.stepY, invert=False)

    def ymPress(self, *args):
        self.move(axis='Y', dist=9999999.0 if self.ihm.getContinueState() else self.ihm.stepY, invert=True)

    def yRelease(self, *args):
        if not self._jobRunningCb():
            if self.ihm.getContinueState() and self._feedRequest['Y']:
                self._driver.stopAxis('Y')
                self._feedRequest['Y'] = False

    def zpPress(self, *args):
        self.move(axis='Z', dist=9999999.0 if self.ihm.getContinueState() else self.ihm.stepZ, invert=False)

    def zmPress(self, *args):
        self.move(axis='Z', dist=9999999.0 if self.ihm.getContinueState() else self.ihm.stepZ, invert=True)

    def zRelease(self, *args):
        if not self._jobRunningCb():
            if self.ihm.getContinueState() and self._feedRequest['Z']:
                self._driver.stopAxis('Z')
                self._feedRequest['Z'] = False

    def cpPress(self, *args):
        self.move(axis='C', dist=9999999.0 if self.ihm.getContinueState() else self.ihm.stepC, invert=False)

    def cmPress(self, *args):
        self.move(axis='C', dist=9999999.0 if self.ihm.getContinueState() else self.ihm.stepC, invert=True)

    def cRelease(self, *args):
        if not self._jobRunningCb():
            if self.ihm.getContinueState() and self._feedRequest['C']:
                self._driver.stopAxis('C')
                self._feedRequest['C'] = False

    def stepIncrement(self):
        """
        Set all step to preprogrmed value [100,10,1,0.1,0.01]
        """
        stepAxisDict = self.ihm.getStepAxis()
        if stepAxisDict['X'] < 0.1:
            newVal = 0.1
        elif stepAxisDict['X'] < 1.0:
            newVal = 1.0
        elif stepAxisDict['X'] < 10.0:
            newVal = 10.0
        else:
            newVal = 100.0
        self.ihm.setStepAxis({'X': newVal, 'Y': newVal, 'Z': newVal, 'C': newVal})

    def stepDecrement(self):
        """
        Set all step to preprogrmed value [100,10,1,0.1,0.01]
        """
        stepAxisDict = self.ihm.getStepAxis()
        if stepAxisDict['X'] > 99:
            newVal = 10.0
        elif stepAxisDict['X'] > 9:
            newVal = 1.0
        elif stepAxisDict['X'] > 0.9:
            newVal = 0.1
        else:
            newVal = 0.01
        self.ihm.setStepAxis({'X': newVal, 'Y': newVal, 'Z': newVal, 'C': newVal})

    def homeAll(self):
        if not self._jobRunningCb():
            self._driver.homeAxis('ALL')

    def homeX(self):
        if not self._jobRunningCb():
            self._driver.homeAxis('X')

    def homeY(self):
        if not self._jobRunningCb():
            self._driver.homeAxis('Y')

    def homeZ(self):
        if not self._jobRunningCb():
            self._driver.homeAxis('Z')

    def homeC(self):
        if not self._jobRunningCb():
            self._driver.homeAxis('C')

    def evControl(self):
        if not self._jobRunningCb():
            self._driver.ctrlEv(self.ihm.evState)

    def pumpControl(self):
        if not self._jobRunningCb():
            self._driver.ctrlPump(self.ihm.pumpState)

    def continueControl(self):
        if not self._jobRunningCb():
            self._driver.watchDogEnable() if self.ihm.getContinueState() else self._driver.watchDogDisable()

    def stepFeederRequest(self):
        """
        Caled by ihm button step.
        Produce a step to feeder selected.
        :return:
        """
        self._driver.feederMakeStep(self.ihm.feederChoice)

    def getCoordDriver(self):
        return self._driver.getHardwarePos()

    def motorOn(self):
        if self._driver.isConnected():
            # self._driver.statusModeDisable()
            self._driver.sendMachineConf(self._machineConf)
            self._driver.statusModeEnable()
            # self._driver.setMaxSpeed()
            # self._driver.setStepConf()
            # self._driver.setAccel()
            self._driver.motorEnable()

    def motorOff(self):
        if self._driver.isConnected():
            self._driver.motorDisable()
            self._driver.statusModeDisable()


class BoardController:
    def __init__(self, driver, logger, modelList, machineConf, parameters):
        self.ihm = 0
        self.driver = driver
        self.board = 0
        self.logger = logger
        self.enableSaveFunc = 0
        self.modList = modelList
        self.__machineConf = machineConf
        self._parameters = parameters
        self.__littleJob = job.ThreadJobExecutor()
        self.__longJob = job.ThreadJobExecutor()
        self._jobLastUsedRefList = None

    def panelizeBoard(self, countX, countY, offsetX, offsetY):
        self.board.panelize(countX, countY, offsetX, offsetY)
        self.ihm.bomCreate(self.board)

    def boardRotation(self, rotation):
        self.board.boardRotation(rotation)
        self.ihm.bomCreate(self.board)

    def boardVerticalMirror(self):
        self.board.verticalMirror()
        self.ihm.bomCreate(self.board)

    def boardHorizontalMirror(self):
        self.board.horizontalMirror()
        self.ihm.bomCreate(self.board)

    def initIHMcallBack(self):
        self.ihm.jobFrame.setBuildCallBack(self.buildLongJob)
        self.ihm.jobFrame.setStopCallBack(self.stopJob)
        self.ihm.jobFrame.setPauseCallBack(self.pauseJob)
        self.ihm.jobFrame.setPlayCallBack(self.startLongJob)

        self.ihm.jobFrame.playButtonState(0)
        self.ihm.jobFrame.pauseButtonState(0)
        self.ihm.jobFrame.stopButtonState(0)
        self.ihm.jobFrame.buildButtonState(1)

    def createFromCsv(self, name, pathFile, separator, startLine, dicConf):
        self.board = brd.Board(name, self.logger)

        f = open(pathFile, "r")
        self.board.importFromCSV(f, separator, startLine, dicConf)
        f.close()
        # self.board.assosciateCmpModel(self.modList)
        self.ihm.setboardParam(self.board)
        self.ihm.bomCreate(self.board)
        self.enableSaveFunc('normal')
        # self.initIHMcallBack()

        self.logger.printCout(self.board.__str__())

    def changeAndLoadMachineConf(self, pathFile):
        # Modify path of machine conf only if there is no error
        self.__machineConf.loadFromXml(pathFile)
        self.board.tableTopPath = self.__machineConf.pathFile

        if self.driver.isConnected():
            self.driver.sendMachineConf(self.__machineConf)

    def importFromXml(self, path):
        self.board = dtb.boarLoad(path, self.logger)
        self.ihm.setboardParam(self.board)
        self.ihm.bomCreate(self.board)
        self.enableSaveFunc('normal')
        self.initIHMcallBack()

        if len(self.board.tableTopPath):
            self.changeAndLoadMachineConf(self.board.tableTopPath)

        self.logger.printCout(self.board.__str__())

    def saveBoard(self):
        self.board.save()

    def saveAsBoard(self, path):
        self.board.saveAs(path)

    def __longjobError(self, status):
        self.logger.printCout('Long job error: ' + self.__longJob.getStateDescription())
        # self.pauseJob() // reactivate when restar work
        self.stopJob()

        if int(self._parameters['JOB']['errorManagement']) == 0:
            #One error mode, we stop on first error
            for loop in range(5):
                self.driver.ctrlPump(0)
                self.driver.ctrlEv(0)
                time.sleep(0.500)
                self.driver.ctrlPump(1)
                self.driver.ctrlEv(1)
                time.sleep(0.500)
            self.driver.ctrlPump(0)
            self.driver.ctrlEv(0)
        elif int(self._parameters['JOB']['errorManagement']) == 1:
            # One feeder three error or all feeder three error.
            # We try to rebuild and relunch if succes.
            for loop in range(2):
                self.driver.ctrlPump(0)
                self.driver.ctrlEv(0)
                time.sleep(0.500)
                self.driver.ctrlPump(1)
                self.driver.ctrlEv(1)
                time.sleep(0.500)
            self.driver.ctrlPump(0)
            self.driver.ctrlEv(0)
            if self.buildLongJob(self._jobLastUsedRefList):
                self.startLongJob()

    def __endLongJob(self, status):
        self.logger.printCout('Long job End: ' + self.__longJob.getStateDescription())
        self.stopJob()

    def __littlejobError(self, status):
        self.logger.printCout('Little job error: ' + self.__littleJob.getStateDescription())
        # self.pauseJob() // reactivate when restar work
        self.stopJob()
        for loop in range(5):
            self.driver.ctrlPump(0)
            self.driver.ctrlEv(0)
            time.sleep(500)
            self.driver.ctrlPump(1)
            self.driver.ctrlEv(1)
            time.sleep(500)
        self.driver.ctrlPump(0)
        self.driver.ctrlEv(0)

    def __endLittleJob(self, status):
        self.logger.printCout('Little job End: ' + self.__littleJob.getStateDescription())
        self.stopJob()

    def __jobNotify(self, str):
        self.ihm.jobFrame.jobDescription(str)
        self.logger.printCout('Job: ' + str)

    def _displayFeederError(self):
        strError = ''

        for feeder in self.__machineConf.feederList:
            if feeder.isInError():
                strError += f'{feeder.id}, '

        if len(strError):
            strError = 'Feeder error: ' + strError

        self.ihm.jobFrame.jobDescription(strError)

    def buildLongJob(self, refList=None):
        """p²
        Build long job and unluck button play and stop.
        :return:
        """
        if not refList:
            refList = [cmp.ref for cmp in self.ihm.rootCmpFrame.cmpDisplayList]
        self._jobLastUsedRefList = refList
        longJob = job.Job(name='Standard Long job')
        cmpNumber = int(self._parameters['JOB']['homeCmpCount'])
        for cmp in self.board.values():
            if cmp.isEnable and not cmp.isPlaced and cmp.ref in refList:
                cmpJob = self.__buildPickAndPlaceJob(cmp.ref)
                if cmpJob:
                    print(cmp.ref)
                    cmpJob.append(job.ExternalCallTask(callBack=self.__isPlacedCallBack, param=cmp.ref,
                                                       name='Is placed callBack'))
                    cmpJob.jobConfigure()
                    longJob.append(cmpJob)
                    cmpNumber -= 1
                    if not cmpNumber:
                        longJob.append(job.HomingTask(pnpDriver=self.driver, name='Homing'))
                        cmpNumber = int(self._parameters['JOB']['homeCmpCount'])
                else:
                    if int(self._parameters['JOB']['errorManagement']) != 2:
                        #One feeder one  error mode or one feeder three error mode, unbuild if an error occured.
                        self.ihm.jobFrame.playButtonState(0)
                        self.ihm.jobFrame.stopButtonState(0)
                        self._displayFeederError()
                        self.logger.printCout("Build Error.")
                        return 0


        longJob.append(job.HomingTask(pnpDriver=self.driver, name='Homing'))
        longJob.jobConfigure()
        # print(longJob)
        self.logger.printCout("Build compleete.")
        self.__longJob = job.ThreadJobExecutor(job=longJob, driver=self.driver,
                                               errorFunc=self.__longjobError, endFunc=self.__endLongJob,
                                               notifyFunc=self.__jobNotify)
        self.ihm.jobFrame.playButtonState(1)
        self.ihm.jobFrame.stopButtonState(1)
        self.ihm.jobFrame.jobDescription(self.__longJob.getStateDescription())
        self._displayFeederError()
        return 1

    def stopJob(self):
        self.ihm.rootCmpFrame.enableComponentButton()
        if self.__longJob.is_alive():
            self.__longJob.stop()
            self.ihm.jobFrame.jobDescription('Long job stopped.')
        if self.__littleJob.is_alive():
            self.__littleJob.stop()
            self.ihm.jobFrame.jobDescription('Little job stopped.')

        self.ihm.jobFrame.playButtonState(0)
        self.ihm.jobFrame.stopButtonState(0)
        self.ihm.jobFrame.pauseButtonState(0)
        self.ihm.jobFrame.buildButtonState(1)
        self.ihm.jobFrame.jobDescription('')

    def startLongJob(self):
        self.ihm.rootCmpFrame.disableComponentButton()
        self.ihm.jobFrame.playButtonState(0)
        self.ihm.jobFrame.stopButtonState(1)
        self.ihm.jobFrame.pauseButtonState(1)
        self.ihm.jobFrame.buildButtonState(0)
        if self.__longJob.is_alive():
            self.__longJob.unPause()
        else:
            self.__longJob.start()

    def __startLittleJob(self):
        self.ihm.rootCmpFrame.disableComponentButton()
        self.ihm.jobFrame.playButtonState(0)
        self.ihm.jobFrame.stopButtonState(1)
        self.ihm.jobFrame.pauseButtonState(0)
        self.ihm.jobFrame.buildButtonState(0)
        self.__littleJob.start()

    def pauseJob(self):
        if self.__littleJob.is_alive():
            self.__littleJob.stop()

        if self.__longJob.is_alive():
            self.__longJob.pause()
            self.ihm.jobFrame.jobDescription(self.__longJob.getStateDescription())
            self.ihm.jobFrame.playButtonState(1)
            self.ihm.jobFrame.pauseButtonState(0)
            self.ihm.jobFrame.stopButtonState(1)
            self.ihm.jobFrame.buildButtonState(0)
        else:
            self.ihm.jobFrame.jobDescription('Little job stopped.')
            self.ihm.jobFrame.playButtonState(0)
            self.ihm.jobFrame.stopButtonState(0)
            self.ihm.jobFrame.pauseButtonState(0)
            self.ihm.jobFrame.buildButtonState(1)

    def jobIsRunning(self):
        if self.__littleJob.is_alive():
            if self.__littleJob.status.status == job.TaskStatusEnum.RUN:
                return 1
        if self.__longJob.is_alive():
            if self.__longJob.status.status == job.TaskStatusEnum.RUN:
                return 1
        return 0

    def __isPlacedCallBack(self, ref):
        """
        Called by job when a component is placed
        :param ref:
        :return:
        """
        self.board[ref].isPlaced = 1
        self.logger.printCout('{} is placed'.format(ref))
        self.ihm.cmpHaveChanged(ref)
        self.saveBoard()
        # self.ihm.componentUpdate()

    def __buildPickAndPlaceJob(self, ref):
        """
        Build a job for pick and place component.
        :param ref:
        :return: new job created
        """
        if ref not in self.board:
            self.logger.printCout("Ref {} is not on board".format(ref))
            return 0

        if self.board[ref].model == 'Null':
            self.logger.printCout("Ref {} doesn't have model".format(ref))
            return 0

        if self.board[ref].feeder == 'Null':
            self.logger.printCout("Ref {} doesn't have feeder".format(ref))
            return 0

        feeder = self.__machineConf.getFeederById(int(self.board[ref].feeder))

        if feeder.isInError():
            self.logger.printCout("Ref {}, feeder {} is in error".format(ref, feeder.id))
            return 0

        model = self.modList[self.modList.findModelWithAlias(self.board[ref].model)]


        cmpPos = self.board.getMachineCmpPos(ref)
        # cmpPos['Z'] = self.__machineConf.boardRefPosition['Z'] + model.height
        cmpJob = job.PickAndPlaceJob(pnpDriver=self.driver, feeder=feeder,
                                     placePos=cmpPos, model=model, zLift=self.__machineConf.zLift,
                                     name='Pick and place {}'.format(ref), correctorPos=self.__machineConf.scanPosition)
        cmpJob.jobConfigure()
        # self.logger.printCout("Build {} succes.".format(ref))
        return cmpJob

    def pickAndPlaceCmp(self, ref):
        """
        Build a pick and place job and lunch it.
        :param ref:
        :return:
        """
        if self.__littleJob.isRunning():
            self.logger.printCout("LitTle job already running")
            return 0

        if self.__longJob.isRunning():
            self.logger.printCout("Long job already running")
            return 0

        cmpJob = self.__buildPickAndPlaceJob(ref)
        if not cmpJob:
            return 0

        self.__littleJob = job.ThreadJobExecutor(cmpJob, self.__jobNotify, self.__littlejobError, self.__endLittleJob)
        self.__startLittleJob()

    def goToCmp(self, ref):
        """
        Go to XY component place.
        BEWARE this fuction does not manage Z lift.
        :param ref:
        :return:
        """
        if ref not in self.board:
            self.logger.printCout("Ref {} is not on board".format(ref))
            return 0

        cmpPos = self.board.getMachineCmpPos(ref)

        # Build job.
        goToJob = job.Job(self.driver)
        goToJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        goToJob.append(job.MoveTask(self.driver, {'X': cmpPos['X'], 'Y': cmpPos['Y']},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        goToJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.boardRefPosition['Z'] + 1},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        goToJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        if self.__longJob.isRunning():
            self.logger.printCout("Long job already running")
            return 0

        # Run job
        if self.driver.isConnected():
            self.__littleJob = job.ThreadJobExecutor(goToJob, errorFunc=self.__littlejobError,
                                                     endFunc=self.__endLittleJob)
            self.__littleJob.start()

    def goTo(self, posData):
        goToJob = job.Job(self.driver)
        goToJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        goToJob.append(job.MoveTask(self.driver, {'X': posData['X'], 'Y': posData['Y']},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        goToJob.append(
            job.MoveTask(self.driver, {'Z': posData['Z']}, speed=self.__machineConf.axisConfArray['Z'].speed))

        goToJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        if self.__longJob.isRunning():
            self.logger.printCout("Long job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=goToJob, errorFunc=self.__littlejobError,
                                                 endFunc=self.__endLittleJob,
                                                 driver=self.driver)
        self.__startLittleJob()

    def goToFeeder(self, idFeed, idCmp):
        feeder = self.__machineConf.getFeederById(idFeed)
        # Get position of board origin
        # boardOrigin = self.driver.readBoardRef()

        # print(feeder.getPositionById(cmpId=idCmp,stripId=idStrip))
        # Build job.
        cmpPos = feeder.getPositionById(idCmp)
        goToJob = job.Job(self.driver)
        goToJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        goToJob.append(job.MoveTask(self.driver, {'X': cmpPos['X'], 'Y': cmpPos['Y']},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        goToJob.append(
            job.MoveTask(self.driver, {'Z': cmpPos['Z'] + 1}, speed=self.__machineConf.axisConfArray['Z'].speed))
        goToJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        if self.__longJob.isRunning():
            self.logger.printCout("Long job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=goToJob, errorFunc=self.__littlejobError,
                                                 endFunc=self.__endLittleJob,
                                                 driver=self.driver)
        self.__startLittleJob()


class DtbController:
    def __init__(self, logger, modList):
        self.ihm = 0
        self.logger = logger
        self.modList = modList

    def saveInFile(self):
        self.modList.saveFile()

    def makeNewModel(self, strmod):
        self.modList.makeNewModel(strmod)


class ScanController:
    def __init__(self, logger, driver, machine, modelList):
        self.ihm = 0
        self.logger = logger
        self.driver = driver
        self.__machineConf = machine
        self.__scanArray = []
        self.__littleJob = job.ThreadJobExecutor()
        self.__scanXWidth = 20.0
        self.__scanYWidth = 4.0
        self.__scanZWidth = 5
        self.__scanCircleWidth = 360.0
        self.__scanLineXPoint = 200
        self.__scanLineYPoint = 20
        self.__scanLineZPoint = 40
        self.__scanCirclePoint = 360
        self.modList = modelList

    def testCorrector(self):
        model = self.modList[self.modList.findModelWithAlias('C_0402')]
        corrJob = job.MechanicsCorrectorJob(pnpDriver=self.driver, correctorPos=self.__machineConf.scanPosition,
                                            model=model, zLift=self.__machineConf.zLift)

        corrJob.jobConfigure()
        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=corrJob, driver=self.driver)
        self.__littleJob.start()

    def linkCallBack(self, ihm):
        self.ihm = ihm
        self.ihm.setScan3Dcb(self.testCorrector)
        self.ihm.setScanXLinecb(self._scanXLine)
        self.ihm.setScanYLinecb(self._scanYLine)
        self.ihm.setScanPointcb(self._scanPoint)
        self.ihm.setGoTOcb(self._goTo)
        self.ihm.setScanFacecb(self._scanFace)
        self.ihm.setScanCirclecb(self._scanCircle)

    def _goTo(self):
        goToJob = job.Job(self.driver)
        goToJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        goToJob.append(job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'],
                                                  'Y': self.__machineConf.scanPosition['Y']},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        goToJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan()},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        goToJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=goToJob, driver=self.driver)
        self.__littleJob.start()

    def _scanPoint(self):
        self.__scanArray = []
        scanJob = job.Job(self.driver)
        # scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
        #                             speed=self.__machineConf.axisConfArray['Z'].speed))
        # scanJob.append(job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'],
        #                                           'Y': self.__machineConf.scanPosition['Y']},
        #                             speed=self.__machineConf.axisConfArray['X'].speed))
        # scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan()},
        #                             speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(job.WaitTask(0.1))
        scanJob.append(job.ScanTask(pnpDriver=self.driver, extList=self.__scanArray))
        scanJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=scanJob, driver=self.driver,
                                                 endFunc=lambda x: self.ihm.setMeasureValue(self.__scanArray[0]))
        self.__littleJob.start()

    def _endScanCircle_old(self, stat):
        with open('circle.csv', 'w+') as file:
            # angle = 0.0
            for scanData in self.__scanArray[0]:
                # for scanData in self.__scanArray:
                file.write('{} {}\n'.format(scanData[0], scanData[1]))
                # angle += self.__scanCircleWidth / self.__scanCirclePoint
                # file.write('{} {}\n'.format(angle, scanData))

    def _scanCircle_old(self):
        self.__scanArray = []
        scanJob = job.Job(self.driver)
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'],
                                                  'Y': self.__machineConf.scanPosition['Y']},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan()},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))

        scanJob.append(job.MoveTask(self.driver, {'C': (0 - self.__scanCircleWidth / 2.0)}, coordMode='R',
                                    speed=self.__machineConf.axisConfArray['C'].speed))

        scanJob.append(
            job.ScanLineTask(pnpDriver=self.driver, extList=self.__scanArray, axis='C', lengt=self.__scanCircleWidth,
                             nbMesure=self.__scanCirclePoint, speed=self.__machineConf.axisConfArray['C'].speed))

        scanJob.append(job.MoveTask(self.driver, {'C': (0 - self.__scanCircleWidth)}, coordMode='R',
                                    speed=self.__machineConf.axisConfArray['C'].speed))

        scanJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=scanJob, driver=self.driver, endFunc=self._endScanCircle)
        self.__littleJob.start()

    def _endScanCircle(self, stat):
        with open('circle.csv', 'w+') as file:
            angle = 0.0
            for scanData in self.__scanArray:
                # for scanData in self.__scanArray:
                # file.write('{} {}\n'.format(scanData[0], scanData[1]))
                angle += self.__scanCircleWidth / self.__scanCirclePoint
                file.write('{} {}\n'.format(angle, scanData))

    def _scanCircle(self):
        self.__scanArray = []
        scanJob = job.Job(self.driver)
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'],
                                                  'Y': self.__machineConf.scanPosition['Y']},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan()},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))

        scanJob.append(job.MoveTask(self.driver, {'C': (0 - self.__scanCircleWidth / 2.0)}, coordMode='R',
                                    speed=self.__machineConf.axisConfArray['C'].speed))

        for i in range(self.__scanCirclePoint):
            scanJob.append(
                job.MoveTask(self.driver, {'C': self.__scanCircleWidth / self.__scanCirclePoint}, coordMode='R',
                             speed=self.__machineConf.axisConfArray['C'].speed))
            scanJob.append(job.WaitTask(0.01))
            scanJob.append(job.ScanTask(pnpDriver=self.driver, extList=self.__scanArray))

        scanJob.append(job.MoveTask(self.driver, {'C': (0 - self.__scanCircleWidth)}, coordMode='R',
                                    speed=self.__machineConf.axisConfArray['C'].speed))

        scanJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=scanJob, driver=self.driver, endFunc=self._endScanCircle)
        self.__littleJob.start()

    def _endScanXLine(self, stat):
        with open('Xline.csv', 'w+') as file:
            # posy = 0 - self.__scanYWidth / 2.0
            for scanData in self.__scanArray[0]:
                file.write('{} {}\n'.format(scanData[0], scanData[1]))
                # posy += self.__scanYWidth / self.__scanLinePoint

    def _scanXLine(self):
        self.__scanArray = []
        scanJob = job.Job(self.driver)
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(
            job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'] + (0 - self.__scanXWidth / 2.0),
                                       'Y': self.__machineConf.scanPosition['Y']},
                         speed=self.__machineConf.axisConfArray['X'].speed))
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan()},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(
            job.ScanLineTask(pnpDriver=self.driver, extList=self.__scanArray, axis='X',
                             lengt=self.__scanXWidth,
                             nbMesure=self.__scanLineXPoint, speed=self.__machineConf.axisConfArray['X'].speed))

        scanJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=scanJob, driver=self.driver, endFunc=self._endScanXLine)
        self.__littleJob.start()

    def _endScanYLine(self, stat):
        with open('Yline.csv', 'w+') as file:
            # posy = 0 - self.__scanYWidth / 2.0
            for scanData in self.__scanArray[0]:
                file.write('{} {}\n'.format(scanData[0], scanData[1]))
                # posy += self.__scanYWidth / self.__scanLinePoint

    def _scanYLine(self):
        self.__scanArray = []
        scanJob = job.Job(self.driver)
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'],
                                                  'Y': self.__machineConf.scanPosition['Y'] + (
                                                          0 - self.__scanYWidth / 2.0)},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan()},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))

        scanJob.append(
            job.ScanLineTask(pnpDriver=self.driver, extList=self.__scanArray, axis='Y',
                             lengt=self.__scanYWidth,
                             nbMesure=self.__scanLineYPoint, speed=self.__machineConf.axisConfArray['Y'].speed))

        scanJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=scanJob, driver=self.driver, endFunc=self._endScanYLine)
        self.__littleJob.start()

    def _endScanFace(self, stat):
        with open('face.asc', 'w+') as file:
            for indexLine, line in enumerate(self.__scanArray):
                for mes in line[0]:
                    x = mes[0] - (self.__machineConf.scanPosition['X'] + (0 - self.__scanXWidth / 2.0))
                    y = (0 - self.__scanYWidth / 2.0) + (indexLine * (self.__scanYWidth / self.__scanLineYPoint))
                    z = mes[1] / 100.0
                    file.write('{} {} {}\n'.format(x, y, z))

    def _scanFace(self):
        self.__scanArray = []
        scanJob = job.Job(self.driver)
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(
            job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'] + (0 - self.__scanXWidth / 2.0),
                                       'Y': self.__machineConf.scanPosition['Y'] + (self.__scanYWidth / 2.0)},
                         speed=self.__machineConf.axisConfArray['X'].speed))
        scanJob.append(job.MoveTask(self.driver, {
            'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan()},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))

        for xline in range(self.__scanLineYPoint):
            lineList = []
            scanJob.append(
                job.ScanLineTask(pnpDriver=self.driver, extList=lineList, axis='X',
                                 lengt=self.__scanXWidth,
                                 nbMesure=self.__scanLineXPoint, speed=self.__machineConf.axisConfArray['X'].speed))

            self.__scanArray.append(lineList)
            scanJob.append(
                job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'] + (0 - self.__scanXWidth / 2.0)},
                             speed=self.__machineConf.axisConfArray['X'].speed))
            scanJob.append(
                job.MoveTask(self.driver, {'Y': (self.__scanYWidth / self.__scanLineYPoint) * -1.0}, coordMode='R',
                             speed=self.__machineConf.axisConfArray['Y'].speed))
        scanJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=scanJob, driver=self.driver, endFunc=self._endScanFace)
        self.__littleJob.start()

    def _endScanFace_old(self, stat):
        with open('face.asc', 'w+') as file:
            for zIndex, xLine in enumerate(self.__scanArray):
                for xIndex, scanMes in enumerate(xLine):
                    x = (0 - self.__scanXWidth / 2.0) + (xIndex * (self.__scanXWidth / self.__scanLinePoint))
                    y = scanMes / 100.0
                    z = (0 - self.__scanZWidth / 2.0) + (zIndex * (self.__scanZWidth / self.__scanLinePoint))
                    file.write('{} {} {}\n'.format(x, y, z))

    def _scanFace_old(self):
        self.__scanArray = []
        scanJob = job.Job(self.driver)
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(
            job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'] + (0 - self.__scanXWidth / 2.0),
                                       'Y': self.__machineConf.scanPosition['Y']},
                         speed=self.__machineConf.axisConfArray['X'].speed))
        scanJob.append(job.MoveTask(self.driver, {
            'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan() + (0 - self.__scanZWidth / 2.0)},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))

        for xline in range(self.__scanLinePoint):
            lineList = []
            for zPoint in range(self.__scanLinePoint):
                scanJob.append(job.WaitTask(0.01))
                scanJob.append(job.ScanTask(pnpDriver=self.driver, extList=lineList))
                scanJob.append(job.MoveTask(self.driver, {'X': self.__scanXWidth / self.__scanLinePoint}, coordMode='R',
                                            speed=self.__machineConf.axisConfArray['X'].speed))
            self.__scanArray.append(lineList)
            scanJob.append(
                job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'] + (0 - self.__scanXWidth / 2.0)},
                             speed=self.__machineConf.axisConfArray['X'].speed))
            scanJob.append(job.MoveTask(self.driver, {'Z': self.__scanZWidth / self.__scanLinePoint}, coordMode='R',
                                        speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=scanJob, driver=self.driver, endFunc=self._endScanFace)
        self.__littleJob.start()

    def _endScan3D(self, stat):
        firstAngle = self.__scanArray[0][0][0][0]
        with open('3D.asc', 'w+') as file:
            for indexLine, line in enumerate(self.__scanArray):
                for mes in line[0]:
                    x = (mes[0] - firstAngle) / 10.0
                    y = mes[1] / 100.0
                    z = (0 - self.__scanZWidth / 2.0) + (
                            indexLine * (self.__scanZWidth / self.__scanLineZPoint))
                    file.write('{} {} {}\n'.format(x, y, z))

    def _scan3D(self):
        self.__scanArray = []
        scanJob = job.Job(self.driver)
        scanJob.append(job.MoveTask(self.driver, {'Z': self.__machineConf.zLift},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(job.MoveTask(self.driver, {'X': self.__machineConf.scanPosition['X'],
                                                  'Y': self.__machineConf.scanPosition['Y']},
                                    speed=self.__machineConf.axisConfArray['X'].speed))
        scanJob.append(job.MoveTask(self.driver, {
            'Z': self.__machineConf.scanPosition['Z'] + self.ihm.getZscan() + (0 - self.__scanZWidth / 2.0)},
                                    speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.append(job.MoveTask(self.driver, {'C': (0 - self.__scanCircleWidth / 2.0)}, coordMode='R',
                                    speed=self.__machineConf.axisConfArray['C'].speed))

        for circle in range(self.__scanCirclePoint):
            circle = []
            scanJob.append(
                job.ScanLineTask(pnpDriver=self.driver, extList=circle, axis='C',
                                 lengt=self.__scanCircleWidth,
                                 nbMesure=self.__scanCirclePoint, speed=self.__machineConf.axisConfArray['C'].speed))
            self.__scanArray.append(circle)
            scanJob.append(job.MoveTask(self.driver, {'C': (0 - self.__scanCircleWidth)}, coordMode='R',
                                        speed=self.__machineConf.axisConfArray['C'].speed))
            scanJob.append(job.MoveTask(self.driver, {'Z': self.__scanZWidth / self.__scanLineZPoint}, coordMode='R',
                                        speed=self.__machineConf.axisConfArray['Z'].speed))
        scanJob.jobConfigure()

        if self.__littleJob.isRunning():
            self.logger.printCout("Little job already running")
            return 0

        # Run job
        self.__littleJob = job.ThreadJobExecutor(job=scanJob, driver=self.driver, endFunc=self._endScan3D)
        self.__littleJob.start()


class PnpConroller:

    def __init__(self, driver, logger):
        self.driver = driver
        self.ihm = 0
        self.preferences = pr.Preferences(logger, '../userdata/conf/conf.cfg')
        self.modList = dtb.ModDatabase(self.preferences['PATH']['mod'], logger)
        self.machineConfiguration = mch.MachineConf(self.preferences['PATH']['machine'], logger, self.driver)
        self.directCtrl = DirectCtrl(self.driver, self.machineConfiguration)
        self.paramCtrl = ParamCtrl(self.driver, self.machineConfiguration)
        self.boardCtrl = BoardController(self.driver, logger, self.modList, self.machineConfiguration, self.preferences)
        self.dtbCtrl = DtbController(logger, self.modList)
        self.scanCtrl = ScanController(logger, self.driver, self.machineConfiguration, self.modList)
        self.driver.setStatusPipeCallBack(self.updateStatusOnIHM)

        self.directCtrl.setJobIsRunningCb(self.jobIsRunning)

        self.gamePad = gp.AppGamepad()
        self.gamePad.setPresCallBack('connection', lambda: logger.printCout('Gamepad connected'))
        self.gamePad.setReleaseCallBack('connection', lambda: logger.printCout('Gamepad disconnected'))
        self.gamePad.start()

    def setTopIHM(self, ihm):
        self.ihm = ihm

    def discoveringDevice(self):
        self.driver.startDiscoveringDevice()

    def updateStatusOnIHM(self):
        statusStr = ''
        if self.driver.isConnected():
            posDict = self.driver.status
            for key, val in posDict.items():
                statusStr += '{}: {}   '.format(key, val)
            self.directCtrl.IHMposUpdate(posDict)
        else:
            statusStr = 'Searching device...'

        driveState = f'{self.ihm.ctrlWindow.stepX}, '
        driveState += 'C' if self.ihm.ctrlWindow.getContinueState() else 'S'

        self.ihm.setStatusLabel(statusStr, driveState)
        self.ihm.mainWindow.after(300, self.updateStatusOnIHM)

    def jobIsRunning(self):
        return self.boardCtrl.jobIsRunning()

    def _righGamePadRelease(self):
        self.directCtrl.xRelease()
        self.directCtrl.cRelease()

    def _leftGamePadRelease(self):
        self.directCtrl.xRelease()
        self.directCtrl.cRelease()

    def _upGamePadRelease(self):
        self.directCtrl.yRelease()
        self.directCtrl.zRelease()

    def _downGamePadRelease(self):
        self.directCtrl.yRelease()
        self.directCtrl.zRelease()

    def switchDriveMode(self):
        if self.ihm.ctrlWindow.getContinueState():
            self.ihm.ctrlWindow.setContiniueState(0)
        else:
            self.ihm.ctrlWindow.setContiniueState(1)

    def bindInit(self):
        # toto = 'fais caca'
        self.ihm.mainWindow.bind('<Control-KeyPress-Right>', self.directCtrl.xpPress)
        self.ihm.mainWindow.bind('<KeyRelease-Right>', self.directCtrl.xRelease)
        self.ihm.mainWindow.bind('<Control-KeyPress-Left>', self.directCtrl.xmPress)
        self.ihm.mainWindow.bind('<KeyRelease-Left>', self.directCtrl.xRelease)
        self.ihm.mainWindow.bind('<Control-KeyPress-Up>', self.directCtrl.ypPress)
        self.ihm.mainWindow.bind('<KeyRelease-Up>', self.directCtrl.yRelease)
        self.ihm.mainWindow.bind('<Control-KeyPress-Down>', self.directCtrl.ymPress)
        self.ihm.mainWindow.bind('<KeyRelease-Down>', self.directCtrl.yRelease)
        self.ihm.mainWindow.bind('<Control-KeyPress-Prior>', self.directCtrl.zpPress)  # page Up
        self.ihm.mainWindow.bind('<KeyRelease-Prior>', self.directCtrl.zRelease)  # page up
        self.ihm.mainWindow.bind('<Control-KeyPress-Next>', self.directCtrl.zmPress)  # page down
        self.ihm.mainWindow.bind('<KeyRelease-Next>', self.directCtrl.zRelease)  # page down
        self.ihm.mainWindow.bind('<Control-KeyPress-Home>', self.directCtrl.cpPress)  # Debut
        self.ihm.mainWindow.bind('<KeyRelease-Home>', self.directCtrl.cRelease)  # Debut
        self.ihm.mainWindow.bind('<Control-KeyPress-End>', self.directCtrl.cmPress)  # Fin
        self.ihm.mainWindow.bind('<KeyRelease-End>', self.directCtrl.cRelease)  # Fin

        self.gamePad.setPresCallBack('DPAD_RIGHT', self.directCtrl.xpPress)
        self.gamePad.setReleaseCallBack('DPAD_RIGHT', self._righGamePadRelease)
        self.gamePad.setPresCallBack('DPAD_LEFT', self.directCtrl.xmPress)
        self.gamePad.setReleaseCallBack('DPAD_LEFT', self._leftGamePadRelease)
        self.gamePad.setPresCallBack('DPAD_UP', self.directCtrl.ypPress)
        self.gamePad.setReleaseCallBack('DPAD_UP', self._upGamePadRelease)
        self.gamePad.setPresCallBack('DPAD_DOWN', self.directCtrl.ymPress)
        self.gamePad.setReleaseCallBack('DPAD_DOWN', self._downGamePadRelease)

        self.gamePad.setComboPressCallBack('DPAD_RIGHT', 'B', self.directCtrl.cpPress)
        self.gamePad.setComboReleaseCallBack('DPAD_RIGHT', 'B', self._righGamePadRelease)
        self.gamePad.setComboPressCallBack('DPAD_LEFT', 'B', self.directCtrl.cmPress)
        self.gamePad.setComboReleaseCallBack('DPAD_LEFT', 'B', self._leftGamePadRelease)

        self.gamePad.setComboPressCallBack('DPAD_UP', 'B', self.directCtrl.zpPress)
        self.gamePad.setComboReleaseCallBack('DPAD_UP', 'B', self._upGamePadRelease)
        self.gamePad.setComboPressCallBack('DPAD_DOWN', 'B', self.directCtrl.zmPress)
        self.gamePad.setComboReleaseCallBack('DPAD_DOWN', 'B', self._downGamePadRelease)

        self.gamePad.setPresCallBack('RIGHT_SHOULDER', self.directCtrl.stepIncrement)
        self.gamePad.setReleaseCallBack('LEFT_SHOULDER', self.directCtrl.stepDecrement)

        self.gamePad.setPresCallBack('X', self.switchDriveMode)
