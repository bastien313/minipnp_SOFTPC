# coding: utf-8

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
# from PnpDriver import Feeder
import serial.tools.list_ports
import tkinter.filedialog
from tkscrolledframe import ScrolledFrame
import math
import machine as mch


def trashFunc(*args):
    doNothing = 1


def checkDoubleEntry(value_if_allowed, text):
    """ Discard all character who is not a digit . + -
    Called after write charcter in Entry"""
    if text in '0123456789.-+':
        try:
            float(value_if_allowed)
            return True
        except ValueError:
            return False
    else:
        return False


def checkIntEntry(value_if_allowed, text):
    """ Discard all character who is not a digit . + -
    Called after write charcter in Entry"""
    if text in '0123456789':
        try:
            int(value_if_allowed)
            return True
        except ValueError:
            return False
    else:
        return False


class ScrollableFrame(tk.Frame):
    """
    Vertical and horizontal scrolable frame.
    use ScrollableFrame.userFrame for put widget into.
    Use set size to expand the maximum view.
    """

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        vsb = tk.Scrollbar(self, orient=tk.VERTICAL)
        vsb.grid(row=0, column=1, sticky=tk.N + tk.S)
        hsb = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hsb.grid(row=1, column=0, sticky=tk.E + tk.W)
        self._c = tk.Canvas(self, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._c.grid(row=0, column=0, sticky="news")

        vsb.config(command=self._c.yview)
        hsb.config(command=self._c.xview)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._fr = tk.Frame(self._c)

        self._c.create_window(0, 0, window=self._fr)
        self._fr.update_idletasks()
        self._c.config(scrollregion=self._c.bbox("all"))

        self._fr.bind("<Configure>",
                      self.onFrameConfigure)  # bind an event whenever the size of the viewPort frame changes.
        # self._c.bind("<Configure>",
        #                 self.onCanvasConfigure)  # bind an event whenever the size of the viewPort frame changes.

        self.onFrameConfigure(
            None)  # perform an initial stretch on render, otherwise the scroll region has a tiny border until the first resize

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self._c.configure(scrollregion=self._c.bbox("all"))

    def setSize(self, width, height):
        self._c.configure(width=width, height=height)

    def __getUserFrame(self):
        return self._fr

    userFrame = property(fget=__getUserFrame)


class BoarDrawing(tk.Frame):
    def __init__(self, fenetre, *args, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)
        self.motherFram = fenetre

        vsb = tk.Scrollbar(self, orient=tk.VERTICAL)
        vsb.grid(row=0, column=1, sticky=tk.N + tk.S)
        hsb = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hsb.grid(row=1, column=0, sticky=tk.E + tk.W)

        self._c = tk.Canvas(self, yscrollcommand=vsb.set, xscrollcommand=hsb.set, bg="white")
        self._c.configure(width=500, height=400)

        vsb.config(command=self._c.yview)
        hsb.config(command=self._c.xview)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._c.grid(row=0, column=0, sticky="news")

        self.scale = 4

        # self.grid_rowconfigure(0, weight=1)
        # self.grid_columnconfigure(0, weight=1)

    def __drawRotatedCmp(self, cmp, modelList, board):
        """
        Draw a square wich represent component
        :param cmp: component to draw.
        :return:
        """
        cmpSizeX = modelList[cmp.model].width * self.scale
        cmpSizeY = modelList[cmp.model].length * self.scale
        posX = ((cmp.posX) * self.scale) - cmpSizeX / 2.0
        posY = self._c.winfo_reqheight() - (((cmp.posY) * self.scale) - cmpSizeY / 2.0)
        points = [
            [posX, posY],
            [posX + cmpSizeX, posY],
            [posX + cmpSizeX, posY - cmpSizeY],
            [posX, posY - cmpSizeY],
        ]
        """
        if cmp.rot > 180.0:
            angle = math.radians(180.0-cmp.rot)
        else:
            angle = math.radians(cmp.rot)
        """
        angle = math.radians(cmp.rot + board.angleCorr)
        # angle = math.radians(270.0)
        cos_val = math.cos(angle)
        sin_val = math.sin(angle)
        cx = ((cmp.posX) * self.scale)
        cy = self._c.winfo_reqheight() - ((cmp.posY) * self.scale)
        new_points = []
        for x_old, y_old in points:
            x_old -= cx
            y_old -= cy
            x_new = x_old * cos_val - y_old * sin_val
            y_new = x_old * sin_val + y_old * cos_val
            new_points.append([x_new + cx, y_new + cy])

        self._c.create_polygon(new_points, fill='brown')

    def drawBoard(self, board, modelList):
        self._c.delete("all")
        self._c.create_rectangle(0, self._c.winfo_reqheight(), board.xSize * self.scale,
                                 self._c.winfo_reqheight() - (board.ySize * self.scale), fill='green')

        for cmp in board.cmpDic.values():
            self.__drawRotatedCmp(cmp, modelList, board)
            self._c.configure(scrollregion=self._c.bbox("all"))


class entryWindow():
    def __init__(self, frame, name, lstLab, listEntry, cbValid, cbDiscart):
        """
        Initialise litle windows
        :param frame, parant frame:
        :param name , name of window:
        :param lstLab, list of label:
        :param listEntry, list of label wich represent key of each Entry:
        :param cbValid, calback of button OK:
        :param cbDiscart, calback of button Cancel:
        """
        self._tl = tk.Toplevel(frame)
        userFrame = tk.Frame(self._tl)
        btnFrame = tk.Frame(self._tl)

        self._tl.title(name)

        self._listLab = []
        self._dicVal = {}
        self._dicEntry = {}
        self._cbValid = cbValid
        self._cbDiscart = cbDiscart

        for elem in lstLab:
            self._listLab.append(tk.Label(userFrame, text=elem))

        for elem in listEntry:
            self._dicVal[elem] = tk.StringVar()
            self._dicEntry[elem] = tk.Entry(userFrame, textvariable=self._dicVal[elem], width=15)

        id = 0
        for elem in self._listLab:
            elem.grid(row=id, column=0)
            id += 1

        id = 0
        for elem in self._dicEntry.values():
            elem.grid(row=id, column=1)
            id += 1

        btnOk = tk.Button(btnFrame, text='OK', command=self.__okBtn)
        btnCanc = tk.Button(btnFrame, text='Cancel', command=self.__cancelBtn)

        btnCanc.grid(row=0, column=0)
        btnOk.grid(row=0, column=1)

        userFrame.grid(row=0, column=0)
        btnFrame.grid(row=1, column=0)

    def __okBtn(self):
        listOut = {}

        for key, elem in self._dicVal.items():
            listOut[key] = elem.get()

        if self._cbValid:
            self._cbValid(listOut)
        self._tl.destroy()

    def __cancelBtn(self):
        if self._cbDiscart:
            self._cbDiscart()
        self._tl.destroy()


class completeEntry(tk.Entry):
    """
    Entry wich contain its own Var and traceCotrol.
    Used for disable trace when var is not edited by user IHM.
    """

    def __init__(self, frame, traceFunc, varType='str'):
        tk.Entry.__init__(self, frame, width=15, state='normal')
        self._frame = frame
        self._traceFunc = traceFunc
        if varType == 'int':
            self._var = tk.IntVar(self._frame, 1)
            checkEntryCmdInt = self._frame.register(checkIntEntry)
            self.configure(validate='key', textvariable=self._var, validatecommand=(checkEntryCmdInt, '%P', '%S'))
        elif varType == 'double':
            self._var = tk.DoubleVar(self._frame, 1.0)
            checkEntryCmdDouble = self._frame.register(checkDoubleEntry)
            self.configure(validate='key', textvariable=self._var, validatecommand=(checkEntryCmdDouble, '%P', '%S'))
        else:
            self._var = tk.StringVar(self._frame, "str")
            self.configure(textvariable=self._var)

        self._var.trace_id = self._var.trace("w", self._traceFunc)

    def _getVar(self):
        return self._var.get()

    def _setVar(self, val):
        self._var.trace_vdelete("w", self._var.trace_id)
        self._var.set(val)
        self._var.trace_id = self._var.trace("w", self._traceFunc)

    var = property(fset=_setVar, fget=_getVar)


class StripFeederFrame(tk.Frame):
    def __init__(self, fenetre, feederData, machine, logger, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)

        identificationFrame = tk.LabelFrame(self, text="Identification", labelanchor='n', padx=10, pady=10)
        parametersFrame = tk.LabelFrame(self, text="Parameters", labelanchor='n', padx=10, pady=10)
        btnFram = tk.LabelFrame(self, text="Command", labelanchor='n', padx=10, pady=10)
        testFrame = tk.LabelFrame(self, text="Test", labelanchor='n', padx=10, pady=10)

        identificationFrame.grid(row=0, column=0)
        parametersFrame.grid(row=1, column=0)
        btnFram.grid(row=2, column=0)
        testFrame.grid(row=2, column=1)

        posFirstCmpFrame = tk.LabelFrame(parametersFrame, text="First component", labelanchor='n', padx=10, pady=10)
        posLastCmpFrame = tk.LabelFrame(parametersFrame, text="Last component", labelanchor='n', padx=10, pady=10)
        otherParam = tk.LabelFrame(parametersFrame, text="Other", labelanchor='n', padx=10, pady=10)

        posFirstCmpFrame.grid(row=0, column=0)
        posLastCmpFrame.grid(row=0, column=1)
        otherParam.grid(row=0, column=2)

        self.__mother = fenetre
        self.__machine = machine
        self.__logger = logger
        self.id = completeEntry(identificationFrame, trashFunc, varType='int')
        self.id.var = feederData.id
        self.id['width'] = 20
        self.type = completeEntry(identificationFrame, trashFunc, varType='str')
        self.type.var = feederData.type
        self.type['state'] = 'disable'
        self.type['width'] = 30
        self.name = completeEntry(identificationFrame, trashFunc, varType='str')
        self.name.var = feederData.name
        self.name['width'] = 50

        tk.Label(identificationFrame, text="Id").grid(row=0, column=0)
        self.id.grid(row=1, column=0)
        tk.Label(identificationFrame, text="Type").grid(row=0, column=1)
        self.type.grid(row=1, column=1)
        tk.Label(identificationFrame, text="Name").grid(row=0, column=2)
        self.name.grid(row=1, column=2)

        self.xFirst = completeEntry(posFirstCmpFrame, trashFunc, varType='float')
        self.xFirst.var = feederData.pos['X']
        self.yFirst = completeEntry(posFirstCmpFrame, trashFunc, varType='float')
        self.yFirst.var = feederData.pos['Y']
        self.zFirst = completeEntry(posFirstCmpFrame, trashFunc, varType='float')
        self.zFirst.var = feederData.pos['Z']

        tk.Label(posFirstCmpFrame, text="X").grid(row=0, column=0)
        self.xFirst.grid(row=0, column=1)
        tk.Label(posFirstCmpFrame, text="Y").grid(row=1, column=0)
        self.yFirst.grid(row=1, column=1)
        tk.Label(posFirstCmpFrame, text="Z").grid(row=2, column=0)
        self.zFirst.grid(row=2, column=1)

        self.xLast = completeEntry(posLastCmpFrame, trashFunc, varType='float')
        self.xLast.var = feederData.endPos['X']
        self.yLast = completeEntry(posLastCmpFrame, trashFunc, varType='float')
        self.yLast.var = feederData.endPos['Y']

        tk.Label(posLastCmpFrame, text="X").grid(row=0, column=0)
        self.xLast.grid(row=0, column=1)
        tk.Label(posLastCmpFrame, text="Y").grid(row=1, column=0)
        self.yLast.grid(row=1, column=1)

        self.stripAmount = completeEntry(otherParam, trashFunc, varType='int')
        self.stripAmount.var = feederData.stripAmount
        self.componentPerStrip = completeEntry(otherParam, trashFunc, varType='int')
        self.componentPerStrip.var = feederData.componentPerStrip
        self.stripStep = completeEntry(otherParam, trashFunc, varType='float')
        self.stripStep.var = feederData.stripStep
        self.cmpStep = completeEntry(otherParam, trashFunc, varType='float')
        self.cmpStep.var = feederData.cmpStep

        tk.Label(otherParam, text="Strip nb").grid(row=0, column=0)
        self.stripAmount.grid(row=0, column=1)
        tk.Label(otherParam, text="Cmp/strip").grid(row=1, column=0)
        self.componentPerStrip.grid(row=1, column=1)
        tk.Label(otherParam, text="Strip step").grid(row=2, column=0)
        self.stripStep.grid(row=2, column=1)
        tk.Label(otherParam, text="Cmp step").grid(row=3, column=0)
        self.cmpStep.grid(row=3, column=1)

        tk.Button(btnFram, command=self.__save, text='Save').grid(row=0, column=0)
        tk.Button(btnFram, command=self.__delete, text='Delete').grid(row=0, column=1)

        self.pickId = completeEntry(testFrame, trashFunc, varType='int')
        self.stripId = completeEntry(testFrame, trashFunc, varType='int')
        self.pickId.var = 0
        self.stripId.var = 0

        tk.Label(testFrame, text="Strip").grid(row=0, column=0)
        self.stripId.grid(row=0, column=1)
        tk.Label(testFrame, text="Cmp").grid(row=1, column=0)
        self.pickId.grid(row=1, column=1)
        tk.Button(testFrame, command=self.__pick, text='Pick').grid(row=0, column=2)

    def __save(self):
        newFeeder = mch.StripFeeder({'id': self.id.var, 'name': self.name.var,
                                     'xPos': self.xFirst.var, 'yPos': self.yFirst.var, 'zPos': self.zFirst.var,
                                     'xEndPos': self.xLast.var, 'yEndPos': self.yLast.var,
                                     'stripAmount': self.stripAmount.var,
                                     'componentPerStrip': self.componentPerStrip.var,
                                     'cmpStep': self.cmpStep.var, 'stripStep': self.stripStep.var},
                                      self.__machine.saveToXml)
        self.__machine.addFeeder(newFeeder)
        self.__machine.saveToXml()
        self.__mother.updateFeederListOm()

    def __delete(self):
        self.__machine.deleteFeeder(self.id.var)
        self.__machine.saveToXml()
        self.__mother.updateFeederListOm()
        self.__mother.displayFeeder(0)

    def __pick(self):
        self.__mother.pick(self.id.var, self.pickId.var, self.stripId.var)


class FeederFrame(tk.Frame):
    def __init__(self, fenetre, machineConf, logger, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)

        self.__newBtn = tk.Button(self, command=self.__addFeeder, text='New')
        self.controller = controller
        self.__machineConf = machineConf
        self.__logger = logger
        self.__feederList = ['None']
        self.__strFeeder = tk.StringVar(self)
        self.__strFeeder.set(self.__feederList[0])

        self.__feederOm = tk.OptionMenu(self, self.__addFeeder, *self.__feederList)

        self.__feederFrame = tk.Frame(self, width=500, height=500)

        self.__feederOm.grid(row=0, column=0)
        self.__newBtn.grid(row=0, column=1)
        self.__feederFrame.grid(row=1, column=0, columnspan=2)

        self.updateFeederListOm()
        self.__strFeeder.trace('w', self.__changeFeederTrace)

    def __changeFeederTrace(self, *args):
        """
        Called when string of option me nu change
        :param args:
        :return:
        """
        self.displayFeeder(int(self.__strFeeder.get()))

    def updateFeederListOm(self):
        """
        Update the option menu with machine data ( feeder list).
        :return:
        """
        self.__feederList = [str(feeder.id) for feeder in self.__machineConf.feederList]
        menu = self.__feederOm["menu"]
        menu.delete(0, "end")
        for string in self.__feederList:
            menu.add_command(label=string,
                             command=lambda value=string: self.__strFeeder.set(value))

    def __addFeeder(self):
        """
        Créate feeder 0 on machine (feeder list)
        Anad display it on IHM.
        :param strFeeder:
        :return:
        """
        newFeeder = mch.StripFeeder({},self.__machineConf.saveToXml)
        self.__machineConf.addFeeder(newFeeder)
        self.__strFeeder.set(str(newFeeder.id))

    def displayFeeder(self, feederId):
        """
        Display feeder on IHM.
        :param feederId: id of feeder
        :return:
        """
        self.__feederFrame.grid_forget()
        for feeder in self.__machineConf.feederList:
            if feeder.id == feederId:
                if feeder.type == 'stripfeeder':
                    self.__feederFrame = StripFeederFrame(self, feeder, self.__machineConf, self.__logger)
                    self.__feederFrame.grid(row=1, column=0, columnspan=3)
                    return
                else:
                    self.__logger.printCout(feeder.type + ': type cannot be loaded in IHM.')
        self.__logger.printCout('{} Feeder not found'.format(feederId))

    def pick(self, idFeed, cmpid, idStrip):
        self.controller.goToFeeder(idFeed=idFeed, idCmp=cmpid, idStrip=idStrip)


class ParamFrame(tk.Frame):
    def __init__(self, fenetre, controller, machineConf, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)
        self.controller = controller
        self.controller.ihm = self
        checkEntryCmdDouble = self.register(checkDoubleEntry)
        checkEntryCmdInt = self.register(checkIntEntry)

        self._machineConf = machineConf
        self._frameAxis = tk.LabelFrame(self, text="Axis", labelanchor='n', padx=10, pady=10)
        self._frameRef = tk.LabelFrame(self, text="References", labelanchor='n', padx=10, pady=10)
        self._frameMisc = tk.LabelFrame(self, text="Misc", labelanchor='n', padx=10, pady=10)

        self._frameX = tk.LabelFrame(self._frameAxis, text="X", labelanchor='n', padx=10, pady=10)
        self._frameY = tk.LabelFrame(self._frameAxis, text="Y", labelanchor='n', padx=10, pady=10)
        self._frameZ = tk.LabelFrame(self._frameAxis, text="Z", labelanchor='n', padx=10, pady=10)
        self._frameC = tk.LabelFrame(self._frameAxis, text="C", labelanchor='n', padx=10, pady=10)
        self._frameScan = tk.LabelFrame(self._frameRef, text="Scan", labelanchor='n', padx=10, pady=10)
        self._frameBoard = tk.LabelFrame(self._frameRef, text="Board", labelanchor='n', padx=10, pady=10)
        self._frameTrash = tk.LabelFrame(self._frameRef, text="Trash", labelanchor='n', padx=10, pady=10)

        self._XstepBymmEntry = completeEntry(self._frameX, self.__paramChange, 'double')
        self._XmaxAccelEntry = completeEntry(self._frameX, self.__paramChange, 'double')
        self._XmaxSpeedEntry = completeEntry(self._frameX, self.__paramChange, 'double')

        self._XstepBymmEntry.configure(state='normal')
        tk.Label(self._frameX, text="Step/mm").grid(row=0, column=0)
        self._XstepBymmEntry.grid(row=1, column=0)
        tk.Label(self._frameX, text="Speed (mm/s)").grid(row=2, column=0)
        self._XmaxSpeedEntry.grid(row=3, column=0)
        tk.Label(self._frameX, text="Accel (mm/s²)").grid(row=4, column=0)
        self._XmaxAccelEntry.grid(row=5, column=0)

        self._YstepBymmEntry = completeEntry(self._frameY, self.__paramChange, 'double')
        self._YmaxAccelEntry = completeEntry(self._frameY, self.__paramChange, 'double')
        self._YmaxSpeedEntry = completeEntry(self._frameY, self.__paramChange, 'double')

        tk.Label(self._frameY, text="Step/mm").grid(row=0, column=0)
        self._YstepBymmEntry.grid(row=1, column=0)
        tk.Label(self._frameY, text="Speed (mm/s)").grid(row=2, column=0)
        self._YmaxSpeedEntry.grid(row=3, column=0)
        tk.Label(self._frameY, text="Accel (mm/s²)").grid(row=4, column=0)
        self._YmaxAccelEntry.grid(row=5, column=0)

        self._ZstepBymmEntry = completeEntry(self._frameZ, self.__paramChange, 'double')
        self._ZmaxAccelEntry = completeEntry(self._frameZ, self.__paramChange, 'double')
        self._ZmaxSpeedEntry = completeEntry(self._frameZ, self.__paramChange, 'double')

        tk.Label(self._frameZ, text="Step/mm").grid(row=0, column=0)
        self._ZstepBymmEntry.grid(row=1, column=0)
        tk.Label(self._frameZ, text="Speed (mm/s)").grid(row=2, column=0)
        self._ZmaxSpeedEntry.grid(row=3, column=0)
        tk.Label(self._frameZ, text="Accel (mm/s)²").grid(row=4, column=0)
        self._ZmaxAccelEntry.grid(row=5, column=0)

        self._CstepBymmEntry = completeEntry(self._frameC, self.__paramChange, 'double')
        self._CmaxAccelEntry = completeEntry(self._frameC, self.__paramChange, 'double')
        self._CmaxSpeedEntry = completeEntry(self._frameC, self.__paramChange, 'double')

        tk.Label(self._frameC, text="Step/deg").grid(row=0, column=0)
        self._CstepBymmEntry.grid(row=1, column=0)
        tk.Label(self._frameC, text="Speed (deg/s)").grid(row=2, column=0)
        self._CmaxSpeedEntry.grid(row=3, column=0)
        tk.Label(self._frameC, text="Accel (deg/s²)").grid(row=4, column=0)
        self._CmaxAccelEntry.grid(row=5, column=0)

        self._XposScanEntry = completeEntry(self._frameScan, self.__paramChange, 'double')
        self._YposScanEntry = completeEntry(self._frameScan, self.__paramChange, 'double')
        self._ZposScanEntry = completeEntry(self._frameScan, self.__paramChange, 'double')

        tk.Label(self._frameScan, text="X").grid(row=0, column=0)
        self._XposScanEntry.grid(row=1, column=0)
        tk.Label(self._frameScan, text="Y").grid(row=2, column=0)
        self._YposScanEntry.grid(row=3, column=0)
        tk.Label(self._frameScan, text="Z").grid(row=4, column=0)
        self._ZposScanEntry.grid(row=5, column=0)

        self._XposBoardEntry = completeEntry(self._frameBoard, self.__paramChange, 'double')
        self._YposBoardEntry = completeEntry(self._frameBoard, self.__paramChange, 'double')
        self._ZposBoardEntry = completeEntry(self._frameBoard, self.__paramChange, 'double')

        tk.Label(self._frameBoard, text="X").grid(row=0, column=0)
        self._XposBoardEntry.grid(row=1, column=0)
        tk.Label(self._frameBoard, text="Y").grid(row=2, column=0)
        self._YposBoardEntry.grid(row=3, column=0)
        tk.Label(self._frameBoard, text="Z").grid(row=4, column=0)
        self._ZposBoardEntry.grid(row=5, column=0)

        self._XposTrashEntry = completeEntry(self._frameTrash, self.__paramChange, 'double')
        self._YposTrashEntry = completeEntry(self._frameTrash, self.__paramChange, 'double')
        self._ZposTrashEntry = completeEntry(self._frameTrash, self.__paramChange, 'double')

        tk.Label(self._frameTrash, text="X").grid(row=0, column=0)
        self._XposTrashEntry.grid(row=1, column=0)
        tk.Label(self._frameTrash, text="Y").grid(row=2, column=0)
        self._YposTrashEntry.grid(row=3, column=0)
        tk.Label(self._frameTrash, text="Z").grid(row=4, column=0)
        self._ZposTrashEntry.grid(row=5, column=0)

        self._ZposHeadEntry = completeEntry(self._frameMisc, self.__paramChange, 'double')
        self._ZposHeadLab = tk.Label(self._frameMisc, text="Z Head")
        self._ZLiftEntry = completeEntry(self._frameMisc, self.__paramChange, 'double')
        self._ZLiftLab = tk.Label(self._frameMisc, text="Z Lift")

        self._ZposHeadLab.grid(row=0, column=0)
        self._ZposHeadEntry.grid(row=1, column=0)
        self._ZLiftLab.grid(row=2, column=0)
        self._ZLiftEntry.grid(row=3, column=0)

        self._frameX.grid(row=0, column=0)
        self._frameY.grid(row=0, column=1)
        self._frameZ.grid(row=0, column=2)
        self._frameC.grid(row=0, column=3)

        self._frameScan.grid(row=0, column=0, rowspan=2, sticky='ns')
        self._frameBoard.grid(row=0, column=1, rowspan=2, sticky='ns')
        self._frameTrash.grid(row=0, column=2, rowspan=2, sticky='ns')

        self._frameAxis.grid(row=0, column=0, columnspan=4)
        self._frameRef.grid(row=1, column=0, columnspan=3,rowspan=2, sticky='ns')
        self._frameMisc.grid(row=1, column=3, sticky='ns')
        tk.Button(self, text='Save', command=self.__paramSave).grid(row=2, column=3)

    def __paramSave(self):
        self._machineConf.saveToXml()

    def __paramChange(self, *args):
        """
        Update machien conf when user change by IHM
        :return:
        """
        self._machineConf.axisConfArray['X'].speed = self._XmaxSpeedEntry.var
        self._machineConf.axisConfArray['Y'].speed = self._YmaxSpeedEntry.var
        self._machineConf.axisConfArray['Z'].speed = self._ZmaxSpeedEntry.var
        self._machineConf.axisConfArray['C'].speed = self._CmaxSpeedEntry.var

        self._machineConf.axisConfArray['X'].accel = self._XmaxAccelEntry.var
        self._machineConf.axisConfArray['Y'].accel = self._YmaxAccelEntry.var
        self._machineConf.axisConfArray['Z'].accel = self._ZmaxAccelEntry.var
        self._machineConf.axisConfArray['C'].accel = self._CmaxAccelEntry.var

        self._machineConf.axisConfArray['X'].step = self._XstepBymmEntry.var
        self._machineConf.axisConfArray['Y'].step = self._YstepBymmEntry.var
        self._machineConf.axisConfArray['Z'].step = self._ZstepBymmEntry.var
        self._machineConf.axisConfArray['C'].step = self._CstepBymmEntry.var

        self._machineConf.scanPosition['X'] = self._XposScanEntry.var
        self._machineConf.scanPosition['Y'] = self._YposScanEntry.var
        self._machineConf.scanPosition['Z'] = self._ZposScanEntry.var

        self._machineConf.boardRefPosition['X'] = self._XposBoardEntry.var
        self._machineConf.boardRefPosition['Y'] = self._YposBoardEntry.var
        self._machineConf.boardRefPosition['Z'] = self._ZposBoardEntry.var

        self._machineConf.trashPosition['X'] = self._XposTrashEntry.var
        self._machineConf.trashPosition['Y'] = self._YposTrashEntry.var
        self._machineConf.trashPosition['Z'] = self._ZposTrashEntry.var

        self._ZposHeadEntry.var = self._machineConf.zHead
        self._ZLiftEntry.var = self._machineConf.zLift

    def update(self):
        """
        Update IHM with data in machi,e.
        :return:
        """
        self._XmaxSpeedEntry.var = self._machineConf.axisConfArray['X'].speed
        self._YmaxSpeedEntry.var = self._machineConf.axisConfArray['Y'].speed
        self._ZmaxSpeedEntry.var = self._machineConf.axisConfArray['Z'].speed
        self._CmaxSpeedEntry.var = self._machineConf.axisConfArray['C'].speed

        self._XmaxAccelEntry.var = self._machineConf.axisConfArray['X'].accel
        self._YmaxAccelEntry.var = self._machineConf.axisConfArray['Y'].accel
        self._ZmaxAccelEntry.var = self._machineConf.axisConfArray['Z'].accel
        self._CmaxAccelEntry.var = self._machineConf.axisConfArray['C'].accel

        self._XstepBymmEntry.var = self._machineConf.axisConfArray['X'].step
        self._YstepBymmEntry.var = self._machineConf.axisConfArray['Y'].step
        self._ZstepBymmEntry.var = self._machineConf.axisConfArray['Z'].step
        self._CstepBymmEntry.var = self._machineConf.axisConfArray['C'].step

        self._XposScanEntry.var = self._machineConf.scanPosition['X']
        self._YposScanEntry.var = self._machineConf.scanPosition['Y']
        self._ZposScanEntry.var = self._machineConf.scanPosition['Z']

        self._XposBoardEntry.var = self._machineConf.boardRefPosition['X']
        self._YposBoardEntry.var = self._machineConf.boardRefPosition['Y']
        self._ZposBoardEntry.var = self._machineConf.boardRefPosition['Z']

        self._XposTrashEntry.var = self._machineConf.trashPosition['X']
        self._YposTrashEntry.var = self._machineConf.trashPosition['Y']
        self._ZposTrashEntry.var = self._machineConf.trashPosition['Z']

        self._ZposHeadEntry.var = self._machineConf.zHead
        self._ZLiftEntry.var = self._machineConf.zLift


class SerialFrame(tk.LabelFrame):
    def __init__(self, fenetre, controller, **kwargs):
        tk.LabelFrame.__init__(self, fenetre, **kwargs)
        self.controller = controller

        self._listCom = ['0']
        self._comSel = tk.StringVar(self)
        self._comSelOM = tk.OptionMenu(self, self._comSel, *self._listCom)
        self._comSelOM['width'] = 7
        self._serialSpeedLab = tk.Label(self, text="Speed")
        self._comSpeedVar = tk.IntVar(self, 115200)
        self._comSpeedEntry = completeEntry(self, trashFunc(), varType='int')
        self._comSpeedEntry.var = 115200

        self._openBtn = tk.Button(self, text='Open', command=self.__openCom)
        self._closeBtn = tk.Button(self, text='Close', command=self.__closeCom)

        self._comSelOM.grid(row=0, column=0)
        self._serialSpeedLab.grid(row=1, column=1)
        self._comSpeedEntry.grid(row=2, column=1)
        self._openBtn.grid(row=3, column=1)
        self._closeBtn.grid(row=4, column=1)

    def __openCom(self):
        self.controller.openCom(self._comSel.get(), self._comSpeedVar.get())

    def __closeCom(self):
        self.controller.closeCom()

    def __deleteComList(self):
        self._listCom = []
        menu = self._comSelOM["menu"]
        menu.delete(0, "end")

    def listCom(self, *args):
        self.__deleteComList()

        liste = serial.tools.list_ports.comports()
        for port in liste:
            self._listCom.append(port.device)
        menu = self._comSelOM["menu"]
        for string in self._listCom:
            menu.add_command(label=string,
                             command=lambda value=string: self._comSel.set(value))


class CtrlFrame(tk.Frame):
    """Frame used for direct control of Pnp."""

    def __init__(self, fenetre, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)
        self.controller = controller
        self.controller.ihm = self

        checkEntryCmdDouble = self.register(checkDoubleEntry)
        checkEntryCmdInt = self.register(checkIntEntry)

        self._frameArrow = tk.LabelFrame(self, text="Control", labelanchor='n', padx=10, pady=10)
        self._frameAuxCtrl = tk.LabelFrame(self, text="Aux control", labelanchor='n', padx=20, pady=10)
        self._frameHome = tk.LabelFrame(self._frameAuxCtrl, text="Home", labelanchor='n', padx=5, pady=5)
        self._frameConfArrow = tk.LabelFrame(self, text="Control configuration", labelanchor='n', padx=10, pady=10)
        self._framePos = tk.LabelFrame(self, text="Position", labelanchor='n', padx=10, pady=10)
        self._frameConsole = tk.LabelFrame(self, text="Console", labelanchor='n', padx=10, pady=10)
        self.serialFrame = SerialFrame(self, self.controller, text='Serial', labelanchor='n', padx=5, pady=5)

        self._xp = tk.Button(self._frameArrow, text='X+', height=2, width=4)
        self._xm = tk.Button(self._frameArrow, text='X-', height=2, width=4)
        self._yp = tk.Button(self._frameArrow, text='Y+', height=2, width=4)
        self._ym = tk.Button(self._frameArrow, text='Y-', height=2, width=4)
        self._zp = tk.Button(self._frameArrow, text='Z+', height=2, width=4)
        self._zm = tk.Button(self._frameArrow, text='Z-', height=2, width=4)
        self._cp = tk.Button(self._frameArrow, text='C+', height=2, width=4)
        self._cm = tk.Button(self._frameArrow, text='C-', height=2, width=4)

        self._xp.bind("<ButtonPress>", self.controller.xpPress)
        self._xp.bind("<ButtonRelease>", self.controller.xRelease)
        self._xm.bind("<ButtonPress>", self.controller.xmPress)
        self._xm.bind("<ButtonRelease>", self.controller.xRelease)

        self._yp.bind("<ButtonPress>", self.controller.ypPress)
        self._yp.bind("<ButtonRelease>", self.controller.yRelease)
        self._ym.bind("<ButtonPress>", self.controller.ymPress)
        self._ym.bind("<ButtonRelease>", self.controller.yRelease)

        self._zp.bind("<ButtonPress>", self.controller.zpPress)
        self._zp.bind("<ButtonRelease>", self.controller.zRelease)
        self._zm.bind("<ButtonPress>", self.controller.zmPress)
        self._zm.bind("<ButtonRelease>", self.controller.zRelease)

        self._cp.bind("<ButtonPress>", self.controller.cpPress)
        self._cp.bind("<ButtonRelease>", self.controller.cRelease)
        self._cm.bind("<ButtonPress>", self.controller.cmPress)
        self._cm.bind("<ButtonRelease>", self.controller.cRelease)

        self._xp.grid(row=1, column=2)
        self._xm.grid(row=1, column=0)
        self._yp.grid(row=0, column=1)
        self._ym.grid(row=2, column=1)
        self._zp.grid(row=0, column=3, padx=10)
        self._zm.grid(row=2, column=3, padx=10)
        self._cp.grid(row=0, column=4, padx=10)
        self._cm.grid(row=2, column=4, padx=10)

        self._homeX = tk.Button(self._frameHome, text='X', height=2, width=4, command=self.controller.homeX)
        self._homeY = tk.Button(self._frameHome, text='Y', height=2, width=4, command=self.controller.homeY)
        self._homeZ = tk.Button(self._frameHome, text='Z', height=2, width=4, command=self.controller.homeZ)
        self._homeC = tk.Button(self._frameHome, text='C', height=2, width=4, command=self.controller.homeC)
        self._homeALL = tk.Button(self._frameHome, text='ALL', height=2, width=4, command=self.controller.homeAll)

        self._homeX.grid(row=0, column=0)
        self._homeY.grid(row=0, column=1)
        self._homeZ.grid(row=0, column=2)
        self._homeC.grid(row=0, column=3)
        self._homeALL.grid(row=0, column=4)

        self._evVar = tk.IntVar(self._frameConfArrow, 1)
        self._pumpVar = tk.IntVar(self._frameConfArrow, 1)
        self._evEna = tk.Checkbutton(self._frameAuxCtrl, text='EV', variable=self._evVar,
                                     command=self.controller.evControl)
        self._pumpEna = tk.Checkbutton(self._frameAuxCtrl, text='Pump', variable=self._pumpVar,
                                       command=self.controller.pumpControl)

        self._frameHome.grid(row=0, column=0, columnspan=2, sticky='nesw')
        self._evEna.grid(row=1, column=0)
        self._pumpEna.grid(row=1, column=1)

        self._labStep = tk.Label(self._frameConfArrow, text="Step(mm | °)")
        self._labX = tk.Label(self._frameConfArrow, text="X")
        self._labY = tk.Label(self._frameConfArrow, text="Y")
        self._labZ = tk.Label(self._frameConfArrow, text="Z")
        self._labC = tk.Label(self._frameConfArrow, text="C")

        self._stepX = tk.DoubleVar(self._frameConfArrow, 0.1)
        self._stepY = tk.DoubleVar(self._frameConfArrow, 0.1)
        self._stepZ = tk.DoubleVar(self._frameConfArrow, 0.1)
        self._stepC = tk.DoubleVar(self._frameConfArrow, 0.1)
        self._stepXEntry = tk.Entry(self._frameConfArrow, textvariable=self._stepX, width=15,
                                    validate='key', validatecommand=(checkEntryCmdDouble, '%P', '%S'))
        self._stepYEntry = tk.Entry(self._frameConfArrow, textvariable=self._stepY, width=15,
                                    validate='key', validatecommand=(checkEntryCmdDouble, '%P', '%S'))
        self._stepZEntry = tk.Entry(self._frameConfArrow, textvariable=self._stepZ, width=15,
                                    validate='key', validatecommand=(checkEntryCmdDouble, '%P', '%S'))
        self._stepCEntry = tk.Entry(self._frameConfArrow, textvariable=self._stepC, width=15,
                                    validate='key', validatecommand=(checkEntryCmdDouble, '%P', '%S'))

        self._contEnaVar = tk.IntVar(self._frameConfArrow, 1)
        self._contEna = tk.Checkbutton(self._frameConfArrow, variable=self._contEnaVar)
        self._contEna.configure(command=self.controller.continueControl)

        self._labStep.grid(row=0, column=1)
        tk.Label(self._frameConfArrow, text='Continue').grid(row=0, column=2, columnspan=2)
        self._labX.grid(row=1, column=0)
        self._labY.grid(row=2, column=0)
        self._labZ.grid(row=3, column=0)
        self._labC.grid(row=4, column=0)
        self._stepXEntry.grid(row=1, column=1)
        self._stepYEntry.grid(row=2, column=1)
        self._stepZEntry.grid(row=3, column=1)
        self._stepCEntry.grid(row=4, column=1)
        self._contEna.grid(row=1, column=3, rowspan=4)

        self._posX = tk.DoubleVar(self._framePos, 0.1)
        self._posY = tk.DoubleVar(self._framePos, 0.1)
        self._posZ = tk.DoubleVar(self._framePos, 0.1)
        self._posC = tk.DoubleVar(self._framePos, 0.1)
        self._pres = tk.DoubleVar(self._framePos, 0.1)
        self._posXEntry = tk.Entry(self._framePos, textvariable=self._posX, width=15, font='Arial 30', state='disable'
                                   , disabledbackground='white')
        self._posYEntry = tk.Entry(self._framePos, textvariable=self._posY, width=15, font='Arial 30', state='disable'
                                   , disabledbackground='white')
        self._posZEntry = tk.Entry(self._framePos, textvariable=self._posZ, width=15, font='Arial 30', state='disable'
                                   , disabledbackground='white')
        self._posCEntry = tk.Entry(self._framePos, textvariable=self._posC, width=15, font='Arial 30', state='disable'
                                   , disabledbackground='white')
        self._presEntry = tk.Entry(self._framePos, textvariable=self._pres, width=15, font='Arial 30', state='disable'
                                   , disabledbackground='white')
        self._labPosX = tk.Label(self._framePos, text="X", font='Arial 30 bold')
        self._labPosY = tk.Label(self._framePos, text="Y", font='Arial 30 bold')
        self._labPosZ = tk.Label(self._framePos, text="Z", font='Arial 30 bold')
        self._labPosC = tk.Label(self._framePos, text="T", font='Arial 30 bold')
        self._labPres = tk.Label(self._framePos, text="P", font='Arial 30 bold')
        self._labPosUnitX = tk.Label(self._framePos, text="mm", font='Arial 30')
        self._labPosUnitY = tk.Label(self._framePos, text="mm", font='Arial 30')
        self._labPosUnitZ = tk.Label(self._framePos, text="mm", font='Arial 30')
        self._labPosUnitC = tk.Label(self._framePos, text="°", font='Arial 30')
        self._labPresUnit = tk.Label(self._framePos, text="pa", font='Arial 30')

        self._labPosUnitX.grid(row=0, column=0)
        self._labPosUnitY.grid(row=1, column=0)
        self._labPosUnitZ.grid(row=2, column=0)
        self._labPosUnitC.grid(row=3, column=0)
        self._labPresUnit.grid(row=4, column=0)
        self._posXEntry.grid(row=0, column=1)
        self._posYEntry.grid(row=1, column=1)
        self._posZEntry.grid(row=2, column=1)
        self._posCEntry.grid(row=3, column=1)
        self._presEntry.grid(row=4, column=1)
        self._labPosX.grid(row=0, column=2)
        self._labPosY.grid(row=1, column=2)
        self._labPosZ.grid(row=2, column=2)
        self._labPosC.grid(row=3, column=2)
        self._labPres.grid(row=4, column=2)

        self._textConsole = tk.Text(self._frameConsole, width=30, height=20, wrap=tk.NONE, state="disabled")
        self._commandVar = tk.StringVar(self._frameConsole)
        self._commandEntry = tk.Entry(self._frameConsole, textvariable=self._commandVar, width=40)
        self._clearB = tk.Button(self._frameConsole, text='Clear', command=self.__clearConsole, height=2, width=10)
        self._sendB = tk.Button(self._frameConsole, text='Send', command=self.__sendtmp, height=2, width=10)
        self._consoleScrollY = tk.Scrollbar(self._frameConsole, command=self._textConsole.yview)
        self._consoleScrollX = tk.Scrollbar(self._frameConsole, command=self._textConsole.xview, orient=tk.HORIZONTAL)
        self._textConsole.config(yscrollcommand=self._consoleScrollY.set)
        self._textConsole.config(xscrollcommand=self._consoleScrollX.set)

        self._commandEntry.grid(row=0, column=0, columnspan=2)
        self._textConsole.grid(row=1, column=0, columnspan=2)
        self._clearB.grid(row=3, column=0)
        self._sendB.grid(row=3, column=1)
        self._consoleScrollY.grid(row=1, column=2, sticky=tk.S + tk.N)
        self._consoleScrollX.grid(row=2, column=0, columnspan=2, sticky=tk.W + tk.E)

        self._framePos.grid(row=0, column=0, rowspan=2, sticky='n')
        self.serialFrame.grid(row=2, column=0, sticky='ewns')
        self._frameArrow.grid(row=0, column=1, sticky='n')
        self._frameConfArrow.grid(row=2, column=1, sticky='s')
        self._frameAuxCtrl.grid(row=1, column=1, sticky='nesw')
        self._frameConsole.grid(row=0, column=2, rowspan=3, sticky='ns')

    def __sendtmp(self):
        # self.insertToConsole(self._commandVar.get())
        self.controller._driver.externalGcodeLine(self._commandVar.get())

    def insertToConsole(self, str):
        """
        Insert line in console
        :param str is the line to insert:
        :return:
        """
        self._textConsole.configure(state='normal')
        self._textConsole.insert(tk.END, str + '\n')
        self._textConsole.yview(tk.END)
        self._textConsole.configure(state='disabled')

    def __clearConsole(self):
        """
        Clear console Text.
        :return:
        """
        self._textConsole.configure(state='normal')
        self._textConsole.delete(1.0, tk.END)
        self._textConsole.configure(state='disabled')

    def _setPosX(self, value):
        self._posX.set(round(value, 4))

    def _setPosY(self, value):
        self._posY.set(round(value, 4))

    def _setPosZ(self, value):
        self._posZ.set(round(value, 4))

    def _setPosC(self, value):
        self._posC.set(round(value, 4))

    def _setPres(self, value):
        self._pres.set(round(value, 4))

    def _getStepX(self):
        return self._stepX.get()

    def _getStepY(self):
        return self._stepY.get()

    def _getStepZ(self):
        return self._stepZ.get()

    def _getStepC(self):
        return self._stepC.get()

    def _getEvState(self):
        return self._evVar.get()

    def _getPumpState(self):
        return self._pumpVar.get()

    def __evtXp(self, evt):
        self.controller.xInc()

    def __evtXm(self, evt):
        self.controller.xDec()

    def __evtYp(self, evt):
        self.controller.yInc()

    def __evtYm(self, evt):
        self.controller.yDec()

    def __evtZp(self, evt):
        self.controller.zInc()

    def __evtZm(self, evt):
        self.controller.zDec()

    def __evtCp(self, evt):
        self.controller.cInc()

    def __evtCm(self, evt):
        self.controller.cDec()

    def getContinueState(self):
        #return self._contEnaVar.get()
        return False

    posX = property(fset=_setPosX)
    posY = property(fset=_setPosY)
    posZ = property(fset=_setPosZ)
    posC = property(fset=_setPosC)
    pres = property(fset=_setPres)

    stepX = property(fget=_getStepX)
    stepY = property(fget=_getStepY)
    stepZ = property(fget=_getStepZ)
    stepC = property(fget=_getStepC)

    evState = property(fget=_getEvState)
    pumpState = property(fget=_getPumpState)


class ImportFrame(tk.Frame):
    def __init__(self, masterIHM, file, controller, fenetre, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)

        self._pathFile = file

        self._controller = controller
        self._masterIHM = masterIHM

        self._labSep = tk.Label(self, text="Separator")
        self._sepVar = tk.StringVar(self, ",")
        self._sepEntry = tk.Entry(self, textvariable=self._sepVar, width=15)

        self._labSl = tk.Label(self, text="Start line")
        self._slVar = tk.IntVar(self, 1)
        self._slEntry = tk.Entry(self, textvariable=self._slVar, width=15)

        self._labPosRef = tk.Label(self, text="Reference (C1)")
        self._posRefVar = tk.IntVar(self, 0)
        self._posRefEntry = tk.Entry(self, textvariable=self._posRefVar, width=15)

        self._labPosVal = tk.Label(self, text="Value (100nF)")
        self._posValVar = tk.IntVar(self, 1)
        self._posValEntry = tk.Entry(self, textvariable=self._posValVar, width=15)

        self._labPosPack = tk.Label(self, text="Package")
        self._posPackVar = tk.IntVar(self, 2)
        self._posPackEntry = tk.Entry(self, textvariable=self._posPackVar, width=15)

        self._labPosX = tk.Label(self, text="X")
        self._posXVar = tk.IntVar(self, 3)
        self._posXEntry = tk.Entry(self, textvariable=self._posXVar, width=15)

        self._labPosY = tk.Label(self, text="Y")
        self._posYVar = tk.IntVar(self, 4)
        self._posYEntry = tk.Entry(self, textvariable=self._posYVar, width=15)

        self._labName = tk.Label(self, text="Name")
        self._nameVar = tk.StringVar(self, "N")
        self._posName = tk.Entry(self, textvariable=self._nameVar, width=20)

        self._labPosT = tk.Label(self, text="T")
        self._posTVar = tk.IntVar(self, 5)
        self._posTEntry = tk.Entry(self, textvariable=self._posTVar, width=15)

        self._import = tk.Button(self, text='Import', command=self.__importCmd, width=15)

        self._labName.grid(row=0, column=0, columnspan=2, sticky='e')
        self._posName.grid(row=0, column=2, columnspan=2, sticky='w')

        self._labPosRef.grid(row=2, column=0)
        self._labPosVal.grid(row=3, column=0)
        self._labPosPack.grid(row=4, column=0)
        self._labSep.grid(row=5, column=0)

        self._posRefEntry.grid(row=2, column=1)
        self._posValEntry.grid(row=3, column=1)
        self._posPackEntry.grid(row=4, column=1)
        self._sepEntry.grid(row=5, column=1)

        self._labPosX.grid(row=2, column=2)
        self._labPosY.grid(row=3, column=2)
        self._labPosT.grid(row=4, column=2)
        self._labSl.grid(row=5, column=2)

        self._posXEntry.grid(row=2, column=3)
        self._posYEntry.grid(row=3, column=3)
        self._posTEntry.grid(row=4, column=3)
        self._slEntry.grid(row=5, column=3)

        self._import.grid(row=6, column=0, columnspan=4)

    def __importCmd(self):
        dicConf = {'X': self._posXVar.get(), 'Y': self._posYVar.get(), 'T': self._posTVar.get(),
                   'REF': self._posRefVar.get(), 'VAL': self._posValVar.get(), 'MOD': self._posPackVar.get()}
        self._controller.createFromCsv(self._nameVar.get(), self._pathFile, self._sepVar.get(), self._slVar.get(),
                                       dicConf)
        self._masterIHM.initBoardMenu()


class componentFrame(tk.Frame):
    """Frame used for display component information."""

    def __init__(self,fenetre, controller, cmp, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)

        self.controller = controller
        self.cmp = cmp

        self.tree = ttk.Treeview(self)
        self._isPlaceVar = tk.IntVar(self, 0)
        self._isEnableVar = tk.IntVar(self, 0)

        self._isPlaced = tk.Checkbutton(self, text='P', variable=self._isPlaceVar, command=self.__cmpChange)
        self._isEnable = tk.Checkbutton(self, text='E', variable=self._isEnableVar, command=self.__cmpChange)
        self._goTo = tk.Button(self, text='GoTo', command=self.__goToCmd)
        self._place = tk.Button(self, text='Place', command=self.__placeCmp)

        # self._listFeeder = self.controller.getFeederList()
        self._val = completeEntry(self, self.__cmpChange, varType='str')
        self._val.configure(width=11)
        self._ref = completeEntry(self, self.__cmpChange, varType='str')
        self._ref.configure(width=11)
        self._package = completeEntry(self, self.__cmpChange, varType='str')
        self._package.configure(width=11)
        self._model = completeEntry(self, self.__cmpChange, varType='str')
        self._model.configure(width=11)
        self._x = completeEntry(self, self.__cmpChange, varType='double')
        self._x.configure(width=11)
        self._y = completeEntry(self, self.__cmpChange, varType='double')
        self._y.configure(width=11)
        self._t = completeEntry(self, self.__cmpChange, varType='double')
        self._t.configure(width=11)
        self._feeder = completeEntry(self, self.__cmpChange, varType='str')
        self._feeder.configure(width=11)

        self._val.grid(row=0, column=0)
        self._ref.grid(row=0, column=1)
        self._package.grid(row=0, column=2)
        self._model.grid(row=0, column=3)
        self._feeder.grid(row=0, column=4)
        self._x.grid(row=0, column=5)
        self._y.grid(row=0, column=6)
        self._t.grid(row=0, column=7)
        self._isPlaced.grid(row=0, column=8)
        self._isEnable.grid(row=0, column=9)
        self._goTo.grid(row=0, column=10)
        self._place.grid(row=0, column=11)

        self.update()

    def __cmpChange(self, *args):
        """
        Called when IHM change parameters
        :return:
        """
        self.cmp.posX = self._x.var
        self.cmp.posY = self._y.var
        self.cmp.rot = self._t.var
        self.cmp.ref = self._ref.var
        self.cmp.value = self._val.var
        self.cmp.package = self._package.var
        self.cmp.model = self._model.var
        self.cmp.feeder = self._feeder.var
        self.cmp.isPlaced = self._isPlaceVar.get()
        self.cmp.isEnable = self._isEnableVar.get()

    def __placeCmp(self):
        self.controller.pickAndPlaceCmp(self._ref.var)

    def __goToCmd(self):
        self.controller.goToCmp(self._ref.var)

    def update(self):
        """
        Update IHM with data in cmp.
        :param cmp, is component class:
        :return:
        """
        self._x.var = self.cmp.posX
        self._y.var = self.cmp.posY
        self._t.var = self.cmp.rot
        self._ref.var = self.cmp.ref
        self._val.var = self.cmp.value
        self._package.var = self.cmp.package
        self._model.var = self.cmp.model
        self._feeder.var = self.cmp.feeder
        self._isPlaceVar.set(self.cmp.isPlaced)
        self._isEnableVar.set(self.cmp.isEnable)


class JobFrame(tk.Frame):
    def __init__(self, fenetre, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)
        imgSize = (25, 25)

        self.__playImg = ImageTk.PhotoImage(Image.open('./resources/play.png').resize(imgSize))
        self.__playBtn = tk.Button(self, image=self.__playImg)

        self.__pauseImg = ImageTk.PhotoImage(Image.open('./resources/pause.png').resize(imgSize))
        self.__pauseBtn = tk.Button(self, image=self.__pauseImg)

        self.__stopImg = ImageTk.PhotoImage(Image.open('./resources/stop.png').resize(imgSize))
        self.__stopBtn = tk.Button(self, image=self.__stopImg)

        self.__buildImg = ImageTk.PhotoImage(Image.open('./resources/build.png').resize(imgSize))
        self.__buildBtn = tk.Button(self, image=self.__buildImg)

        self.__jobDesc = tk.Label(self, text='')

        self.__playBtn.grid(row=0, column=0)
        self.__pauseBtn.grid(row=0, column=1, padx=10)
        self.__stopBtn.grid(row=0, column=2)
        self.__buildBtn.grid(row=0, column=3, padx=10)
        self.__jobDesc.grid(row=1, column=0, columnspan=4)

        self.playButtonState(0)
        self.pauseButtonState(0)
        self.buildButtonState(0)
        self.stopButtonState(0)

    def setPlayCallBack(self, cb):
        self.__playBtn['command'] = cb

    def setPauseCallBack(self, cb):
        self.__pauseBtn['command'] = cb

    def setStopCallBack(self, cb):
        self.__stopBtn['command'] = cb

    def setBuildCallBack(self, cb):
        self.__buildBtn['command'] = cb

    def playButtonState(self, state):
        self.__playBtn['state'] = 'normal' if state else 'disable'

    def pauseButtonState(self, state):
        self.__pauseBtn['state'] = 'normal' if state else 'disable'

    def buildButtonState(self, state):
        self.__buildBtn['state'] = 'normal' if state else 'disable'

    def stopButtonState(self, state):
        self.__stopBtn['state'] = 'normal' if state else 'disable'

    def jobDescription(self, desc):
        self.__jobDesc['text'] = desc

class globalCmpFrame(tk.LabelFrame):
    def __init__(self, fenetre, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)
        self.cmpList = []
        self.cmpDisplayList = []
        self.controller = controller

        self._filterFrame = tk.Frame(self)
        self._cmpFrameScrol = ScrollableFrame(self)
        self._cmpFrameScrol.setSize(width=750, height=500)

        self._filterFrame.grid(row=0, column=0)
        self._cmpFrameScrol.grid(row=1, column=0)

        self._valueFilter = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._refFilter = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._packageFilter = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._modelFilter = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._placedFilter = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._enableFilter = completeEntry(self._filterFrame, trashFunc, varType='str')

        self._modelEdit = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._feederEdit = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._placedEdit = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._enableEdit = completeEntry(self._filterFrame, trashFunc, varType='str')
        self._modelEdit.var = ''
        self._feederEdit.var = ''
        self._placedEdit.var = ''
        self._enableEdit.var = ''

        btnFilterApply = tk.Button(self._filterFrame,text='Filter', command=self.filterApply)
        btnEditApply = tk.Button(self._filterFrame, text='Edit', command=self.__editApply)

        tk.Label(self._filterFrame, text='Value:').grid(row=0, column=0)
        tk.Label(self._filterFrame, text='Ref:').grid(row=0, column=1)
        tk.Label(self._filterFrame, text='Package:').grid(row=0, column=2)
        tk.Label(self._filterFrame, text='Model:').grid(row=0, column=3)
        tk.Label(self._filterFrame, text='Feeder:').grid(row=0, column=4)
        tk.Label(self._filterFrame, text='x:').grid(row=0, column=5)
        tk.Label(self._filterFrame, text='Y:').grid(row=0, column=6)
        tk.Label(self._filterFrame, text='Z:').grid(row=0, column=7)
        tk.Label(self._filterFrame, text='Placed:').grid(row=0, column=8)
        tk.Label(self._filterFrame, text='Enable:').grid(row=0, column=9)

        #labelFrameScrol = tk.Frame(self._cmpFrameScrol.userFrame)

        self._valueFilter.grid(row=1, column=0)
        self._refFilter.grid(row=1, column=1)
        self._packageFilter.grid(row=1, column=2)
        self._modelFilter.grid(row=1, column=3)
        self._placedFilter.grid(row=1, column=8)
        self._enableFilter.grid(row=1, column=9)
        btnFilterApply.grid(row=1, column=10)

        self._modelEdit.grid(row=2, column=3)
        self._placedEdit.grid(row=2, column=8)
        self._enableEdit.grid(row=2, column=9)
        self._feederEdit.grid(row=2, column=4)
        btnEditApply.grid(row=2, column=10)


    def __filterChange(self):
        """
        Called when filter enter text change.
        Update onl board database object.
        :return:
        """

    def __displayFilterList(self):
        #for frame in self.cmpDisplayFrameList:
            #frame.destroy()

        self.controller.board.filter['value'] = self._valueFilter.var
        self.controller.board.filter['ref'] = self._refFilter.var
        self.controller.board.filter['package'] = self._packageFilter.var
        self.controller.board.filter['model'] = self._modelFilter.var
        self.controller.board.filter['placed'] = self._placedFilter.var
        self.controller.board.filter['enable'] = self._enableFilter.var

        list = self._cmpFrameScrol.userFrame.grid_slaves()
        for l in list:
            if type(l) is componentFrame:
                l.destroy()

        idRow = 1
        for cmp in self.cmpDisplayList:
            componentFrame(self._cmpFrameScrol.userFrame, self.controller, cmp).grid(row=idRow, column=0)
            idRow += 1

    def filterApply(self):
        self.cmpDisplayList = []
        valueFilterList = self._valueFilter.var.split('|')
        valueEnable = True if len(self._valueFilter.var.replace('|', '')) else False
        refFilterList = self._refFilter.var.split('|')
        refEnable = True if len(self._refFilter.var.replace('|', '')) else False
        packageFilterList = self._packageFilter.var.split('|')
        packageEnable = True if len(self._packageFilter.var.replace('|', '')) else False
        modelFilterList = self._modelFilter.var.split('|')
        modelEnable = True if len(self._modelFilter.var.replace('|', '')) else False
        placedFilterList = self._placedFilter.var.split('|')
        placedEnable = True if len(self._placedFilter.var.replace('|', '')) else False
        enableFilterList = self._enableFilter.var.split('|')
        enableEnable = True if len(self._enableFilter.var.replace('|', '')) else False

        for cmp in self.cmpList:
            valueAuthorized = not valueEnable
            refAuthorized = not refEnable
            packageAuthorized = not packageEnable
            modelAuthorized = not modelEnable
            placedAuthorized = not placedEnable
            enableAuthorized = not enableEnable

            if valueEnable:
                for value in valueFilterList:
                    if cmp.value == value:
                        valueAuthorized = True
            if refEnable:
                for ref in refFilterList:
                    if cmp.ref == ref:
                        refAuthorized = True
            if packageEnable:
                for package in packageFilterList:
                    if cmp.package == package:
                        packageAuthorized = True
            if modelEnable:
                for model in modelFilterList:
                    if cmp.model == model:
                        modelAuthorized = True
            if placedEnable:
                for isPlaced in placedFilterList:
                    if isPlaced == '1' and cmp.isPlaced:
                        placedAuthorized = True
                    elif isPlaced == '0' and not cmp.isPlaced:
                        placedAuthorized = True

            if enableEnable:
                for isEnable in enableFilterList:
                    if isEnable == '1' and cmp.isEnable:
                        enableAuthorized = True
                    elif isEnable == '0' and not cmp.isEnable:
                        enableAuthorized = True

            if valueAuthorized and refAuthorized and packageAuthorized and modelAuthorized and placedAuthorized and enableAuthorized:
                self.cmpDisplayList.append(cmp)

        self.__displayFilterList()

    def __editApply(self):
        slaveList = self._cmpFrameScrol.userFrame.grid_slaves()

        for slave in slaveList:
            if type(slave) is componentFrame:
                if len(self._modelEdit.var.replace(' ', '')):
                    slave.cmp.model = self._modelEdit.var
                if len(self._feederEdit.var.replace(' ', '')):
                    slave.cmp.feeder = int(self._feederEdit.var)
                if self._placedEdit.var == '1':
                    slave.cmp.isPlaced = 1
                elif self._placedEdit.var == '0':
                    slave.cmp.isPlaced = 0
                if self._enableEdit.var == '1':
                    slave.cmp.isEnable = 1
                elif self._enableEdit.var == '0':
                    slave.cmp.isEnable = 0
                slave.update()

        self._modelEdit.var = ''
        self._feederEdit.var = ''
        self._placedEdit.var = ''
        self._enableEdit.var = ''

    def setCmpList(self, cmpList):
        self.cmpList = cmpList

    def setFilter(self,value, ref, pack, model, place, enable):
        self._valueFilter.var = value
        self._refFilter.var = ref
        self._packageFilter.var = pack
        self._modelFilter.var = model
        self._placedFilter.var = place
        self._enableFilter.var = enable

    def componentHaveChanged(self, ref):
        slaveList = self._cmpFrameScrol.userFrame.grid_slaves()
        for slave in slaveList:
            if type(slave) is componentFrame:
                if slave.cmp.ref == ref:
                    slave.update()

class BoardFrame(tk.Frame):
    """
    Main frame of board window.
    Board display.
    List of component.
    Job frame.
    """

    def __init__(self, fenetre, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)

        self.controller = controller

        self._rootCmpFrame = globalCmpFrame(self, controller)
        self.jobFrame = JobFrame(self)

        self._boardFrame = tk.LabelFrame(self, text="Board", labelanchor='n', padx=10, pady=0)
        self._paramBoardFrame = tk.LabelFrame(self._boardFrame, text="Parameters", labelanchor='n', padx=10, pady=0)
        self._referenceFrame = tk.LabelFrame(self._boardFrame, text="References", labelanchor='n', padx=10, pady=0)
        # self._viewFrame = tk.LabelFrame(self, text="View", labelanchor='n', padx=10, pady=10)
        # self._testFrame = tk.LabelFrame(self, text="Parameters", labelanchor='n', padx=10, pady=10)
        # self._paramFrame = tk.LabelFrame(self, text="Component", labelanchor='n',width=768, height=200, padx=10, pady=10)

        self._boardDraw = BoarDrawing(self._boardFrame)

        self._sizeX = completeEntry(self._paramBoardFrame, self.__paramBoardChange, varType='double')
        self._sizeY = completeEntry(self._paramBoardFrame, self.__paramBoardChange, varType='double')
        self._sizeZ = completeEntry(self._paramBoardFrame, self.__paramBoardChange, varType='double')

        self._rootCmpFrame.grid(row=1, column=1)
        self.jobFrame.grid(row=0, column=1)
        self._boardFrame.grid(row=0, column=0, rowspan=2)

        self._paramBoardFrame.grid(row=0, column=0)
        self._boardDraw.grid(row=1, column=0)
        self._referenceFrame.grid(row=2, column=0)

        tk.Label(self._paramBoardFrame, text="Size").grid(row=1, column=0)
        tk.Label(self._paramBoardFrame, text="Offset").grid(row=2, column=0)
        tk.Label(self._paramBoardFrame, text="X").grid(row=0, column=1)
        tk.Label(self._paramBoardFrame, text="Y").grid(row=0, column=2)
        tk.Label(self._paramBoardFrame, text="Z").grid(row=0, column=3)
        tk.Label(self._paramBoardFrame, text="T").grid(row=0, column=4)
        self._sizeX.grid(row=1, column=1)
        self._sizeY.grid(row=1, column=2)
        self._sizeZ.grid(row=1, column=3)

        self._ref1 = completeEntry(self._referenceFrame, self.__paramBoardChange, varType='str')
        self._ref2 = completeEntry(self._referenceFrame, self.__paramBoardChange, varType='str')
        self._ref1X = completeEntry(self._referenceFrame, self.__paramBoardChange, varType='double')
        self._ref1Y = completeEntry(self._referenceFrame, self.__paramBoardChange, varType='double')
        self._ref2X = completeEntry(self._referenceFrame, self.__paramBoardChange, varType='double')
        self._ref2Y = completeEntry(self._referenceFrame, self.__paramBoardChange, varType='double')
        self._ref1updt = tk.Button(self._referenceFrame, command=self.__getPosRef1, text='Get Pos')
        self._ref2updt = tk.Button(self._referenceFrame, command=self.__getPosRef2, text='Get Pos')

        tk.Label(self._referenceFrame, text="N°1").grid(row=1, column=0)
        tk.Label(self._referenceFrame, text="N°2").grid(row=2, column=0)
        tk.Label(self._referenceFrame, text="Ref").grid(row=0, column=1)
        tk.Label(self._referenceFrame, text="X").grid(row=0, column=2)
        tk.Label(self._referenceFrame, text="Y").grid(row=0, column=3)
        self._ref1.grid(row=1, column=1)
        self._ref1X.grid(row=1, column=2)
        self._ref1Y.grid(row=1, column=3)
        self._ref2.grid(row=2, column=1)
        self._ref2X.grid(row=2, column=2)
        self._ref2Y.grid(row=2, column=3)
        self._ref1updt.grid(row=1, column=4)
        self._ref2updt.grid(row=2, column=4)

    def setboardParam(self, board):
        self._sizeX.var = board.xSize
        self._sizeY.var = board.ySize
        self._sizeZ.var = board.zSize
        self._ref1.var = board.ref1
        self._ref2.var = board.ref2
        self._ref1X.var = board.ref1RealPos['X']
        self._ref1Y.var = board.ref1RealPos['Y']
        self._ref2X.var = board.ref2RealPos['X']
        self._ref2Y.var = board.ref2RealPos['Y']

        """ 
        bizare???
        self.controller.board.ref1X = self._ref1X.var
        self.controller.board.ref1Y = self._ref1Y.var
        self.controller.board.ref2X = self._ref2X.var
        self.controller.board.ref2Y = self._ref2Y.var
        """


    def __paramBoardChange(self, *args):
        """
        Called when a paramter of board is changing;
        :param args:
        :return:
        """
        self.controller.board.xSize = self._sizeX.var
        self.controller.board.ySize = self._sizeY.var
        self.controller.board.zSize = self._sizeZ.var
        self.controller.board.ref1 = self._ref1.var
        self.controller.board.ref2 = self._ref2.var
        self.controller.board.ref1RealPos['X'] = self._ref1X.var
        self.controller.board.ref1RealPos['Y'] = self._ref1Y.var
        self.controller.board.ref2RealPos['X'] = self._ref2X.var
        self.controller.board.ref2RealPos['Y'] = self._ref2Y.var

        self._boardDraw.drawBoard(self.controller.board, self.controller.modList)

    def bomCreate(self, board):
        self._rootCmpFrame.setFilter(value=board.filter['value'], ref=board.filter['ref'], pack=board.filter['package'],
                           model=board.filter['model'], place=board.filter['placed'], enable=board.filter['enable'])

        self._rootCmpFrame.setCmpList(board.cmpDic.values())
        self._rootCmpFrame.filterApply()
        self._boardDraw.drawBoard(board, self.controller.modList)

    def cmpHaveChanged(self, ref):
        """
        Program mus call this when the state of a cmp have changed
        :param ref:
        :return:
        """
        self._rootCmpFrame.componentHaveChanged(ref)


    def __getPosRef1(self):
        try:
            pos = self.controller.driver.readHardwarePos()
        except:
            self.controller.logger.printCout("Devise does not responding")
        else:
            self._ref1X.var = pos['X']
            self._ref1Y.var = pos['Y']
            self.__paramBoardChange()

    def __getPosRef2(self):
        try:
            pos = self.controller.driver.readHardwarePos()
        except:
            self.controller.logger.printCout("Devise does not responding")
        else:
            self._ref2X.var = pos['X']
            self._ref2Y.var = pos['Y']
            self.__paramBoardChange()


class DtbFrame(tk.Frame):
    """Frame used for debug."""

    def __init__(self, fenetre, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)

        self.controller = controller

        frameTop = tk.LabelFrame(self, text="Model", labelanchor='n', padx=10, pady=10)
        frameAlias = tk.LabelFrame(self, text="Alias", labelanchor='n', padx=10, pady=10)
        frameInfo = tk.LabelFrame(self, text="Data", labelanchor='n', padx=10, pady=10)
        frameCtrl = tk.Frame(self, padx=10, pady=10)

        self._modelList = ['toto']
        self._strModel = tk.StringVar()
        self._strModel.set(self._modelList[0])
        self._modelOm = tk.OptionMenu(frameTop, self._strModel, *self._modelList)

        self._aliasList = ['toto']
        self._strAlias = tk.StringVar()
        self._strAlias.set(self._aliasList[0])
        self._aliasOm = tk.OptionMenu(frameAlias, self._strAlias, *self._aliasList)

        newModBtn = tk.Button(frameTop, text='New', width=15,
                              command=lambda: entryWindow(self, 'New model', ['Model Name'], ['Name'],
                                                          self.__userAddModelReturn, 0))
        dellModBtn = tk.Button(frameTop, text='Delete', width=15, command=self.__deleteModel)
        addBtn = tk.Button(frameAlias, text='Add',
                           command=lambda: entryWindow(self, 'New Alias', ['Alias Name'], ['Name'],
                                                       self.__userAddAliasReturn, 0))
        dellBtn = tk.Button(frameAlias, text='Del', command=self.__deleteAlias)
        saveBtn = tk.Button(frameCtrl, text='Save', command=self.controller.saveInFile)

        self._sX = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._sY = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._sZ = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._scanHentry = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')

        self._pickupSpeed = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._placeSpeed = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._pickupDelay = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._placeDelay = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._moveSpeed = completeEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')

        self._sX.var = 0.0
        self._sY.var = 0.0
        self._sZ.var = 0.0
        self._scanHentry.var = 0.0

        self._modelOm.grid(row=0, column=0)
        newModBtn.grid(row=0, column=2)
        dellModBtn.grid(row=0, column=3)

        tk.Label(frameInfo, text="size X").grid(row=0, column=0)
        tk.Label(frameInfo, text="size Y").grid(row=1, column=0)
        tk.Label(frameInfo, text="size Z").grid(row=2, column=0)
        tk.Label(frameInfo, text="Scan height").grid(row=3, column=0)
        tk.Label(frameInfo, text="Pickup speed(mm/min)").grid(row=0, column=2)
        tk.Label(frameInfo, text="Pickup delay(ms)").grid(row=1, column=2)
        tk.Label(frameInfo, text="Place speed(mm/min)").grid(row=2, column=2)
        tk.Label(frameInfo, text="Place delay(ms)").grid(row=3, column=2)
        tk.Label(frameInfo, text="Move speed(ms)").grid(row=4, column=2)

        self._sX.grid(row=0, column=1)
        self._sY.grid(row=1, column=1)
        self._sZ.grid(row=2, column=1)
        self._scanHentry.grid(row=3, column=1)
        self._pickupSpeed.grid(row=0, column=3)
        self._pickupDelay.grid(row=1, column=3)
        self._placeSpeed.grid(row=2, column=3)
        self._placeDelay.grid(row=3, column=3)
        self._moveSpeed.grid(row=4, column=3)

        addBtn.grid(row=0, column=0, sticky='we')
        dellBtn.grid(row=0, column=1, sticky='we')
        self._aliasOm.grid(row=1, column=0, columnspan=2, sticky='we')

        saveBtn.grid(row=0, column=1)

        frameTop.grid(row=0, column=0, columnspan=2, sticky='we')
        frameInfo.grid(row=1, column=0)
        frameAlias.grid(row=1, column=1)
        frameCtrl.grid(row=2, column=0)

        self._strModel.trace('w', self.__chageModelTrace)

        self.__deleteModelList()
        self.deleteAliaslList()
        self.__updateFromController()

        # self.addModel('test')

    def __deleteAlias(self):
        if self._strModel.get() in self.controller.modList:
            self.controller.modList[self._strModel.get()].aliasRemove(self._strAlias.get())
            if len(self.controller.modList[self._strModel.get()].aliasList):
                self._strAlias.set(self.controller.modList[self._strModel.get()].aliasList[-1])
            else:
                self._strAlias.set('')
            self.__displayModel(self.controller.modList[self._strModel.get()])

    def __deleteModel(self):
        if self._strModel.get() in self.controller.modList:
            self.controller.modList.deleteModule(self._strModel.get())
            self.__updateFromController()
            if len(self.controller.modList):
                modSel = self.controller.modList.__iter__().__next__()
                self._strModel.set(modSel)
            else:
                self._strModel.set('')

    def __entryEnable(self):
        self._sX['state'] = 'normal'
        self._sY['state'] = 'normal'
        self._sZ['state'] = 'normal'
        self._scanHentry['state'] = 'normal'
        self._pickupSpeed['state'] = 'normal'
        self._placeSpeed['state'] = 'normal'
        self._pickupDelay['state'] = 'normal'
        self._placeDelay['state'] = 'normal'
        self._moveSpeed['state'] = 'normal'

    def __entryDisable(self):
        self._sX['state'] = 'disable'
        self._sY['state'] = 'disable'
        self._sZ['state'] = 'disable'
        self._scanHentry['state'] = 'disable'
        self._pickupSpeed['state'] = 'disable'
        self._placeSpeed['state'] = 'disable'
        self._pickupDelay['state'] = 'disable'
        self._placeDelay['state'] = 'disable'
        self._moveSpeed['state'] = 'disable'

    def __dataChange(self, *args):
        """
        Called by trace of all value.
        Update ram database at each change
        :param args:
        :return:
        """
        self.controller.modList[self._strModel.get()].width = self._sX.var
        self.controller.modList[self._strModel.get()].length = self._sY.var
        self.controller.modList[self._strModel.get()].height = self._sZ.var
        self.controller.modList[self._strModel.get()].scanHeight = self._scanHentry.var
        self.controller.modList[self._strModel.get()].aliasList = list(self._aliasList)
        self.controller.modList[self._strModel.get()].pickupSpeed = self._pickupSpeed.var
        self.controller.modList[self._strModel.get()].placeSpeed = self._placeSpeed.var
        self.controller.modList[self._strModel.get()].pickupDelay = self._pickupDelay.var
        self.controller.modList[self._strModel.get()].placeDelay = self._placeDelay.var
        self.controller.modList[self._strModel.get()].moveSpeed = self._moveSpeed.var

    def __userAddModelReturn(self, dataIn):
        """
        Called by the return of little window
        :param dataIn:
        :return:
        """
        strIn = dataIn['Name'].replace(' ', '_')

        self.controller.makeNewModel(strIn)
        self.__updateFromController()
        self._strModel.set(strIn)

    def __userAddAliasReturn(self, dataIn):
        """
        Called by the return of little window
        :param dataIn:
        :return:
        """
        if self._strModel.get() in self.controller.modList:
            self.controller.modList[self._strModel.get()].aliasList.append(dataIn['Name'].replace(' ', '_'))
            self.__displayModel(self.controller.modList[self._strModel.get()])
            # self._strAlias.set()

    def __chageModelTrace(self, *arg):
        """
        Update data associated to model when strModel change.
        If model don't exist enstry is disable.
        :param arg:
        :return:
        """
        if self._strModel.get() in self.controller.modList:
            self.__displayModel(self.controller.modList[self._strModel.get()])
            self.__entryEnable()
        else:
            self.__entryDisable()

    def __displayModel(self, model):
        self._sX.var = model.width
        self._sY.var = model.length
        self._sZ.var = model.height
        self._scanHentry.var = model.scanHeight
        self._pickupSpeed.var = model.pickupSpeed
        self._placeSpeed.var = model.placeSpeed
        self._pickupDelay.var = model.pickupDelay
        self._placeDelay.var = model.placeDelay
        self._moveSpeed.var = model.moveSpeed

        self.deleteAliaslList()
        for alias in model.aliasList:
            self.__addAlias(alias)
        if len(model.aliasList):
            self._strAlias.set(model.aliasList[-1])
        else:
            self._strAlias.set('')

    def __updateFromController(self):
        """
        Uptade model list from controller/database
        :return:
        """
        self.__deleteModelList()
        for mod in self.controller.modList.values():
            self.__addModel(mod.name)

        if self._strModel.get() not in self.controller.modList:
            try:
                modSel = self.controller.modList.__iter__().__next__()
            except:
                self._strModel.set('')
            else:
                self._strModel.set(modSel)

    def __addModel(self, strMod):
        """Add a new model for display in IHM"""
        self._modelList.append(strMod)
        menu = self._modelOm["menu"]
        menu.delete(0, "end")
        for string in self._modelList:
            menu.add_command(label=string,
                             command=lambda value=string: self._strModel.set(value))

    def __deleteModelList(self):
        self._modelList = []
        self._modelOm["menu"].delete(0, "end")
        self._strModel.set('')
        self.__entryDisable()

    def __addAlias(self, strAlias):
        """Add a new model"""
        self._aliasList.append(strAlias)
        menu = self._aliasOm["menu"]
        menu.delete(0, "end")
        for string in self._aliasList:
            menu.add_command(label=string,
                             command=lambda value=string: self._strAlias.set(value))

    def deleteAliaslList(self):
        self._aliasList = []
        self._aliasOm["menu"].delete(0, "end")
        self._strAlias.set('')


class DebugFrame(tk.Frame):
    """Frame used for place cmp."""

    def __init__(self, fenetre, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)

        vsb = tk.Scrollbar(self, orient=tk.VERTICAL)
        vsb.grid(row=0, column=1, sticky=tk.N + tk.S)
        # hsb = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        # hsb.grid(row=1, column=0, sticky=tk.E + tk.W)
        # c = tk.Canvas(self, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        c = tk.Canvas(self, yscrollcommand=vsb.set)
        c.grid(row=0, column=0, sticky="news")
        c.configure(width=200, height=200)
        vsb.config(command=c.yview)
        # hsb.config(command=c.xview)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._fr = tk.Frame(c)
        # On ajoute des widgets :
        c.create_window(0, 0, window=self._fr)
        self._fr.update_idletasks()
        c.config(scrollregion=c.bbox("all"))
        for i in range(0, 26):
            for t in range(0, 7):
                tk.Button(self._fr, width=10, height=2, text="{}{}".format(chr(i + 65), t)).grid(row=i, column=t)
        c.create_window(0, 0, window=self._fr)
        self._fr.update_idletasks()
        c.config(scrollregion=c.bbox("all"))


class PnpIHM:
    """High level class for IHM view
    """

    def __init__(self, controller, logger):
        self.ctrl = controller  # Hight level class of self.controller.
        self.ctrl.boardCtrl.enableSaveFunc = self.boardIsLoad

        self.mainWindow = tk.Tk()  # Instance of main window.
        self.mainWindow.title('MiniPnp - OXILEC')
        self.mainWindow.maxsize(width=1350, height=700)

        self.ctrlWindow = CtrlFrame(self.mainWindow, self.ctrl.directCtrl)
        logger.ihmDirect = self.ctrlWindow

        self.paramWindow = ParamFrame(self.mainWindow, self.ctrl.paramCtrl, self.ctrl.machineConfiguration)
        self.feederWindow = FeederFrame(self.mainWindow, self.ctrl.machineConfiguration, logger, self.ctrl.boardCtrl)

        self.brdWindow = BoardFrame(self.mainWindow, self.ctrl.boardCtrl)
        self.ctrl.boardCtrl.ihm = self.brdWindow

        self.dtbWindow = DtbFrame(self.mainWindow, self.ctrl.dtbCtrl)
        self.debugWindow = DebugFrame(self.mainWindow)

        self.topMenuBar = tk.Menu(self.mainWindow)
        self._menuFile = tk.Menu(self.topMenuBar, tearoff=0)
        self._menuTableTop = tk.Menu(self.topMenuBar, tearoff=0)

        self.topMenuBar.add_cascade(label="File ", menu=self._menuFile)
        self.topMenuBar.add_command(label="Board ", command=self.initBoardMenu, state='disabled')
        self.topMenuBar.add_command(label="DataBase", command=self.initDtbMenu)
        self.topMenuBar.add_command(label="Control", command=self.initCtrlMenu)
        self.topMenuBar.add_cascade(label="TableTop", menu=self._menuTableTop)
        self.topMenuBar.add_command(label="Debug", command=self.initDebugMenu)
        self.mainWindow.config(menu=self.topMenuBar)

        self._menuFile.add_command(label="New ", command=self.importFile)
        self._menuFile.add_command(label="Open ", command=self.importFromXml)
        self._menuFile.add_separator()
        self._menuFile.add_command(label="Save ", state='disabled', command=self.ctrl.boardCtrl.saveBoard)
        self._menuFile.add_command(label="Save As ", state='disabled', command=self.ctrl.boardCtrl.saveAsBoard)
        self._menuFile.add_command(label="Close ", state='disabled')

        self._menuTableTop.add_command(label="Parameters ", command=self.initParamMenu)
        self._menuTableTop.add_command(label="Feeder ", command=self.initFeederMenu)
        self._menuTableTop.add_command(label="View ", state='disabled')
        self._menuTableTop.add_separator()
        self._menuTableTop.add_command(label="Save ", command=self.ctrl.machineConfiguration.saveToXml)

        self._statusLabel = tk.Label(self.mainWindow, text='status', font='Arial 20 bold')
        self.actualFrame = self.paramWindow
        self.initCtrlMenu()

        self.ctrl.setTopIHM(self)
        self.ctrl.bindInit()
        self.ctrl.updateStatusOnIHM()
        self.paramWindow.update()

        self.mainWindow.mainloop()

    def initCtrlMenu(self):
        if self.actualFrame is not self.ctrlWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.ctrlWindow.pack()
            self._statusLabel.pack()
            self.actualFrame = self.ctrlWindow;
            self.ctrlWindow.serialFrame.listCom()
            self.ctrlWindow.focus_force()

    def initParamMenu(self):
        if self.actualFrame is not self.paramWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.paramWindow.pack()
            self.actualFrame = self.paramWindow;
            self.paramWindow.focus_force()
            self._statusLabel.pack()

    def initFeederMenu(self):
        if self.actualFrame is not self.feederWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.feederWindow.pack()
            self.actualFrame = self.feederWindow
            self.feederWindow.focus_force()
            self._statusLabel.pack()

    def initBoardMenu(self):
        if self.actualFrame is not self.brdWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.brdWindow.pack()
            self.actualFrame = self.brdWindow
            self._statusLabel.pack()

    def initDebugMenu(self):
        if self.actualFrame is not self.debugWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.debugWindow.pack()
            self.actualFrame = self.debugWindow
            self._statusLabel.pack()

    def initDtbMenu(self):
        if self.actualFrame is not self.dtbWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.dtbWindow.pack()
            self.actualFrame = self.dtbWindow;
            self._statusLabel.pack()

    def importFile(self):
        """
        Crate a new program with a pos file créated by CAO.
        :return:
        """
        f = tkinter.filedialog.askopenfilename(title="Open file", filetypes=[('CSV files', '.csv')])
        importFrame = ImportFrame(self, f, self.ctrl.boardCtrl, self.mainWindow)
        self.actualFrame.pack_forget()
        self._statusLabel.pack_forget()
        importFrame.pack()
        self.actualFrame = importFrame
        self._statusLabel.pack()

    def importFromXml(self):
        """
        Import an old program.
        :return:
        """
        f = tkinter.filedialog.askopenfilename(title="Open file", filetypes=[('pnpp files', '.pnpp')])
        self.ctrl.boardCtrl.importFromXml(f)
        self.initBoardMenu()

    def boardIsLoad(self, state):
        self._menuFile.entryconfigure("Save ", state=state)
        self._menuFile.entryconfigure("Save As ", state=state)
        self.topMenuBar.entryconfigure('Board ', state=state)

    def setStatusLabel(self, text):
        self._statusLabel['text'] = text

    def setBind(self, event, key, calBack):
        self.mainWindow.bind("<{}-{}>".format(event, key), calBack)
