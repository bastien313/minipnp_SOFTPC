from tkinter import messagebox
from .utils import *
import tkinter as tk

from .basePlate import *
from machine import feeder as fdr


class CommonFeederFrame(tk.Frame):
    """
    Common feeder frame class.
    Define all common frame of a feeder, identification, test(pick), save/delete.
    implement commun method, delete, pick. User must always implement save.
    This class does not grit the top frame, the herited class must do it.

    """
    def __init__(self, fenetre, feederData, machine, logger, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, width=500, height=300, **kwargs)
        self._controller = controller
        self._mother = fenetre
        self._machine = machine
        self._logger = logger
        self._feeder = feederData

        self._identificationFrame = tk.LabelFrame(self, text=feederData.type, labelanchor='n', padx=10, pady=10)
        self._testFrame = tk.LabelFrame(self, text="Pick", labelanchor='n', padx=10, pady=10)
        self._btnFrame = tk.LabelFrame(self, text="Command", labelanchor='n', padx=10, pady=10)

        leftIdFrame = tk.Frame(self._identificationFrame)
        errorFrame = tk.Frame(self._identificationFrame,padx=50)

        leftIdFrame.grid(row=0, column=0)
        errorFrame.grid(row=0, column=1)

        self.id = CompleteEntry(leftIdFrame, lambda: None, varType='int')
        self.id.var = feederData.id
        self.id['width'] = 10
        self.id['state'] = 'disable'
        self.name = CompleteEntry(leftIdFrame, lambda: None, varType='str')
        self.name.var = feederData.name
        self.name['width'] = 50

        tk.Label(leftIdFrame, text="Id").grid(row=0, column=0)
        self.id.grid(row=1, column=0)
        tk.Label(leftIdFrame, text="Name").grid(row=0, column=2)
        self.name.grid(row=1, column=2)


        self._errStatus = CompleteEntry(errorFrame, lambda: None, varType='int')
        self._errStatus.var = feederData.getErrorScore()
        self._errScore = CompleteEntry(errorFrame, lambda: None, varType='int')
        self._errScore.var = feederData.getErrorCounter()
        self._btnClearError = ttk.Button(errorFrame, text='Clear', command=self._errorClr)


        tk.Label(errorFrame, text="Error status").grid(row=0, column=0)
        self._errStatus.grid(row=0, column=1)
        tk.Label(errorFrame, text="Error score").grid(row=1, column=0)
        self._errScore.grid(row=1, column=1)
        self._btnClearError.grid(row=0, column=3, padx=10)



        self.pickId = CompleteEntry(self._testFrame, lambda: None, varType='int')
        #self.stripId = CompleteEntry(self._testFrame, lambda: None, varType='int')
        self.pickId.var = 0
        #self.stripId.var = 0

        tk.Label(self._testFrame, text="Cmp").grid(row=0, column=0)
        self.pickId.grid(row=0, column=1)
        #tk.Label(self._testFrame, text="Cmp").grid(row=1, column=0)
        #self.pickId.grid(row=1, column=1)
        ttk.Button(self._testFrame, command=self._pick, text='Pick').grid(row=0, column=2, padx=10, sticky='ew')

        self._btnSave = ttk.Button(self._btnFrame, text='Save', command=self._save)
        self._btnSave.grid(row=0, column=0, padx=10)
        ttk.Button(self._btnFrame, command=self._delete, text='Delete').grid(row=0, column=1, padx=10)

    def _delete(self):
        self._machine.deleteFeeder(self.id.var)
        self._machine.saveToXml()
        self._mother.updateFeederListOm()
        self._mother.displayFeeder(0)

    def _pick(self):
        self._mother.pick(self.id.var, self.pickId.var)

    def _save(self):
        self._logger.printCout('Feeder save is not implemented!')
        raise 'Feeder save is not implemented!'

    def _errorClr(self):
        self._feeder.clearErrorScore()
        self._save()


class CompositeFeederFrame(CommonFeederFrame):
    def __init__(self, fenetre, feederData, machine, logger, controller, **kwargs):

        CommonFeederFrame.__init__(self, fenetre, feederData, machine, logger, controller, **kwargs)
        parametersFrame = tk.LabelFrame(self, text="Parameters", labelanchor='n', padx=10, pady=10)

        self._identificationFrame.grid(row=0, column=0, columnspan=2, sticky='ew')
        parametersFrame.grid(row=1, column=0, columnspan=2)
        self._btnFrame.grid(row=2, column=0, sticky='ew')
        self._testFrame.grid(row=2, column=1, sticky='ew')

        self.feederDesc = CompleteEntry(parametersFrame, lambda: None, varType='str')
        self.feederDesc.var = feederData.feederListToStr()
        self.feederDesc['width'] = 50

        tk.Label(parametersFrame, text="Composition").grid(row=0, column=0)
        self.feederDesc.grid(row=0, column=1)

    def _save(self):
        newFeeder = fdr.CompositeFeeder({'id': self.id.var, 'name': self.name.var,
                                         'feederList': self._machine.makeFilteredFeederList(self.feederDesc.var)},
                                        self._machine)
        self._machine.addFeeder(newFeeder)
        self._machine.saveToXml()
        self._mother.updateFeederListOm()


class MechanicalFeederFrame(CommonFeederFrame):
    def __init__(self, fenetre, feederData, machine, logger, controller, **kwargs):
        CommonFeederFrame.__init__(self, fenetre, feederData, machine, logger, controller,  **kwargs)

        parametersFrame = tk.LabelFrame(self, text="Parameters", labelanchor='n', padx=10, pady=10)

        self._identificationFrame.grid(row=0, column=0, columnspan=2, sticky='ew')
        parametersFrame.grid(row=1, column=0, columnspan=2)
        self._btnFrame.grid(row=2, column=0, sticky='ew')
        self._testFrame.grid(row=2, column=1, sticky='ew')

        self._xyzcPickup = XYZCFrame(parametersFrame, text='PickUp')
        self._xyzcPickup.x = feederData.getComponentPosition()['X']
        self._xyzcPickup.y = feederData.getComponentPosition()['Y']
        self._xyzcPickup.z = feederData.getComponentPosition()['Z']
        self._xyzcPickup.c = feederData.getComponentPosition()['C']
        self._leverLowPos = XYZFrame(parametersFrame, text='Lever')
        self._leverLowPos.x = feederData.getLeverPos()['X']
        self._leverLowPos.y = feederData.getLeverPos()['Y']
        self._leverLowPos.z = feederData.getLeverPos()['Z']

        self._xyzcPickup.grid(row=0, column=0)
        self._leverLowPos.grid(row=0, column=1)
        ttk.Button(parametersFrame, command=self._xyzcGetPos, text='Get Pos.').grid(row=1, column=0, padx=10)
        ttk.Button(parametersFrame, command=self._leverGetPos, text='Get Pos.').grid(row=1, column=1, padx=10)



    def _save(self):
        newFeeder = fdr.MechanicalFeeder(paramList={'id': self.id.var, 'name': self.name.var,
                                                    'pickupPos': {'X': self._xyzcPickup.x, 'Y': self._xyzcPickup.y,
                                                                  'Z': self._xyzcPickup.z, 'C': self._xyzcPickup.c},
                                                    'leverLowPos': {'X': self._leverLowPos.x, 'Y': self._leverLowPos.y,
                                                                    'Z': self._leverLowPos.z}},
                                         driver=self._controller, machine=self._machine)
        self._feeder = newFeeder
        self._machine.addFeeder(newFeeder)
        self._machine.saveToXml()
        self._mother.updateFeederListOm()

    def _xyzcGetPos(self):
        try:
            pos = self._controller.driver.readHardwarePos()
        except:
            self._controller.Logger.printCout("Devise does not responding")
        else:
            self._xyzcPickup.x = float(pos['X'])
            self._xyzcPickup.y = float(pos['Y'])
            self._xyzcPickup.z = float(pos['Z'])
        self._save()

    def _leverGetPos(self):
        try:
            pos = self._controller.driver.readHardwarePos()
        except:
            self._controller.Logger.printCout("Devise does not responding")
        else:
            self._leverLowPos.x = float(pos['X'])
            self._leverLowPos.y = float(pos['Y'])
            self._leverLowPos.z = float(pos['Z'])
        self._save()




class StripFeederFrame(CommonFeederFrame):
    def __init__(self, fenetre, feederData, machine, logger, controller, **kwargs):
        CommonFeederFrame.__init__(self,fenetre, feederData, machine, logger, controller,  **kwargs)


        basePlateFrame = tk.Frame(self, relief='sunken', borderwidth=3, padx=10, pady=10)
        self._basePlateDataFrame = tk.Frame(basePlateFrame)
        parametersFrame = tk.LabelFrame(self, text="Parameters", labelanchor='n', padx=10, pady=10)

        self._identificationFrame.grid(row=0, column=0, columnspan=2, sticky='ew')
        basePlateFrame.grid(row=1, column=0, columnspan=2, sticky='s')
        parametersFrame.grid(row=2, column=0, columnspan=2)
        self._btnFrame.grid(row=3, column=0, sticky='ew')
        self._testFrame.grid(row=3, column=1, sticky='ew')

        self._basePlateName = tk.Label(basePlateFrame, text='str')
        self.__basePlateList = ['Local']
        self.__strBasePlate = tk.StringVar(basePlateFrame)
        self.__strBasePlate.trace('w', self.__changeBasePlateTrace)
        self._basePlateOm = ttk.OptionMenu(basePlateFrame, self.__strBasePlate, *self.__basePlateList)
        self.updateBasePlateListOm()

        if feederData.basePlateId == 0 or feederData.basePlateId not in [bp.id for bp in machine.basePlateList]:
            self.__strBasePlate.set(self.__basePlateList[0])
        else:
            self.__strBasePlate.set(f'{feederData.basePlateId}')

        self._basePlateOm.grid(row=0, column=0)
        self._basePlateName.grid(row=0, column=1)
        self._basePlateDataFrame.grid(row=1, column=0, columnspan=2)





        self.componentPerStrip = CompleteEntry(parametersFrame, trashFunc, varType='int')
        self.componentPerStrip.var = feederData.componentPerStrip
        self.cmpStep = CompleteEntry(parametersFrame, trashFunc, varType='float')
        self.cmpStep.var = feederData.componentStep
        self.nextCmp = CompleteEntry(parametersFrame, trashFunc, varType='int')
        self.nextCmp.var = feederData.nextComponent
        self.idStripBp = CompleteEntry(parametersFrame, trashFunc, varType='int')
        self.idStripBp.var = feederData.stripIdInBasePlate

        tk.Label(parametersFrame, text="Cmp/strip").grid(row=0, column=0)
        self.componentPerStrip.grid(row=1, column=0)
        tk.Label(parametersFrame, text="Cmp step").grid(row=0, column=1)
        self.cmpStep.grid(row=1, column=1)
        tk.Label(parametersFrame, text="Next cmp").grid(row=0, column=2)
        self.nextCmp.grid(row=1, column=2)
        tk.Label(parametersFrame, text="Id strip in base plate").grid(row=0, column=3)
        self.idStripBp.grid(row=1, column=3)


    def __changeBasePlateTrace(self, *args):
        """
        Called when string of option menu change
        :param args:
        :return:
        """
        self.displayBasePlate(0 if self.__strBasePlate.get() == 'Local' else int(self.__strBasePlate.get()))

    def _save(self):

        newFeeder = fdr.StripFeeder(paramList={'id': self.id.var, 'name': self.name.var,
                                               'componentPerStrip': self.componentPerStrip.var,
                                               'stripIdInBasePlate': self.idStripBp.var,
                                               'componentStep': self.cmpStep.var, 'nextComponent': self.nextCmp.var,
                                               'basePlateId': int(
                                                   self.__strBasePlate.get()) if self.__strBasePlate.get() != 'Local'
                                               else 0,
                                               'localBasePlate': self._feeder.localBasePlate}, machine=self._machine)
        newFeeder.localBasePlate = fdr.BasePlateForStripFeeder({
            'id': self._bpFrame.id.var, 'name': self._bpFrame.name.var,
            'realRef1': {'X': self._bpFrame._ref1Frame.x, 'Y': self._bpFrame._ref1Frame.y,
                         'Z': self._bpFrame._ref1Frame.z},
            'realRef2': {'X': self._bpFrame._ref2Frame.x, 'Y': self._bpFrame._ref2Frame.y,
                         'Z': self._bpFrame._ref2Frame.z},
            'vectorRef': {'X': self._bpFrame._vectorFrame.x, 'Y': self._bpFrame._vectorFrame.y,
                          'Z': self._bpFrame._vectorFrame.z},
            'rotationOffset': math.radians(self._bpFrame._rotAndZFrame['Rot(deg)']),
            'zRamp': self._bpFrame._rotAndZFrame['Zramp'],
            'stripStep': self._bpFrame._misc['Strip Step'],
            'vectorFistCmp': {'X': self._bpFrame._vector.x, 'Y': self._bpFrame._vector.y, 'Z': self._bpFrame._vector.z}
        })

        self._feeder = newFeeder
        self._machine.addFeeder(newFeeder)
        self._machine.saveToXml()
        self._mother.updateFeederListOm()

    def updateBasePlateListOm(self):
        """
        Update the option menu with machine data ( base plate list).
        :return:
        """
        self.__basePlateList = ['Local'] + [str(feeder.id) for feeder in self._machine.basePlateList]
        del self.__basePlateList[self.__basePlateList.index('0')]
        menu = self._basePlateOm["menu"]
        menu.delete(0, "end")
        for basePlateStr in self.__basePlateList:
            menu.add_command(label=basePlateStr,
                             command=lambda value=basePlateStr: self.__strBasePlate.set(value))

    def displayBasePlate(self, basePlateId):
        """
        Change display base plate.
        If base plate id == 0 we take local information otherwise we take machine information.
        """
        for widget in self._basePlateDataFrame.winfo_children():
            widget.destroy()

        # self._basePlateDataFrame.grid_forget()
        bp = self._machine.getBasePlateById(basePlateId) if basePlateId != 0 else self._feeder.localBasePlate

        if bp:
            if bp.type == 'BasePlate':
                self._bpFrame = GenericBasePlateFrame(fenetre=self._basePlateDataFrame, bpData=bp,
                                                      machine=self._machine,
                                                      controller=self._controller, commandFrame=False,
                                                      logger=self._logger)
                self._bpFrame.grid(row=0, column=0)
                if basePlateId:
                    self._bpFrame.disableModification()

            elif bp.type == 'StripFeederBasePlate':
                self._bpFrame = StripFeederBasePlateFrame(fenetre=self._basePlateDataFrame, bpData=bp,
                                                          machine=self._machine,
                                                          controller=self._controller, commandFrame=False,
                                                          logger=self._logger)
                self._bpFrame.grid(row=0, column=0)
                if basePlateId:
                    self._bpFrame.disableModification()

            self._basePlateName['text'] = bp.name
        else:
            self._logger.printCout(f'{basePlateId} Base plate not found')

    # self._basePlateDataFrame.grid(row=1, column=0, columnspan=2)


class FeederFrame(tk.Frame):
    def __init__(self, fenetre, machineConf, logger, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)

        self._motherFrame = fenetre
        self.__newBtn = ttk.Button(self, command=self.__newFeederBtn, text='New')
        self.controller = controller
        self._machineConf = machineConf
        self._logger = logger
        self.__feederList = ['None']
        self.__strFeeder = tk.StringVar(self)
        self.__strFeeder.set(self.__feederList[0])

        self.__feederOm = ttk.OptionMenu(self, self.__strFeeder, *self.__feederList)

        self.__feederFrame = tk.Frame(self, width=500, height=500)

        self.__feederOm.grid(row=0, column=0)
        self.__newBtn.grid(row=0, column=1)
        self.__feederFrame.grid(row=1, column=0, columnspan=2)

        self.updateFeederListOm()
        self.__strFeeder.trace('w', self.__changeFeederTrace)

    def __changeFeederTrace(self, *args):
        """
        Called when string of option menu change
        :param args:
        :return:
        """
        self.displayFeeder(int(self.__strFeeder.get()))

    def updateFeederListOm(self):
        """
        Update the option menu with machine data ( feeder list).
        :return:
        """
        self.__feederList = [str(feeder.id) for feeder in self._machineConf.feederList]
        menu = self.__feederOm["menu"]
        menu.delete(0, "end")
        for string in self.__feederList:
            menu.add_command(label=string,
                             command=lambda value=string: self.__strFeeder.set(value))

    def __newFeederBtn(self):
        """
        Called by btn newFeeder.
        Display new feeder winwdows and go to __addFeeder if Ok is pressed else go to __cancelNewFeeder
        :return:
        """
        self._newFeedWindow = tk.Toplevel(self._motherFrame)
        self._newFeedWindow.title('Add feeder')
        # newFeedFrame = tk.Frame(newFeedWindow)

        listeOptions = ('Strip', 'Composite', 'Mechanical Reel')
        self._newFeederTypeSel = tk.StringVar()
        self._newFeederTypeSel.set(listeOptions[0])
        self._newFeederId = CompleteEntry(self._newFeedWindow, trashFunc, varType='int')
        om = ttk.OptionMenu(self._newFeedWindow, self._newFeederTypeSel, *listeOptions)
        om.configure(width=12)

        tk.Label(self._newFeedWindow, text='Type: ').grid(row=0, column=0, sticky='ew')
        om.grid(row=0, column=1, sticky='ew')
        tk.Label(self._newFeedWindow, text='Id: ').grid(row=1, column=0, sticky='ew')
        self._newFeederId.grid(row=1, column=1, sticky='ew')
        ttk.Button(self._newFeedWindow, text='Cancel', command=self._newFeedWindow.destroy).grid(row=2, column=0,
                                                                                                 sticky='ew')
        ttk.Button(self._newFeedWindow, text='Ok', command=self.__addFeeder).grid(row=2, column=1, sticky='ew')
        self._newFeedWindow.grab_set()  # Lock focus en new window

    def __addFeeder(self):
        """
        Called when create button was pressed in the new feeder windows
        :return:
        """
        self._newFeedWindow.destroy()

        if self._machineConf.getFeederById(self._newFeederId.var):
            MsgBox = messagebox.askokcancel('Feeder confirm',
                                            'Id {} already exist.\nContiniue?'.format(self._newFeederId.var),
                                            icon='warning')
            if not MsgBox:
                return

        newFeeder = None
        if self._newFeederTypeSel.get() == 'Strip':
            newFeeder = fdr.StripFeeder(paramList={'id': self._newFeederId.var}, machine=self._machineConf)
        elif self._newFeederTypeSel.get() == 'Composite':
            newFeeder = fdr.CompositeFeeder(paramList={'id': self._newFeederId.var}, machine=self._machineConf)
        elif self._newFeederTypeSel.get() == 'Mechanical Reel':
            newFeeder = fdr.MechanicalFeeder(paramList={'id': self._newFeederId.var}, machine=self._machineConf,
                                             driver=self.controller.driver)

        self._machineConf.addFeeder(newFeeder)
        self.__strFeeder.set(str(newFeeder.id))
        self.displayFeeder(newFeeder.id)

    def displayFeeder(self, feederId):
        """
        Display feeder on IHM.
        :param feederId: id of feeder
        :return:
        """
        self.__feederFrame.grid_forget()
        for feeder in self._machineConf.feederList:
            if feeder.id == feederId:
                if feeder.type == 'stripfeeder':
                    self.__feederFrame = StripFeederFrame(self, feeder, self._machineConf, self._logger,
                                                          self.controller)
                    self.__feederFrame.grid(row=1, column=0, columnspan=3)
                    return
                elif feeder.type == 'compositefeeder':
                    self.__feederFrame = CompositeFeederFrame(self, feeder, self._machineConf, self._logger,
                                                              self.controller)
                    self.__feederFrame.grid(row=1, column=0, columnspan=3)
                    return
                elif feeder.type == 'mechanicalfeeder':
                    self.__feederFrame = MechanicalFeederFrame(self, feeder, self._machineConf, self._logger,
                                                               self.controller)
                    self.__feederFrame.grid(row=1, column=0, columnspan=3)
                    return
                else:
                    self._logger.printCout(feeder.type + ': type cannot be loaded in IHM.')
        self._logger.printCout('{} Feeder not found'.format(feederId))

    def pick(self, idFeed, cmpid):
        self.controller.goToFeeder(idFeed=idFeed, idCmp=cmpid)
