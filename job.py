import copy
from misc import Point4D
from enum import Enum, auto
import time
import threading
import deprecated


class TaskStatusEnum(Enum):
    ERROR = auto()
    RUN = auto()
    END = auto()
    STOP = auto()
    PAUSE = auto()


class TaskStatus:
    """
    Status of a task
    """

    def __init__(self, status=TaskStatusEnum.RUN, step=0, msg=''):
        # Dtatus definition
        self.status = status
        self.msg = msg
        # self.step = step
        self.result = 0  # Result of task if data a readed from task.


class SimpleTask:
    """
    A simple task class template.
    A simple task is a list of function.
    User can stop task between function.
    When a task is stoped user need to restart all the task for finish it.
    A simple task cannot be paused, only stop or run.
    """

    def __init__(self, name=''):
        self._status = TaskStatus()
        self._functionList = 0
        self._funcCnt = 0
        self._taskConfigure([lambda: TaskStatus(status=TaskStatusEnum.END)])
        self._name = name

    def _taskConfigure(self, functionList):
        """
        Edit function list and rester itterator.
        Herited class must call this.
        :param functionList:
        :return:
        """
        self._functionList = functionList
        self._funcCnt = 0

    def _nextFunc(self):
        """
        Put in self._taskToExec the next task.
        If there is no task to execute self._status.status is set to END.
        :return:
        """
        print(self._name)
        if self._funcCnt == (len(self._functionList) - 1):
            self._status.status = TaskStatusEnum.END
        else:
            self._funcCnt += 1

    def exec(self):
        """
        execute sub function of task.
        Function are stored in self._functionList and accesed by self._funcIter(iterrator)
        if function return 1 the iterrator can next()
        :return:
        """
        if self._status.status == TaskStatusEnum.RUN:
            funcStatus = self._functionList[self._funcCnt]()
            if funcStatus.status == TaskStatusEnum.END:
                self._nextFunc()
            elif funcStatus.status == TaskStatusEnum.ERROR:
                self._status.status = TaskStatusEnum.ERROR
                self._status.msg = funcStatus.msg
        return self._status

    def stop(self):
        self._status.status = TaskStatusEnum.STOP
        self._funcCnt = 0

    def start(self):
        """
        Call this for start or restart task after a stop.
        :return:
        """
        self._status.status = TaskStatusEnum.RUN
        self._funcCnt = 0
        # self._status.step = 0

    def clearError(self):
        if self._status.status == TaskStatusEnum.ERROR:
            self.start()

    def __str__(self, startLine=''):
        return startLine + 'Task: ' + self._name + '\n'

    @property
    def status(self):
        return self._status


class ExternalCallTask(SimpleTask):
    """
    Task call an external function.
    """

    def __init__(self, callBack, name='', param=None):
        """
        :param callBack: Function to call.
        :param param: optional parameter
        """
        super().__init__(name)
        self._cb = callBack
        self._param = param
        self._taskConfigure([self._localCallBack])

    def _localCallBack(self):
        self._cb(self._param)
        self._status.status = TaskStatusEnum.END
        return TaskStatus(status=TaskStatusEnum.END)


class ScanTask(SimpleTask):
    """
    Make a scan and write data to externalList
    """

    def __init__(self, pnpDriver, extList, name=''):
        super().__init__(name)
        self._el = extList
        self._driver = pnpDriver
        self._taskConfigure([self._scan])

    def _scan(self):
        self._el.append(self._driver.makeScan())
        return TaskStatus(status=TaskStatusEnum.END)


class ScanLineTask(SimpleTask):
    """
    Make a scan and write data to externalList
    """

    def __init__(self, pnpDriver, extList, axis, lengt, nbMesure, speed, name=''):
        super().__init__(name)
        self._el = extList
        self._driver = pnpDriver
        self._axis = axis
        self._lengt = lengt
        self._nbMesure = nbMesure
        self._speed = speed
        self._taskConfigure([self._scan])

    def _scan(self):
        self._el.append(self._driver.makeScanLine(axis=self._axis, speed=self._speed,
                                                  lengt=self._lengt, nbMesure=self._nbMesure))
        return TaskStatus(status=TaskStatusEnum.END)


class PumpStateTask(SimpleTask):
    """
    Enable or disable pump.
    """

    def __init__(self, pnpDriver, state, name=''):
        """
        :param pnpDriver: driver class for build gcode and send to device.
        :param state: state of pump
        """
        super().__init__(name)
        self._state = state
        self._driver = pnpDriver
        self._taskConfigure([self._pumpState])

    def _pumpState(self):
        self._driver.ctrlPump(self._state)
        self._status.msg = 'Set pump state{}'.format(self._state)
        self._status.status = TaskStatusEnum.END
        return TaskStatus(status=TaskStatusEnum.END)


class FeederNextCmdTask(SimpleTask):
    """
    Signifie to feeder that a comoment was picked up.
    """

    def __init__(self, feeder, name=''):
        """
        :param pnpDriver: driver class for build gcode and send to device.
        :param state: state of pump
        """
        super().__init__(name)
        self._feeder = feeder
        self._taskConfigure([self._nextRequest])

    def _nextRequest(self):
        self._feeder.prepareNextComponent()
        return TaskStatus(status=TaskStatusEnum.END)


class FeederVoidErrorTask(SimpleTask):
    """
    Raise on status an error if feeder was void
    """

    def __init__(self, feeder, name=''):
        """
        :param pnpDriver: driver class for build gcode and send to device.
        :param state: state of pump
        """
        super().__init__(name)
        self._feeder = feeder
        self._taskConfigure([self._errorCheck])

    def _errorCheck(self):
        print('ffed')
        if not self._feeder.haveComponent():
            self._status.status = TaskStatusEnum.ERROR
            self._status.msg = '{} Feeder void'.format(self._feeder.id)
            return self._status
        else:
            return TaskStatus(status=TaskStatusEnum.END)


class WaitFeederWasReadyTask(SimpleTask):
    """
    Signifie to feeder that a comoment was picked up.
    """

    def __init__(self, feeder, name=''):
        """
        :param pnpDriver: driver class for build gcode and send to device.
        :param state: state of pump
        """
        super().__init__(name)
        self._feeder = feeder
        self._taskConfigure([self._waitFeeder])

    def _waitFeeder(self):
        return TaskStatus(status=TaskStatusEnum.END) if self._feeder.nextComponentIsReady() else TaskStatus(
            status=TaskStatusEnum.RUN)


class MoveTask(SimpleTask):
    """
    Move task.
    Do not combine X Y Z and C movement if a speed change is needed.
    Send Move request and wait while machine is moving.
    """

    def __init__(self, pnpDriver, coord, speed, speedRot=None, speedMode='P', coordMode='A', name=''):
        """
        :param pnpDriver: driver class for build gcode and send to device.
        :param coord: coord where we go. dict{'X':val,.....}
        :param speed: None for dont change speed, float for set speed, 'HS' for high speed (G1)
        :param coordMode: 'A' for absolute, 'R' for relative
        """
        super().__init__(name)
        self._driver = pnpDriver
        self._moveCoord = coord
        self._speed = speed
        self._speedRot = speedRot
        self._speedMode = speedMode
        self._coordMode = coordMode
        self._taskConfigure([self._waitMovementFirst, self._launchMovement, self._waitMovementEnd])

    def _waitMovementFirst(self):
        # Wait last movement.
        self._status.msg = 'Wait machine is ready first'
        return TaskStatus(status=TaskStatusEnum.RUN) if self._driver.isBusy() else TaskStatus(
            status=TaskStatusEnum.END)

    def _waitMovementEnd(self):
        # Wait last movement.
        self._status.name = 'Wait machine is ready end'
        if not self._driver.isBusy():
            self._status.status = TaskStatusEnum.END
            return TaskStatus(status=TaskStatusEnum.END)
        else:
            return TaskStatus(status=TaskStatusEnum.RUN)

    def _launchMovement(self):
        # Move request.
        self._status.msg = 'Launch movement'
        self._driver.moveAxis(moveData=self._moveCoord, speed=self._speed, speedRot=self._speedRot,
                              speedMode=self._speedMode, mode=self._coordMode)
        return TaskStatus(status=TaskStatusEnum.END)


class FeederGoToTask(MoveTask):
    """
        go to XY position feeder component.
    """

    def __init__(self, feeder, pnpDriver, speed, speedRot=None, speedMode='P', coordMode='A', name=''):
        """
        """
        self._moveCoord = {}
        super().__init__(pnpDriver, self._moveCoord, speed,speedRot, speedMode, coordMode, name)
        self._feeder = feeder
        self._taskConfigure([self._getPosition, self._waitMovementFirst, self._launchMovement,
                             self._releaseRotation, self._waitMovementFirst, self._launchMovement, self._waitMovementEnd])

    def _getPosition(self):
        self._moveCoord = self._feeder.getComponentPosition()
        self._moveCoord = {'X': self._moveCoord['X'], 'Y': self._moveCoord['Y'], 'C': -30.0}
        return TaskStatus(status=TaskStatusEnum.END)

    def _releaseRotation(self):
        self._moveCoord = {'C': 30.0}
        return TaskStatus(status=TaskStatusEnum.END)


class EvStateTask(SimpleTask):
    """
    Enable or disable pump.
    """

    def __init__(self, pnpDriver, state, name=''):
        """
        :param pnpDriver: driver class for build gcode and send to device.
        :param state: state of electro vane.
        """
        super().__init__(name)
        self._driver = pnpDriver
        self._state = state
        self._taskConfigure([self._evState])

    def _evState(self):
        self._driver.ctrlEv(self._state)
        self._status.msg = 'Set Ev state{}'.format(self._state)
        self._status.status = TaskStatusEnum.END
        return TaskStatus(status=TaskStatusEnum.END)


class PumpStateTask(SimpleTask):
    """
    Enable or disable pump.
    """

    def __init__(self, pnpDriver, state, name=''):
        """
        :param pnpDriver: driver class for build gcode and send to device.
        :param state: state of electro vane.
        """
        super().__init__(name)
        self._driver = pnpDriver
        self._state = state
        self._taskConfigure([self._evState])

    def _evState(self):
        self._driver.ctrlPump(self._state)
        self._status.msg = 'Set Pump state{}'.format(self._state)
        self._status.status = TaskStatusEnum.END
        return TaskStatus(status=TaskStatusEnum.END)


class WaitTask(SimpleTask):
    """
    Wait task
    """

    def __init__(self, delayInS, name=''):
        """
        :param delayInS: Delay of wait time in seconds.
        """
        super().__init__(name)
        self._timeCount = 0
        self._timeOutS = delayInS
        self._taskConfigure([self._startCounter, self._waitTimeOut])

    def _startCounter(self):
        self._timeCount = time.time()
        self._status.msg = 'Start delay {}s'.format(self._timeOutS)
        return TaskStatus(status=TaskStatusEnum.END)

    def _waitTimeOut(self):
        if (time.time() - self._timeCount) > self._timeOutS:
            self._status.status = TaskStatusEnum.END
            return TaskStatus(status=TaskStatusEnum.END)
        else:
            return TaskStatus(status=TaskStatusEnum.RUN)


class HomingTask(SimpleTask):
    """
    Launch an homming request and with until is finish.
    """

    def __init__(self, pnpDriver, name=''):
        """
        :param pnpDriver: driver class for build gcode and send to device.
        """
        super().__init__(name)
        self._driver = pnpDriver
        self._taskConfigure([self._homingRequest, self._waitMovement])

    def _homingRequest(self):
        self._driver.homeAxis('XYZC')
        self._status.msg = 'Start homing'
        return TaskStatus(status=TaskStatusEnum.END)

    def _waitMovement(self):
        # Wait last movement.
        self._status.msg = 'Wait machine is ready'
        if not self._driver.isBusy():
            self._status.status = TaskStatusEnum.END
            return TaskStatus(status=TaskStatusEnum.END)
        else:
            return TaskStatus(status=TaskStatusEnum.RUN)


class Job(SimpleTask):
    """
    A Job class template.
    A Job is a list of simple task.
    User can stop, pause, start or unpause.
    """

    def __init__(self, name=''):
        super().__init__(name)
        self._taskList = []
        self.jobConfigure()

    def jobConfigure(self):
        """
        Edit job list and rester itterator.
        Herited class must call this.
        :param functionList:
        :return:
        """
        self._taskConfigure([task.exec for task in self._taskList])

    def pause(self):
        self._status.status = TaskStatusEnum.PAUSE
        if type(self._taskList[self._funcCnt]) is Job:
            self._taskList[self._funcCnt].pause()
        else:
            self._taskList[self._funcCnt].stop()

    def unPause(self):
        self._status.status = TaskStatusEnum.RUN
        if type(self._taskList[self._funcCnt]) is Job:
            self._taskList[self._funcCnt].unPause()
        else:
            self._taskList[self._funcCnt].start()

    def clearError(self):
        if self._status.status == TaskStatusEnum.ERROR:
            if type(self._taskList[self._funcCnt]) is Job:
                self._taskList[self._funcCnt].clearError
            else:
                self._taskList[self._funcCnt].start()
            self._status.status = TaskStatusEnum.RUN

    def append(self, task):
        """
        Add task to job.
        A job configure must be called when job is fuuly filled.
        :return:
        """
        self._taskList.append(task)

    def insert(self, id, task):
        """
        Insert a task, job cofigure must be recaled
        :param task:
        :return:
        """
        self._taskList.insert(id, task)

    def getStateDescription(self):
        if len(self._taskList):
            return '{}/{} {}'.format(self._funcCnt, len(self._taskList), self._taskList[self._funcCnt]._name)
        else:
            return '0/0 {}'.format(self._name)

    def __str__(self, startLine=''):
        strOut = startLine + 'Job: ' + self._name + '\n'
        for task in self._taskList:
            strOut += startLine + task.__str__(startLine='---')
        return strOut + '\n'


class PickAndPlaceJob(Job):
    """
    Pick and place task.
    """

    def __init__(self, pnpDriver, feeder, placePos, model, zLift, correctorPos, name='', ref=''):
        """

        :param pnpDriver: Driver of pnp machine
        :param pickupPos: Pickup position.
        :param placePos: Place pos, Z must be 0 board
        :param model: model of component
        :param zLift: security z lift.
        """
        super().__init__(name)
        self._driver = pnpDriver
        self._ZpickupPos = feeder.getComponentPosition()['Z']
        self._placePos = placePos
        self._model = model
        self._taskList = [
            MoveTask(self._driver, {'Z': zLift}, speed=model.moveSpeed, name='{} Start Z lift.'.format(ref)),
            FeederGoToTask(feeder, self._driver, speed=model.moveSpeed,
                           name='{} Go to feeder.'.format(ref)),
            WaitFeederWasReadyTask(feeder, name='{} Wait feeder.'.format(ref)),
            FeederVoidErrorTask(feeder, name='{} Feeder error?'.format(ref)),
            MoveTask(self._driver, {'Z': self._ZpickupPos}, speed=model.pickupSpeed,
                     name='{} Pick Z down.'.format(ref)),
            EvStateTask(self._driver, 1, name='{} Enable vaccum.'.format(ref)),
            PumpStateTask(self._driver, 1, name='{} Enable vaccum.'.format(ref)),
            WaitTask(0.5, name='{}Pump.'.format(ref)),
            WaitTask(model.pickupDelay / 1000.0, name='{} Pick delay.'.format(ref)),
            MoveTask(self._driver, {'Z': zLift}, speed=model.pickupSpeed, name='{} Pick Z up.'.format(ref)),
            FeederNextCmdTask(feeder, name='{} Feeder next request.'.format(ref)),
            MechanicsCorectorJob(pnpDriver, correctorPos, self._model, zLift),
            MoveTask(self._driver, {'X': self._placePos['X'], 'Y': self._placePos['Y'], 'C': self._placePos['C']},
                     speed=model.moveSpeed, name='{} Go to component position.'.format(ref)),
            MoveTask(self._driver, {'Z': placePos['Z'] + model.height}, speed=model.placeSpeed,
                     name='{} Place Z down.'.format(ref)),
            EvStateTask(self._driver, 0, name='{} Disable vaccum.'.format(ref)),
            PumpStateTask(self._driver, 0, name='{} Disable vaccum.'.format(ref)),
            # WaitTask(0.5, name='{}Pump.'.format(ref)),
            WaitTask(model.placeDelay / 1000.0, name='{} Place delay.'.format(ref)),
            MoveTask(self._driver, {'Z': zLift}, speed=model.moveSpeed, name='{} End Z lift.'.format(ref)),
        ]
        self.jobConfigure()


class MechanicsCorectorJob(Job):
    """
    """

    def __init__(self, pnpDriver, correctorPos, model, zLift, name=''):
        """
        :param pnpDriver:
        :param correctorPos:
        :param model:
        :param zLift:
        :param name:
        :param ref:
        """
        super().__init__(name)
        self._driver = pnpDriver
        self._correctorPos = correctorPos
        self._model = model
        corectorSize = {'X': 3.475, 'Y': 3.475}
        cornerHGPos = {'X': (self._correctorPos['X'] - corectorSize['X']) + (model.width/2),
                       'Y': (self._correctorPos['Y'] + corectorSize['Y']) - (model.length/2)}
        cornerBDPos = {'X': (self._correctorPos['X'] + corectorSize['X']) - (model.width/2),
                       'Y': (self._correctorPos['Y'] - corectorSize['Y']) + (model.length/2)}
        self._taskList = [
            MoveTask(self._driver, {'Z': zLift}, speed=model.moveSpeed, name='Start Z lift.'),

            MoveTask(self._driver, {'X': self._correctorPos['X'], 'Y': self._correctorPos['Y'], 'C':30.0}, speed=model.moveSpeed,
                     name='Cooector GO TO -'),
            MoveTask(self._driver, {'Z': self._correctorPos['Z'] + self._model.scanHeight, 'C':-30.0}, speed=model.moveSpeed,
                     name='Corector Z pos.'),
            MoveTask(self._driver, cornerHGPos, speed=model.moveSpeed,
                     name='Corector corner HG.'),
            MoveTask(self._driver, cornerBDPos, speed=model.moveSpeed,
                     name='Corector corner BD.'),
            MoveTask(self._driver, cornerHGPos, speed=model.moveSpeed,
                     name='Corector corner HG.'),
            MoveTask(self._driver, cornerBDPos, speed=model.moveSpeed,
                     name='Corector corner BD.'),
            MoveTask(self._driver, {'X': self._correctorPos['X'], 'Y': self._correctorPos['Y']}, speed=model.moveSpeed,
                     name='Cooector GO TO -'),
            MoveTask(self._driver, {'Z': zLift}, speed=model.moveSpeed, name='Start Z lift.'),
        ]
        self.jobConfigure()


class ThreadJobExecutor(threading.Thread):
    """
    Thread class for launch job.
    When an error occur
    """

    def __init__(self, job=Job(), notifyFunc=lambda x: None, errorFunc=lambda x: None, endFunc=lambda x: None,
                 driver=None):
        """
        :param job: job to execute.
        :param errorFunc: calback when erro occur
        :param endFunc:
        """
        threading.Thread.__init__(self)
        self._job = job
        self._driver = driver
        self._errorFunc = errorFunc
        self._endFunc = endFunc
        self._notify = notifyFunc
        self._inPause = False
        self._stopSignal = False
        self._pauseSignal = False
        self._unPauseSignal = False
        self._oldNotify = ''

    def run(self):
        while not self._stopSignal:
            # Pause called by exterior of thread.
            if self._pauseSignal:
                self._pauseSignal = False
                self._job.pause()
                self._driver.stopMachine()
                self._inPause = True
            # UnPause called by exterior of thread.
            if self._unPauseSignal:
                self._unPauseSignal = False
                self._job.unPause()
                self._inPause = False
            if not self._inPause:
                # Normally job running.
                jobStatus = self._job.exec()
                if self.getStateDescription() != self._oldNotify:
                    self._oldNotify = self.getStateDescription()
                    self._notify(self._oldNotify)
                # Check job status aud pause if needed.
                if jobStatus.status == TaskStatusEnum.PAUSE:
                    self._inPause = True
                elif jobStatus.status == TaskStatusEnum.ERROR:
                    self._inPause = True
                    self._errorFunc(self._job.status)
                elif jobStatus.status == TaskStatusEnum.END:
                    self._stopSignal = True
            #time.sleep(0.02)
        # self._driver.stopMachine()
        self._endFunc(self._job.status)

    def pause(self):
        self._pauseSignal = True

    def unPause(self):
        self._unPauseSignal = True

    def stop(self):
        self._stopSignal = True

    def isRunning(self):
        return self._pauseSignal

    def getStateDescription(self):
        return self._job.getStateDescription()

    @property
    def status(self):
        return self._job.status
