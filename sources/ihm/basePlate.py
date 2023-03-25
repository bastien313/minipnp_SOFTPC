from tkinter import messagebox

from .utils import *
from machine import machine as mch
import math


class GenericBasePlateFrame(tk.LabelFrame):
    def __init__(self, fenetre, bpData, machine, logger, controller, commandFrame=True, **kwargs):
        tk.LabelFrame.__init__(self, fenetre, text='BasePlate', labelanchor='n', padx=10, pady=10, width=500,
                               height=300, **kwargs)
        self._controller = controller
        self._machine = machine
        self._basePlate = bpData
        self._identificationFrame = tk.Frame(self)
        self._parametersFrame = tk.Frame(self)
        btnFrame = tk.LabelFrame(self, text="Command", labelanchor='n', padx=10, pady=10)

        self._identificationFrame.grid(row=0, column=0)
        self._parametersFrame.grid(row=1, column=0)
        self._isLocalFeeder = not commandFrame
        if commandFrame:
            btnFrame.grid(row=2, column=0, columnspan=2, sticky='ew')

        self._mother = fenetre

        self._logger = logger
        self.id = CompleteEntry(self._identificationFrame, trashFunc, varType='int')
        self.id.var = self._basePlate.id
        self.id['width'] = 10
        self.type = CompleteEntry(self._identificationFrame, trashFunc, varType='str')
        self.type.var = self._basePlate.type
        self.type['state'] = 'disable'
        self.type['width'] = 20
        self.name = CompleteEntry(self._identificationFrame, trashFunc, varType='str')
        self.name.var = self._basePlate.name
        self.name['width'] = 50

        tk.Label(self._identificationFrame, text="Id").grid(row=0, column=0)
        self.id.grid(row=1, column=0)
        tk.Label(self._identificationFrame, text="Type").grid(row=0, column=1)
        self.type.grid(row=1, column=1)
        tk.Label(self._identificationFrame, text="Name").grid(row=0, column=2)
        self.name.grid(row=1, column=2)

        self._ref1Frame = XYZFrame(self._parametersFrame, text="Ref 1", labelanchor='n', padx=5, pady=5)
        self._ref2Frame = XYZFrame(self._parametersFrame, text="Ref 2", labelanchor='n', padx=5, pady=5)
        self._vectorFrame = XYZFrame(self._parametersFrame, text="Vector Ref", labelanchor='n', padx=5, pady=5)
        self._rotAndZFrame = MultipleEntryFrame(self._parametersFrame, {'Rot(deg)': 'float', 'Zramp': 'float'},
                                                text="Corrector", labelanchor='n', padx=5, pady=5)
        GenericBasePlateFrame._updateIHMFromBasePlate(self)

        self._btnRef1GoTo = ttk.Button(self._parametersFrame, text='Go to', command=self._goToRef1)
        self._btnRef1Get = ttk.Button(self._parametersFrame, text='Get Pos.', command=self._getPosRef1)
        self._btnRef1Theor = ttk.Button(self._parametersFrame, text='Theo. vector', command=self._calcTheo)
        self._btnRef2GoTo = ttk.Button(self._parametersFrame, text='Go To', command=self._goToRef2)
        self._btnRef2Get = ttk.Button(self._parametersFrame, text='Get Pos.', command=self._getPosRef2)
        self._btnRef2Calc = ttk.Button(self._parametersFrame, text='Calc. Ref2', command=self._ref2Calc)
        self._btnRandZCalc = ttk.Button(self._parametersFrame, text='Calc. Corr.', command=self._RandZCalc)

        self._ref1Frame.grid(row=0, column=2, columnspan=2, sticky='ns')
        self._ref2Frame.grid(row=0, column=4, columnspan=2, sticky='ns')
        self._vectorFrame.grid(row=0, column=0, columnspan=2, sticky='ns')
        self._rotAndZFrame.grid(row=0, column=6, columnspan=2, sticky='ns')
        self._btnRef1GoTo.grid(row=1, column=2)
        self._btnRef1Get.grid(row=1, column=3)
        self._btnRef1Theor.grid(row=2, column=4, columnspan=2, sticky='ew')
        self._btnRef2GoTo.grid(row=1, column=4)
        self._btnRef2Get.grid(row=1, column=5)
        self._btnRef2Calc.grid(row=2, column=6, columnspan=2, sticky='ew')
        self._btnRandZCalc.grid(row=1, column=6, columnspan=2, sticky='ew')

        ttk.Button(btnFrame, command=self._save, text='Save').grid(row=0, column=0, padx=10)
        ttk.Button(btnFrame, command=self._delete, text='Delete').grid(row=0, column=1, padx=10)

    def _updateIHMFromBasePlate(self):
        """
        Update ihm with own base plate objects.
        """
        self._ref1Frame.x = self._basePlate.getRealRef(0)['X']
        self._ref1Frame.y = self._basePlate.getRealRef(0)['Y']
        self._ref1Frame.z = self._basePlate.getRealRef(0)['Z']
        self._ref2Frame.x = self._basePlate.getRealRef(1)['X']
        self._ref2Frame.y = self._basePlate.getRealRef(1)['Y']
        self._ref2Frame.z = self._basePlate.getRealRef(1)['Z']
        self._vectorFrame.x = self._basePlate.getTheorVector()['X']
        self._vectorFrame.y = self._basePlate.getTheorVector()['Y']
        self._vectorFrame.z = self._basePlate.getTheorVector()['Z']
        self._rotAndZFrame['Rot(deg)'] = math.degrees(self._basePlate.getRotationOffset())
        self._rotAndZFrame['Zramp'] = self._basePlate.getZramp()

    def _save(self):
        self._basePlate.buildBasePlateFromConfDict({
            'id': self.id.var, 'name': self.name.var,
            'realRef1': {'X': self._ref1Frame.x, 'Y': self._ref1Frame.y, 'Z': self._ref1Frame.z},
            'realRef2': {'X': self._ref2Frame.x, 'Y': self._ref2Frame.y, 'Z': self._ref2Frame.z},
            'vectorRef': {'X': self._vectorFrame.x, 'Y': self._vectorFrame.y, 'Z': self._vectorFrame.z},
            'rotationOffset': math.radians(self._rotAndZFrame['Rot(deg)']), 'zRamp': self._rotAndZFrame['Zramp']
        })
        self._machine.saveToXml()
        self._mother.updateBpListOm()

    def _delete(self):
        self._machine.deleteBasePlate(self.id.var)
        self._machine.saveToXml()
        self._mother.updateBpListOm()
        self._mother.displayBasePlate(0)

    def _goToRef1(self):
        self._controller.goTo({'X': self._ref1Frame.x, 'Y': self._ref1Frame.y, 'Z': self._ref1Frame.z})

    def _goToRef2(self):
        self._controller.goTo({'X': self._ref2Frame.x, 'Y': self._ref2Frame.y, 'Z': self._ref2Frame.z})

    def _getPosRef1(self):
        try:
            pos = self._controller.driver.readHardwarePos()
        except:
            self._controller.Logger.printCout("Devise does not responding")
        else:
            self._ref1Frame.x = float(pos['X'])
            self._ref1Frame.y = float(pos['Y'])
            self._ref1Frame.z = float(pos['Z'])
        self._save()

    def _getPosRef2(self):
        try:
            pos = self._controller.driver.readHardwarePos()
        except:
            self._controller.Logger.printCout("Devise does not responding")
        else:
            self._ref2Frame.x = float(pos['X'])
            self._ref2Frame.y = float(pos['Y'])
            self._ref2Frame.z = float(pos['Z'])
        self._save()

    def _ref2Calc(self):

        self._save()
        self._basePlate.computeFromAngle()
        self._updateIHMFromBasePlate()

    def _RandZCalc(self):
        self._save()
        self._basePlate.computeFromRef()
        self._updateIHMFromBasePlate()

    def _calcTheo(self):
        self._ref2Frame.x = self._ref1Frame.x + self._vectorFrame.x
        self._ref2Frame.y = self._ref1Frame.y + self._vectorFrame.y
        self._ref2Frame.z = self._ref1Frame.z + self._vectorFrame.z
        self._save()  # Update basplate from IHM

    def disableModification(self):
        self.id['state'] = 'disable'
        self.name['state'] = 'disable'
        self._ref1Frame.disable()
        self._ref2Frame.disable()
        self._vectorFrame.disable()
        self._rotAndZFrame.disable()
        # self._btnRef1GoTo
        self._btnRef1Get['state'] = 'disable'
        self._btnRef1Theor['state'] = 'disable'
        # self._btnRef2GoTo
        self._btnRef2Get['state'] = 'disable'
        self._btnRef2Calc['state'] = 'disable'
        self._btnRandZCalc['state'] = 'disable'

    def enableModification(self):
        self.id['state'] = 'normal'
        self.name['state'] = 'normal'
        self._ref1Frame.enable()
        self._ref2Frame.enable()
        self._vectorFrame.enable()
        self._rotAndZFrame.enable()
        # self._btnRef1GoTo
        self._btnRef1Get['state'] = 'normal'
        self._btnRef1Theor['state'] = 'normal'
        # self._btnRef2GoTo
        self._btnRef2Get['state'] = 'normal'
        self._btnRef2Calc['state'] = 'normal'
        self._btnRandZCalc['state'] = 'normal'


class BoardBasePlateFrame(GenericBasePlateFrame):
    def __init__(self, fenetre, machine, logger, controller, **kwargs):
        GenericBasePlateFrame.__init__(self, fenetre, mch.BasePlate({}), machine, logger, controller,
                                       commandFrame=False, **kwargs)

        self._board = 0

        self._identificationFrame.grid_forget()
        self._ref1Frame.grid_forget()
        self._ref2Frame.grid_forget()
        self._ref1Frame = MultipleEntryFrame(self._parametersFrame,
                                             {'Ref': 'str', 'X': 'float', 'Y': 'float', 'Z': 'float'},
                                             text="Ref 1", labelanchor='n', padx=5, pady=5)
        self._ref2Frame = MultipleEntryFrame(self._parametersFrame,
                                             {'Ref': 'str', 'X': 'float', 'Y': 'float', 'Z': 'float'},
                                             text="Ref 2", labelanchor='n', padx=5, pady=5)

        self._vectorCalcBtn = ttk.Button(self._parametersFrame, text='Vect.Calc', command=self._vectorCalc)

        self._ref1Frame.grid(row=0, column=2, columnspan=2, sticky='ns')
        self._ref2Frame.grid(row=0, column=4, columnspan=2, sticky='ns')
        self._vectorCalcBtn.grid(row=1, column=0, columnspan=2, sticky='ns')

        self._ref1Frame.setTraceFunc(self._save)
        self._ref2Frame.setTraceFunc(self._save)
        self._vectorFrame.setTraceFunc(self._save)
        self._rotAndZFrame.setTraceFunc(self._save)

    def setBoard(self, board):
        self._board = board
        self._updateIHM()

    def _vectorCalc(self):
        self._vectorFrame['X'] = self._board[self._ref2Frame['Ref']].posX - self._board[self._ref1Frame['Ref']].posX
        self._vectorFrame['Y'] = self._board[self._ref2Frame['Ref']].posY - self._board[self._ref1Frame['Ref']].posY
        self._vectorFrame['Z'] = 0
        self._save()  # Update basplate from IHM

    def _ref2Calc(self):
        self._board.localBasePlate.computeFromAngle()
        self._updateIHM()

    def _updateIHM(self):
        self._ref1Frame['X'] = self._board.localBasePlate.getRealRef(0)['X']
        self._ref1Frame['Y'] = self._board.localBasePlate.getRealRef(0)['Y']
        self._ref1Frame['Z'] = self._board.localBasePlate.getRealRef(0)['Z']
        self._ref2Frame['X'] = self._board.localBasePlate.getRealRef(1)['X']
        self._ref2Frame['Y'] = self._board.localBasePlate.getRealRef(1)['Y']
        self._ref2Frame['Z'] = self._board.localBasePlate.getRealRef(1)['Z']
        self._vectorFrame['X'] = self._board.localBasePlate.getTheorVector()['X']
        self._vectorFrame['Y'] = self._board.localBasePlate.getTheorVector()['Y']
        self._vectorFrame['Z'] = self._board.localBasePlate.getTheorVector()['Z']
        self._rotAndZFrame['Rot(deg)'] = math.degrees(self._board.localBasePlate.getRotationOffset())
        self._rotAndZFrame['Zramp'] = self._board.localBasePlate.getZramp()
        self._ref1Frame['Ref'] = self._board.ref1
        self._ref2Frame['Ref'] = self._board.ref2

    def _RandZCalc(self):
        self._board.localBasePlate.computeFromRef()
        self._updateIHM()

    def _calcTheo(self):
        self._ref2Frame['X'] = self._ref1Frame['X'] + self._vectorFrame['X']
        self._ref2Frame['Y'] = self._ref1Frame['Y'] + self._vectorFrame['Y']
        self._ref2Frame['Z'] = self._ref1Frame['Z'] + self._vectorFrame['Z']
        self._save()
        # Update basplate from IHM

    def _save(self):
        self._board.localBasePlate.buildBasePlateFromConfDict({
            'id': self.id.var, 'name': self.name.var,
            'realRef1': {'X': self._ref1Frame['X'], 'Y': self._ref1Frame['Y'], 'Z': self._ref1Frame['Z']},
            'realRef2': {'X': self._ref2Frame['X'], 'Y': self._ref2Frame['Y'], 'Z': self._ref2Frame['Z']},
            'vectorRef': {'X': self._vectorFrame['X'], 'Y': self._vectorFrame['Y'], 'Z': self._vectorFrame['Z']},
            'rotationOffset': math.radians(self._rotAndZFrame['Rot(deg)']), 'zRamp': self._rotAndZFrame['Zramp']
        })
        self._board.ref1 = self._ref1Frame['Ref']
        self._board.ref2 = self._ref2Frame['Ref']
        self._updateIHM()


class StripFeederBasePlateFrame(GenericBasePlateFrame):
    def __init__(self, fenetre, bpData, machine, logger, controller, commandFrame=True, **kwargs):
        GenericBasePlateFrame.__init__(self, fenetre, bpData, machine, logger, controller, commandFrame, **kwargs)

        self._additionalFrame = tk.Frame(self)
        self._vector = XYZFrame(self._additionalFrame, text="Vect cmp 0", labelanchor='n', padx=10, pady=10)
        self._misc = MultipleEntryFrame(self._additionalFrame, {'Strip Step': 'float'}, text="Misc", labelanchor='n',
                                        padx=10, pady=10)

        self._additionalFrame.grid(row=1, column=2)
        self._vector.grid(row=0, column=0, sticky='ew')
        self._misc.grid(row=1, column=0)

        self._updateIHMFromBasePlate()

    def _save(self, isLocalFeeder=False):
        self._basePlate.buildBasePlateFromConfDict({
            'id': self.id.var, 'name': self.name.var,
            'realRef1': {'X': self._ref1Frame.x, 'Y': self._ref1Frame.y, 'Z': self._ref1Frame.z},
            'realRef2': {'X': self._ref2Frame.x, 'Y': self._ref2Frame.y, 'Z': self._ref2Frame.z},
            'vectorRef': {'X': self._vectorFrame.x, 'Y': self._vectorFrame.y, 'Z': self._vectorFrame.z},
            'rotationOffset': math.radians(self._rotAndZFrame['Rot(deg)']), 'zRamp': self._rotAndZFrame['Zramp'],
            'stripStep': self._misc['Strip Step'],
            'vectorFistCmp': {'X': self._vector.x, 'Y': self._vector.y, 'Z': self._vector.z}
        })
        self._machine.saveToXml()
        if not self._isLocalFeeder:
            self._mother.updateBpListOm()

    def _updateIHMFromBasePlate(self):
        GenericBasePlateFrame._updateIHMFromBasePlate(self)
        self._misc['Strip Step'] = self._basePlate.getStripStep()
        self._vector.x = self._basePlate.getVectorFirstCmp()['X']
        self._vector.y = self._basePlate.getVectorFirstCmp()['Y']
        self._vector.z = self._basePlate.getVectorFirstCmp()['Z']

    def disableModification(self):
        GenericBasePlateFrame.disableModification(self)
        self._vector.disable()
        self._misc.disable()

    def enableModification(self):
        GenericBasePlateFrame.enableModification(self)
        self._vector.enable()
        self._misc.enable()


class BasePlateFrame(tk.Frame):
    def __init__(self, fenetre, machineConf, logger, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)

        self._motherFrame = fenetre
        self.__newBtn = ttk.Button(self, command=self.__newBpBtn, text='New')
        self.controller = controller
        self.__machineConf = machineConf
        self.__logger = logger
        self.__bpList = ['None']
        self.__strBp = tk.StringVar(self)
        self.__strBp.set(self.__bpList[0])

        self.__bpOm = ttk.OptionMenu(self, self.__strBp, *self.__bpList)

        self.__bpFrame = tk.Frame(self, width=500, height=500)

        self.__bpOm.grid(row=0, column=0)
        self.__newBtn.grid(row=0, column=1)
        self.__bpFrame.grid(row=1, column=0, columnspan=2)

        self.updateBpListOm()
        self.__strBp.trace('w', self.__changeBpTrace)

    def __changeBpTrace(self, *args):
        """
        Called when string of option menu change
        :param args:
        :return:
        """
        self.displayBasePlate(int(self.__strBp.get()))

    def updateBpListOm(self):
        """
        Update the option menu with machine data (Base plate list).
        :return:
        """
        self.__bpList = [str(bp.id) for bp in self.__machineConf.basePlateList]
        menu = self.__bpOm["menu"]
        menu.delete(0, "end")
        for string in self.__bpList:
            menu.add_command(label=string,
                             command=lambda value=string: self.__strBp.set(value))

    def __newBpBtn(self):
        """
        Called by btn newBsePlate.
        Display new feeder windows and go to __addBp if Ok is pressed else go to __cancelNewFeeder
        :return:
        """
        self._newBpWindow = tk.Toplevel(self._motherFrame)
        self._newBpWindow.title('Add base plate')
        # newFeedFrame = tk.Frame(newFeedWindow)

        listeOptions = ('Generic', 'Strip base')
        self._newBpTypeSel = tk.StringVar()
        self._newBpTypeSel.set(listeOptions[0])
        self._newBpId = CompleteEntry(self._newBpWindow, trashFunc, varType='int')
        om = ttk.OptionMenu(self._newBpWindow, self._newBpTypeSel, *listeOptions)
        om.configure(width=12)

        tk.Label(self._newBpWindow, text='Type: ').grid(row=0, column=0, sticky='ew')
        om.grid(row=0, column=1, sticky='ew')
        tk.Label(self._newBpWindow, text='Id: ').grid(row=1, column=0, sticky='ew')
        self._newBpId.grid(row=1, column=1, sticky='ew')
        ttk.Button(self._newBpWindow, text='Cancel', command=self._newBpWindow.destroy).grid(row=2, column=0,
                                                                                             sticky='ew')
        ttk.Button(self._newBpWindow, text='Ok', command=self.__addBasePlate).grid(row=2, column=1, sticky='ew')
        self._newBpWindow.grab_set()  # Lock focus en new window

    def __addBasePlate(self):
        """
        Called when create button was pressed in the new feeder windows
        :return:
        """
        self._newBpWindow.destroy()

        if self.__machineConf.getBasePlateById(self._newBpId.var):
            MsgBox = messagebox.askokcancel('Base plate confirm',
                                            'Id {} already exist.\nContiniue?'.format(self._newBpId.var),
                                            icon='warning')
            if not MsgBox:
                return

        newBp = None
        if self._newBpTypeSel.get() == 'Generic':
            newBp = mch.BasePlate({'id': self._newBpId.var})
        elif self._newBpTypeSel.get() == 'Strip base':
            newBp = mch.BasePlateForStripFeeder({'id': self._newBpId.var})

        self.__machineConf.addBasePlate(newBp)
        self.__strBp.set(str(newBp.id))
        self.displayBasePlate(newBp.id)

    def displayBasePlate(self, bpId):
        """
        Display base plate on IHM.
        :param bpId: id of base plate
        :return:
        """
        self.__bpFrame.grid_forget()
        for bp in self.__machineConf.basePlateList:
            if bp.id == bpId:
                if bp.type == 'BasePlate':
                    self.__bpFrame = GenericBasePlateFrame(self, bp, self.__machineConf, self.__logger,
                                                           self.controller)
                    self.__bpFrame.grid(row=1, column=0, columnspan=3)
                    return
                elif bp.type == 'StripFeederBasePlate':
                    self.__bpFrame = StripFeederBasePlateFrame(self, bp, self.__machineConf, self.__logger,
                                                               self.controller)
                    self.__bpFrame.grid(row=1, column=0, columnspan=3)
                    return
                else:
                    self.__logger.printCout(bp.type + ': type cannot be loaded in IHM.')
        self.__logger.printCout('{} Base plate not found'.format(bpId))
