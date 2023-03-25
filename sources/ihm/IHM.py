# coding: utf-8

import tkinter as tk
from tkinter import ttk

from deprecated import deprecated
from PIL import ImageTk, Image

import tkinter.filedialog

from .feeder import *
from .basePlate import *

import os


class BoarDrawing(tk.Frame):
    def __init__(self, fenetre, *args, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)
        self.motherFram = fenetre

        vsb = tk.Scrollbar(self, orient=tk.VERTICAL)
        vsb.grid(row=0, column=1, sticky=tk.N + tk.S)
        hsb = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hsb.grid(row=1, column=0, sticky=tk.E + tk.W)

        self._c = tk.Canvas(self, yscrollcommand=vsb.set, xscrollcommand=hsb.set, bg="white")
        self._c.configure(width=500, height=300)

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
        posX = (cmp.posX * self.scale) - cmpSizeX / 2.0
        posY = self._c.winfo_reqheight() - ((cmp.posY * self.scale) - cmpSizeY / 2.0)
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
        # angle = math.radians(cmp.rot + board.angleCorr)
        angle = math.radians(cmp.rot)
        # angle = math.radians(270.0)
        cos_val = math.cos(angle)
        sin_val = math.sin(angle)
        cx = (cmp.posX * self.scale)
        cy = self._c.winfo_reqheight() - (cmp.posY * self.scale)
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


class ParamFrame(tk.Frame):
    def __init__(self, fenetre, controller, machineConf, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)
        self.controller = controller
        self.controller.ihm = self
        #checkEntryCmdDouble = self.register(checkDoubleEntry)
        #checkEntryCmdInt = self.register(checkIntEntry)

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

        self._XstepBymmEntry = CompleteEntry(self._frameX, self.__paramChange, 'double')
        self._XmaxAccelEntry = CompleteEntry(self._frameX, self.__paramChange, 'double')
        self._XmaxSpeedEntry = CompleteEntry(self._frameX, self.__paramChange, 'double')

        self._XstepBymmEntry.configure(state='normal')
        tk.Label(self._frameX, text="Step/mm").grid(row=0, column=0)
        self._XstepBymmEntry.grid(row=1, column=0)
        tk.Label(self._frameX, text="Speed (mm/s)").grid(row=2, column=0)
        self._XmaxSpeedEntry.grid(row=3, column=0)
        tk.Label(self._frameX, text="Accel (mm/s²)").grid(row=4, column=0)
        self._XmaxAccelEntry.grid(row=5, column=0)

        self._YstepBymmEntry = CompleteEntry(self._frameY, self.__paramChange, 'double')
        self._YmaxAccelEntry = CompleteEntry(self._frameY, self.__paramChange, 'double')
        self._YmaxSpeedEntry = CompleteEntry(self._frameY, self.__paramChange, 'double')

        tk.Label(self._frameY, text="Step/mm").grid(row=0, column=0)
        self._YstepBymmEntry.grid(row=1, column=0)
        tk.Label(self._frameY, text="Speed (mm/s)").grid(row=2, column=0)
        self._YmaxSpeedEntry.grid(row=3, column=0)
        tk.Label(self._frameY, text="Accel (mm/s²)").grid(row=4, column=0)
        self._YmaxAccelEntry.grid(row=5, column=0)

        self._ZstepBymmEntry = CompleteEntry(self._frameZ, self.__paramChange, 'double')
        self._ZmaxAccelEntry = CompleteEntry(self._frameZ, self.__paramChange, 'double')
        self._ZmaxSpeedEntry = CompleteEntry(self._frameZ, self.__paramChange, 'double')

        tk.Label(self._frameZ, text="Step/mm").grid(row=0, column=0)
        self._ZstepBymmEntry.grid(row=1, column=0)
        tk.Label(self._frameZ, text="Speed (mm/s)").grid(row=2, column=0)
        self._ZmaxSpeedEntry.grid(row=3, column=0)
        tk.Label(self._frameZ, text="Accel (mm/s)²").grid(row=4, column=0)
        self._ZmaxAccelEntry.grid(row=5, column=0)

        self._CstepBymmEntry = CompleteEntry(self._frameC, self.__paramChange, 'double')
        self._CmaxAccelEntry = CompleteEntry(self._frameC, self.__paramChange, 'double')
        self._CmaxSpeedEntry = CompleteEntry(self._frameC, self.__paramChange, 'double')

        tk.Label(self._frameC, text="Step/deg").grid(row=0, column=0)
        self._CstepBymmEntry.grid(row=1, column=0)
        tk.Label(self._frameC, text="Speed (deg/s)").grid(row=2, column=0)
        self._CmaxSpeedEntry.grid(row=3, column=0)
        tk.Label(self._frameC, text="Accel (deg/s²)").grid(row=4, column=0)
        self._CmaxAccelEntry.grid(row=5, column=0)

        self._XposScanEntry = CompleteEntry(self._frameScan, self.__paramChange, 'double')
        self._YposScanEntry = CompleteEntry(self._frameScan, self.__paramChange, 'double')
        self._ZposScanEntry = CompleteEntry(self._frameScan, self.__paramChange, 'double')

        tk.Label(self._frameScan, text="X").grid(row=0, column=0)
        self._XposScanEntry.grid(row=1, column=0)
        tk.Label(self._frameScan, text="Y").grid(row=2, column=0)
        self._YposScanEntry.grid(row=3, column=0)
        tk.Label(self._frameScan, text="Z").grid(row=4, column=0)
        self._ZposScanEntry.grid(row=5, column=0)

        self._XposBoardEntry = CompleteEntry(self._frameBoard, self.__paramChange, 'double')
        self._YposBoardEntry = CompleteEntry(self._frameBoard, self.__paramChange, 'double')
        self._ZposBoardEntry = CompleteEntry(self._frameBoard, self.__paramChange, 'double')

        tk.Label(self._frameBoard, text="X").grid(row=0, column=0)
        self._XposBoardEntry.grid(row=1, column=0)
        tk.Label(self._frameBoard, text="Y").grid(row=2, column=0)
        self._YposBoardEntry.grid(row=3, column=0)
        tk.Label(self._frameBoard, text="Z").grid(row=4, column=0)
        self._ZposBoardEntry.grid(row=5, column=0)

        self._XposTrashEntry = CompleteEntry(self._frameTrash, self.__paramChange, 'double')
        self._YposTrashEntry = CompleteEntry(self._frameTrash, self.__paramChange, 'double')
        self._ZposTrashEntry = CompleteEntry(self._frameTrash, self.__paramChange, 'double')

        tk.Label(self._frameTrash, text="X").grid(row=0, column=0)
        self._XposTrashEntry.grid(row=1, column=0)
        tk.Label(self._frameTrash, text="Y").grid(row=2, column=0)
        self._YposTrashEntry.grid(row=3, column=0)
        tk.Label(self._frameTrash, text="Z").grid(row=4, column=0)
        self._ZposTrashEntry.grid(row=5, column=0)

        self._ZposHeadEntry = CompleteEntry(self._frameMisc, self.__paramChange, 'double')
        self._ZposHeadLab = tk.Label(self._frameMisc, text="Z Head")
        self._ZLiftEntry = CompleteEntry(self._frameMisc, self.__paramChange, 'double')
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
        self._frameRef.grid(row=1, column=0, columnspan=3, rowspan=2, sticky='ns')
        self._frameMisc.grid(row=1, column=3, sticky='ns')
        ttk.Button(self, text='Save', command=self.__paramSave).grid(row=2, column=3)

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


class MotorOnOffFrame(tk.LabelFrame):
    def __init__(self, fenetre, controller, **kwargs):
        tk.LabelFrame.__init__(self, fenetre, **kwargs)
        self.controller = controller

        self._motorOnBtn = ttk.Button(self, text='Motor On', command=self.__motorOn)
        self._motorOffBtn = ttk.Button(self, text='Motor Off', command=self.__motorOff)

        self._motorOnBtn.grid(row=3, column=1)
        self._motorOffBtn.grid(row=4, column=1)

    def __motorOn(self):
        self.controller.motorOn()

    def __motorOff(self):
        self.controller.motorOff()


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
        self.serialFrame = MotorOnOffFrame(self, self.controller, text='Misc', labelanchor='n', padx=5, pady=5)

        self._xp = ttk.Button(self._frameArrow, text='X+', width=4)
        self._xm = ttk.Button(self._frameArrow, text='X-', width=4)
        self._yp = ttk.Button(self._frameArrow, text='Y+', width=4)
        self._ym = ttk.Button(self._frameArrow, text='Y-', width=4)
        self._zp = ttk.Button(self._frameArrow, text='Z+', width=4)
        self._zm = ttk.Button(self._frameArrow, text='Z-', width=4)
        self._cp = ttk.Button(self._frameArrow, text='C+', width=4)
        self._cm = ttk.Button(self._frameArrow, text='C-', width=4)

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

        self._homeX = ttk.Button(self._frameHome, text='X', width=4, command=self.controller.homeX)
        self._homeY = ttk.Button(self._frameHome, text='Y', width=4, command=self.controller.homeY)
        self._homeZ = ttk.Button(self._frameHome, text='Z', width=4, command=self.controller.homeZ)
        self._homeC = ttk.Button(self._frameHome, text='C', width=4, command=self.controller.homeC)
        self._homeALL = ttk.Button(self._frameHome, text='ALL', width=4, command=self.controller.homeAll)

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

        self._stepXEntry = CompleteEntry(frame=self._frameConfArrow, traceFunc=trashFunc, varType='double')
        self._stepYEntry = CompleteEntry(frame=self._frameConfArrow, traceFunc=trashFunc, varType='double')
        self._stepZEntry = CompleteEntry(frame=self._frameConfArrow, traceFunc=trashFunc, varType='double')
        self._stepCEntry = CompleteEntry(frame=self._frameConfArrow, traceFunc=trashFunc, varType='double')
        self._stepXEntry.var = 0.1
        self._stepYEntry.var = 0.1
        self._stepZEntry.var = 0.1
        self._stepCEntry.var = 0.1

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

        self._posXEntry = CompleteEntry(frame=self._framePos, traceFunc=trashFunc, varType='double', width=15,
                                        font='Arial 30', state='disable'
                                        , disabledbackground='white')
        self._posYEntry = CompleteEntry(frame=self._framePos, traceFunc=trashFunc, varType='double', width=15,
                                        font='Arial 30', state='disable'
                                        , disabledbackground='white')
        self._posZEntry = CompleteEntry(frame=self._framePos, traceFunc=trashFunc, varType='double', width=15,
                                        font='Arial 30', state='disable'
                                        , disabledbackground='white')
        self._posCEntry = CompleteEntry(frame=self._framePos, traceFunc=trashFunc, varType='double', width=15,
                                        font='Arial 30', state='disable'
                                        , disabledbackground='white')
        self._presEntry = CompleteEntry(frame=self._framePos, traceFunc=trashFunc, varType='double', width=15,
                                        font='Arial 30', state='disable'
                                        , disabledbackground='white')
        self._posXEntry.var = 0.1
        self._posYEntry.var = 0.1
        self._posZEntry.var = 0.1
        self._posCEntry.var = 0.1
        self._presEntryvar = 0.1

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
        self._commandEntry = CompleteEntry(frame=self._frameConsole, traceFunc=trashFunc, varType='str', width=40)
        self._commandEntry.var = ''
        self._clearB = ttk.Button(self._frameConsole, text='Clear', command=self.__clearConsole, width=10)
        self._sendB = ttk.Button(self._frameConsole, text='Send', command=self.__sendtmp, width=10)
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
        self.controller._driver.externalGcodeLine(self._commandVar.var)

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

    @deprecated
    def _setPosX(self, value):
        self._posXEntry.var = (round(value, 4))

    @deprecated
    def _setPosY(self, value):
        self._posYEntry.var = (round(value, 4))

    @deprecated
    def _setPosZ(self, value):
        self._posZEntry.var = (round(value, 4))

    @deprecated
    def _setPosC(self, value):
        self._posCEntry.var = (round(value, 4))

    @deprecated
    def _setPres(self, value):
        self._pres.var = (round(value, 4))

    @deprecated
    def _getStepX(self):
        return self._stepXEntry.var

    @deprecated
    def _getStepY(self):
        return self._stepYEntry.var

    @deprecated
    def _getStepZ(self):
        return self._stepZEntry.var

    @deprecated
    def _getStepC(self):
        return self._stepCEntry.var

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

    def setStepAxis(self, axisConf):
        for axis, val in axisConf.items():
            if axis == 'X':
                self._stepXEntry.var = val
            if axis == 'Y':
                self._stepYEntry.var = val
            if axis == 'Z':
                self._stepZEntry.var = val
            if axis == 'C':
                self._stepCEntry.var = val

    def getStepAxis(self):
        return {
            'X': self._stepXEntry.var,
            'Y': self._stepYEntry.var,
            'Z': self._stepZEntry.var,
            'C': self._stepCEntry.var,
        }

    def getContinueState(self):
        return self._contEnaVar.get()
        # return False

    def setContiniueState(self, state):
        self._contEnaVar.set(state)

    posX = property(fset=_setPosX)
    posY = property(fset=_setPosY)
    posZ = property(fset=_setPosZ)
    posC = property(fset=_setPosC)
    pres = property(fset=_setPres)
    cont = property(fset=setContiniueState)

    stepX = property(fget=_getStepX)
    stepY = property(fget=_getStepY)
    stepZ = property(fget=_getStepZ)
    stepC = property(fget=_getStepC)
    cont = property(fget=getContinueState)

    evState = property(fget=_getEvState)
    pumpState = property(fget=_getPumpState)


class ImportFrame(tk.Frame):
    def __init__(self, masterIHM, file, controller, fenetre, **kwargs):
        tk.Frame.__init__(self, fenetre, width=768, height=576, **kwargs)

        self._pathFile = file

        self._controller = controller
        self._masterIHM = masterIHM

        self._sepEntry = CompleteEntry(frame=self, traceFunc=trashFunc, varType='str')
        self._sepEntry.var = ','

        self._slEntry = CompleteEntry(frame=self, traceFunc=trashFunc, varType='int')
        self._slEntry.var = 1

        self._posRefEntry = CompleteEntry(frame=self, traceFunc=trashFunc, varType='int')
        self._posRefEntry.var = 0

        self._posValEntry = CompleteEntry(frame=self, traceFunc=trashFunc, varType='int')
        self._posValEntry.var = 1

        self._posPackEntry = CompleteEntry(frame=self, traceFunc=trashFunc, varType='int')
        self._posPackEntry.var = 2

        self._posXEntry = CompleteEntry(frame=self, traceFunc=trashFunc, varType='int')
        self._posXEntry.var = 3

        self._posYEntry = CompleteEntry(frame=self, traceFunc=trashFunc, varType='int')
        self._posYEntry.var = 4

        self._posTEntry = CompleteEntry(frame=self, traceFunc=trashFunc, varType='str')
        self._posTEntry.var = 5

        self._posName = CompleteEntry(frame=self, traceFunc=trashFunc, varType='str')
        self._posName.var = 'n'

        self._import = ttk.Button(self, text='Import', command=self.__importCmd, width=15)

        tk.Label(self, text="Name").grid(row=0, column=0, columnspan=2, sticky='e')
        self._posName.grid(row=0, column=2, columnspan=2, sticky='w')

        tk.Label(self, text="Reference (C1)").grid(row=2, column=0)
        tk.Label(self, text="Value (100nF)").grid(row=3, column=0)
        tk.Label(self, text="Package").grid(row=4, column=0)
        tk.Label(self, text="Separator").grid(row=5, column=0)

        self._posRefEntry.grid(row=2, column=1)
        self._posValEntry.grid(row=3, column=1)
        self._posPackEntry.grid(row=4, column=1)
        self._sepEntry.grid(row=5, column=1)

        tk.Label(self, text="X").grid(row=2, column=2)
        tk.Label(self, text="Y").grid(row=3, column=2)
        tk.Label(self, text="T").grid(row=4, column=2)
        tk.Label(self, text="Start line").grid(row=5, column=2)

        self._posXEntry.grid(row=2, column=3)
        self._posYEntry.grid(row=3, column=3)
        self._posTEntry.grid(row=4, column=3)
        self._slEntry.grid(row=5, column=3)

        self._import.grid(row=6, column=0, columnspan=4)

    def __importCmd(self):
        dicConf = {'X': self._posXEntry.var, 'Y': self._posYEntry.var, 'T': self._posTEntry.var,
                   'REF': self._posRefEntry.var, 'VAL': self._posValEntry.var, 'MOD': self._posPackEntry.var}
        self._controller.createFromCsv(self._posName.var, self._pathFile, self._sepEntry.var, self._slEntry.var,
                                       dicConf)
        self._masterIHM.initBoardMenu()


class JobFrame(tk.Frame):
    def __init__(self, fenetre, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)
        imgSize = (25, 25)

        self.globalFrame = fenetre

        self.__playImg = ImageTk.PhotoImage(Image.open('../resources/play.png').resize(imgSize))
        self.__playBtn = ttk.Button(self, image=self.__playImg)

        self.__pauseImg = ImageTk.PhotoImage(Image.open('../resources/pause.png').resize(imgSize))
        self.__pauseBtn = ttk.Button(self, image=self.__pauseImg)

        self.__stopImg = ImageTk.PhotoImage(Image.open('../resources/stop.png').resize(imgSize))
        self.__stopBtn = ttk.Button(self, image=self.__stopImg)

        self.__buildImg = ImageTk.PhotoImage(Image.open('../resources/build.png').resize(imgSize))
        self.__buildBtn = ttk.Button(self, image=self.__buildImg)

        self.__jobDesc = tk.Label(self, text='')
        self.__feederErrorList = tk.Label(self, text='', fg='red')

        self.__playBtn.grid(row=0, column=0)
        self.__pauseBtn.grid(row=0, column=1, padx=10)
        self.__stopBtn.grid(row=0, column=2)
        self.__buildBtn.grid(row=0, column=3, padx=10)
        self.__jobDesc.grid(row=1, column=0, columnspan=4)
        self.__feederErrorList.grid(row=2, column=0, columnspan=4)

        self.playButtonState(0)
        self.pauseButtonState(0)
        self.buildButtonState(0)
        self.stopButtonState(0)

    def setErrorList(self, strList):
        self.__feederErrorList['text'] = strList

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


class GlobalCmpFrame(tk.LabelFrame):
    def __init__(self, fenetre, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)
        self.board = 0
        self.cmpDisplayList = []
        self.controller = controller

        self._filterFrame = tk.Frame(self)
        self._cmpFrame = tk.Frame(self)
        self._btnFrame = tk.Frame(self)

        self._filterFrame.grid(row=0, column=0)
        self._cmpFrame.grid(row=1, column=0, sticky='nsew')
        self._btnFrame.grid(row=2, column=0)

        self._cmpTreeView = ttk.Treeview(self._cmpFrame, height=20)
        treeScroll = ttk.Scrollbar(self._cmpFrame)
        treeScroll.configure(command=self._cmpTreeView.yview)
        self._cmpTreeView.configure(yscrollcommand=treeScroll.set)
        self._cmpTreeView['columns'] = ('Ref', 'Package', 'Model', 'Feeder', 'X', 'Y', 'T', 'Placed', 'Enabled')
        self._cmpTreeView.column("#0", width=100, minwidth=100, stretch=tk.NO)
        self._cmpTreeView.column("Ref", width=50, minwidth=50, stretch=tk.NO)
        self._cmpTreeView.column("Package", width=100, minwidth=100, stretch=tk.NO)
        self._cmpTreeView.column("Model", width=100, minwidth=100, stretch=tk.NO)
        self._cmpTreeView.column("Feeder", width=50, minwidth=50, stretch=tk.NO)
        self._cmpTreeView.column("X", width=60, minwidth=60, stretch=tk.NO)
        self._cmpTreeView.column("Y", width=60, minwidth=60, stretch=tk.NO)
        self._cmpTreeView.column("T", width=60, minwidth=60, stretch=tk.NO)
        self._cmpTreeView.column("Placed", width=50, minwidth=50, stretch=tk.NO)
        self._cmpTreeView.column("Enabled", width=50, minwidth=50, stretch=tk.NO)
        self._cmpTreeView.heading('#0', text='Value', anchor=tk.CENTER)
        self._cmpTreeView.heading('Ref', text='Ref', anchor=tk.CENTER)
        self._cmpTreeView.heading('Package', text='Package', anchor=tk.CENTER)
        self._cmpTreeView.heading('Model', text='Model', anchor=tk.CENTER)
        self._cmpTreeView.heading('Feeder', text='Feeder', anchor=tk.CENTER)
        self._cmpTreeView.heading('X', text='X', anchor=tk.CENTER)
        self._cmpTreeView.heading('Y', text='Y', anchor=tk.CENTER)
        self._cmpTreeView.heading('T', text='T', anchor=tk.CENTER)
        self._cmpTreeView.heading('Placed', text='Placed', anchor=tk.CENTER)
        self._cmpTreeView.heading('Enabled', text='Enabled', anchor=tk.CENTER)

        self._cmpTreeView.grid(row=0, column=0, sticky='nsew')
        treeScroll.grid(row=0, column=1, sticky='ns')

        self._valueFilter = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._refFilter = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._packageFilter = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._modelFilter = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._placedFilter = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._enableFilter = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)

        self._modelEdit = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._feederEdit = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._placedEdit = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._enableEdit = CompleteEntry(self._filterFrame, trashFunc, varType='str', width=10)
        self._modelEdit.var = ''
        self._feederEdit.var = ''
        self._placedEdit.var = ''
        self._enableEdit.var = ''

        btnFilterApply = ttk.Button(self._filterFrame, text='Filter', command=self.filterApply)
        btnEditApply = ttk.Button(self._filterFrame, text='Edit', command=self.__editApply)

        self._btnGoTo = ttk.Button(self._btnFrame, text='GoTo', command=self.__goToCmd)
        self._bntPlace = ttk.Button(self._btnFrame, text='Place', command=self.__placeCmp)
        self._bntEdit = ttk.Button(self._btnFrame, text='Edit', command=self.__editCmp)

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

        # labelFrameScrol = tk.Frame(self._cmpFrameScrol.userFrame)

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

        self._btnGoTo.grid(row=0, column=0)
        self._bntPlace.grid(row=0, column=1)
        self._bntEdit.grid(row=0, column=2)

    def disableComponentButton(self):
        self._btnGoTo['state'] = 'disable'
        self._bntPlace['state'] = 'disable'
        self._bntEdit['state'] = 'disable'

    def enableComponentButton(self):
        self._btnGoTo['state'] = 'normal'
        self._bntPlace['state'] = 'normal'
        self._bntEdit['state'] = 'normal'

    def __placeCmp(self):
        refSel = self.__getSelectedRef()
        if len(refSel):
            if len(refSel) == 1:
                print('solo  ' + refSel[0])
                print(refSel)
                self.controller.pickAndPlaceCmp(refSel[0])
            else:
                print('multi   ')
                print(refSel)
                self.controller.buildLongJob(refSel)

    def __goToCmd(self):
        refSel = self.__getSelectedRef()
        if len(refSel):
            self.controller.goToCmp(refSel[0])

    def __editCmp(self):
        kiki = 0

    def __displayFilterList(self):
        """
        Display all component on treeview wich match with filter.
        """
        self.controller.board.filter['value'] = self._valueFilter.var
        self.controller.board.filter['ref'] = self._refFilter.var
        self.controller.board.filter['package'] = self._packageFilter.var
        self.controller.board.filter['model'] = self._modelFilter.var
        self.controller.board.filter['placed'] = self._placedFilter.var
        self.controller.board.filter['enable'] = self._enableFilter.var

        for i in self._cmpTreeView.get_children():
            self._cmpTreeView.delete(i)
        self.update()

        # Build reference list.
        valueList = []
        for cmp in self.cmpDisplayList:
            if cmp.value not in valueList:
                valueList.append(cmp.value)

        for value in valueList:
            self._cmpTreeView.insert(parent="", index="end", iid=value, text=value)

        for cmp in self.cmpDisplayList:
            dataCmp = (cmp.ref, cmp.package, cmp.model, cmp.feeder, f'{cmp.posX}', f'{cmp.posY}', f'{cmp.rot}',
                       f'{cmp.isPlaced}', f'{cmp.isEnable}')
            self._cmpTreeView.insert(iid=cmp.ref, text=cmp.value, parent=cmp.value, index="end", values=dataCmp)

    def filterApply(self):
        """
        Called by filter button or other for take care of filter writen in relative case.
        call __displayFilterList() for update display.
        """
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

        for cmp in self.board.cmpDic.values():
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

    def __getSelectedRef(self):
        """
        Return an array of the reference displayed AND selected.
        """
        selectedRef = []
        for selectedLine in self._cmpTreeView.selection():
            if self._cmpTreeView.parent(selectedLine) == '':
                # Selected line is a parent (group of component ex: 100nF).
                for cmp in self.cmpDisplayList:
                    if cmp.value == selectedLine:
                        if cmp.ref not in selectedRef:
                            selectedRef.append(cmp.ref)
            else:
                # Selected line is a child(comopnent ex: C2)
                if selectedLine not in selectedRef:
                    selectedRef.append(selectedLine)
        return selectedRef

    def __editApply(self):
        """
        Called by pressing apply button.
        This fonction modify all component selected and update display.
        """
        for selRef in self.__getSelectedRef():
            cmp = self.board.cmpDic[selRef]
            if len(self._modelEdit.var.replace(' ', '')):
                cmp.model = self._modelEdit.var
            if len(self._feederEdit.var.replace(' ', '')):
                cmp.feeder = int(self._feederEdit.var)
            if self._placedEdit.var == '1':
                cmp.isPlaced = 1
            elif self._placedEdit.var == '0':
                cmp.isPlaced = 0
            if self._enableEdit.var == '1':
                cmp.isEnable = 1
            elif self._enableEdit.var == '0':
                cmp.isEnable = 0
            self.componentHaveChanged(selRef)

    def setBoard(self, board):
        """
        Set board object.
        """
        self.board = board

    def setFilter(self, value, ref, pack, model, place, enable):
        """
        Set all filter entertext with specified value.
        """
        self._valueFilter.var = value
        self._refFilter.var = ref
        self._packageFilter.var = pack
        self._modelFilter.var = model
        self._placedFilter.var = place
        self._enableFilter.var = enable

    def componentHaveChanged(self, ref):
        """
        Call this for update displayed component when a component change.
        """
        if ref in self.__getSelectedRef():
            cmp = self.board.cmpDic[ref]
            newValue = [cmp.ref, cmp.package, cmp.model, cmp.feeder,
                        cmp.posX, cmp.posY, cmp.rot, cmp.isPlaced, cmp.isEnable]
            self._cmpTreeView.item(ref, values=newValue)


class BoardFrame(tk.Frame):
    """
    Main frame of board window.
    Board display.
    List of component.
    Job frame.
    """

    def __init__(self, fenetre, controller, logger, machine, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)

        self.controller = controller
        self._machineConf = machine
        self.rootCmpFrame = GlobalCmpFrame(self, controller)
        self.jobFrame = JobFrame(self)
        self._boardFrame = tk.LabelFrame(self, text="Board", labelanchor='n', padx=10, pady=0)

        self._pathFrame = tk.Frame(self._boardFrame, padx=10, pady=0)
        self._paramBoardFrame = tk.LabelFrame(self._boardFrame, text="Parameters", labelanchor='n', padx=10, pady=0)
        self._referenceFrame = BoardBasePlateFrame(self._boardFrame, self._machineConf, logger, controller)
        self._boardDraw = BoarDrawing(self._boardFrame)

        self._tableTopPath = CompleteEntry(self._pathFrame, varType='str', width=75)
        self._tableTopPath.var = ''
        self._pathBtn = ttk.Button(self._pathFrame, text='...', width=10, command=self._changeTableTopPath)

        self._sizeX = CompleteEntry(self._paramBoardFrame, self.__paramBoardChange, varType='double')
        self._sizeY = CompleteEntry(self._paramBoardFrame, self.__paramBoardChange, varType='double')
        self._sizeZ = CompleteEntry(self._paramBoardFrame, self.__paramBoardChange, varType='double')

        self._boardFrame.grid(row=0, column=0, rowspan=2)
        self.jobFrame.grid(row=0, column=1)
        self.rootCmpFrame.grid(row=1, column=1, rowspan=2, sticky='ns')

        self._pathFrame.grid(row=0, column=0)
        self._paramBoardFrame.grid(row=1, column=0)
        self._boardDraw.grid(row=2, column=0)
        self._referenceFrame.grid(row=3, column=0)

        tk.Label(self._pathFrame, text='TableTop path: ').grid(row=0, column=0)
        self._tableTopPath.grid(row=0, column=1)
        self._pathBtn.grid(row=0, column=2)

        tk.Label(self._paramBoardFrame, text="Size").grid(row=1, column=0)
        tk.Label(self._paramBoardFrame, text="Offset").grid(row=2, column=0)
        tk.Label(self._paramBoardFrame, text="X").grid(row=0, column=1)
        tk.Label(self._paramBoardFrame, text="Y").grid(row=0, column=2)
        tk.Label(self._paramBoardFrame, text="Z").grid(row=0, column=3)
        tk.Label(self._paramBoardFrame, text="T").grid(row=0, column=4)
        self._sizeX.grid(row=1, column=1)
        self._sizeY.grid(row=1, column=2)
        self._sizeZ.grid(row=1, column=3)

        # self._ref1 = CompleteEntry(self._referenceFrame, self.__paramBoardChange, varType='str')
        # self._ref2 = CompleteEntry(self._referenceFrame, self.__paramBoardChange, varType='str')

        # tk.Label(self._referenceFrame, text="Ref N°1").grid(row=1, column=0)
        # tk.Label(self._referenceFrame, text="Ref N°2").grid(row=2, column=0)
        # self._ref1.grid(row=1, column=1)
        # self._ref2.grid(row=2, column=1)

    def _changeTableTopPath(self):
        path = tkinter.filedialog.askopenfilename(title="Open Machine file", filetypes=[('XML files', '.xml')])
        self.controller.changeAndLoadMachineConf(os.path.relpath(path))
        self._tableTopPath.var = self.controller.board.tableTopPath

    def setboardParam(self, board):
        self._board = board
        self._sizeX.var = board.xSize
        self._sizeY.var = board.ySize
        self._sizeZ.var = board.zSize
        self._tableTopPath.var = board.tableTopPath

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

        self._boardDraw.drawBoard(self.controller.board, self.controller.modList)

    def bomCreate(self, board):
        self.rootCmpFrame.setFilter(value=board.filter['value'], ref=board.filter['ref'], pack=board.filter['package'],
                                    model=board.filter['model'], place=board.filter['placed'],
                                    enable=board.filter['enable'])

        self.rootCmpFrame.setBoard(board)
        self.rootCmpFrame.filterApply()
        self._boardDraw.drawBoard(board, self.controller.modList)
        self._referenceFrame.setBoard(board)

    def cmpHaveChanged(self, ref):
        """
        Program mus call this when the state of a cmp have changed
        :param ref:
        :return:
        """
        self.rootCmpFrame.componentHaveChanged(ref)



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
        self._modelOm = ttk.OptionMenu(frameTop, self._strModel, *self._modelList)

        self._aliasList = ['toto']
        self._strAlias = tk.StringVar()
        self._strAlias.set(self._aliasList[0])
        self._aliasOm = ttk.OptionMenu(frameAlias, self._strAlias, *self._aliasList)

        newModBtn = ttk.Button(frameTop, text='New', width=15,
                               command=lambda: EntryWindow(self, 'New model', ['Model Name'], ['Name'],
                                                           self.__userAddModelReturn, 0))
        dellModBtn = ttk.Button(frameTop, text='Delete', width=15, command=self.__deleteModel)
        addBtn = ttk.Button(frameAlias, text='Add',
                            command=lambda: EntryWindow(self, 'New Alias', ['Alias Name'], ['Name'],
                                                        self.__userAddAliasReturn, 0))
        dellBtn = ttk.Button(frameAlias, text='Del', command=self.__deleteAlias)
        saveBtn = ttk.Button(frameCtrl, text='Save', command=self.controller.saveInFile)

        self._sX = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._sY = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._sZ = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._scanHentry = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._pressureTargetEntry = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._correctorList = ['None', 'Mechanical', 'Optical']
        self._strCorrector = tk.StringVar()
        self._strCorrector.set(self._correctorList[0])
        self._correctorModeOm = ttk.OptionMenu(frameInfo, self._strCorrector, *self._correctorList,
                                               command=self.__dataChange)

        self._pickupSpeed = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._placeSpeed = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._pickupDelay = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._placeDelay = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')
        self._moveSpeed = CompleteEntry(frame=frameInfo, traceFunc=self.__dataChange, varType='double')

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
        tk.Label(frameInfo, text="Pressure target").grid(row=4, column=0)
        tk.Label(frameInfo, text="Corrector mode").grid(row=5, column=0)
        tk.Label(frameInfo, text="Pickup speed(mm/min)").grid(row=0, column=2)
        tk.Label(frameInfo, text="Pickup delay(ms)").grid(row=1, column=2)
        tk.Label(frameInfo, text="Place speed(mm/min)").grid(row=2, column=2)
        tk.Label(frameInfo, text="Place delay(ms)").grid(row=3, column=2)
        tk.Label(frameInfo, text="Move speed(ms)").grid(row=4, column=2)

        self._sX.grid(row=0, column=1)
        self._sY.grid(row=1, column=1)
        self._sZ.grid(row=2, column=1)
        self._scanHentry.grid(row=3, column=1)
        self._pressureTargetEntry.grid(row=4, column=1)
        self._correctorModeOm.grid(row=5, column=1)
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
        self._pressureTargetEntry['state'] = 'normal'

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
        self._pressureTargetEntry['state'] = 'disable'

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
        self.controller.modList[self._strModel.get()].pressureTarget = self._pressureTargetEntry.var
        self.controller.modList[self._strModel.get()].correctorMode = self._strCorrector.get()

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
        self._pressureTargetEntry.var = model.pressureTarget

        self.deleteAliaslList()
        for alias in model.aliasList:
            self.__addAlias(alias)
        if len(model.aliasList):
            self._strAlias.set(model.aliasList[-1])
        else:
            self._strAlias.set('')

        self._strCorrector.set(model.correctorMode)

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


class ScanFrame(tk.Frame):
    """Frame used for place cmp."""

    def __init__(self, fenetre, logger, **kwargs):
        tk.Frame.__init__(self, fenetre, **kwargs)
        self._logger = logger

        self._labMes = tk.Label(self, text='Measure: 00000')
        self._zScan = CompleteEntry(frame=self, traceFunc=trashFunc, varType='double')
        self._btnGoTo = ttk.Button(self, text='Go TO')
        self._btnScanPoint = ttk.Button(self, text='Scan point')
        self._btnScanXLine = ttk.Button(self, text='Scan Line X')
        self._btnScanYLine = ttk.Button(self, text='Scan Line Y')
        self._btnScan3D = ttk.Button(self, text='Scan 3D')
        self._btnFace = ttk.Button(self, text='Face 3D')
        self._btnCircle = ttk.Button(self, text='circle')

        self._labMes.grid(row=0, column=0, columnspan=2)
        tk.Label(self, text='zScan:').grid(row=1, column=0)
        self._zScan.grid(row=1, column=1)
        self._btnGoTo.grid(row=2, column=0)
        self._btnScanPoint.grid(row=2, column=1)
        self._btnScanXLine.grid(row=3, column=0)
        self._btnScanYLine.grid(row=3, column=1)
        self._btnCircle.grid(row=4, column=0)
        self._btnScan3D.grid(row=5, column=0)
        self._btnFace.grid(row=5, column=1)

    def setMeasureValue(self, value):
        self._labMes['text'] = 'Mesure: {}'.format(value)

    def getZscan(self):
        return self._zScan.var

    def setScan3Dcb(self, cb):
        self._btnScan3D['command'] = cb

    def setScanCirclecb(self, cb):
        self._btnCircle['command'] = cb

    def setScanFacecb(self, cb):
        self._btnFace['command'] = cb

    def setScanXLinecb(self, cb):
        self._btnScanXLine['command'] = cb

    def setScanYLinecb(self, cb):
        self._btnScanYLine['command'] = cb

    def setScanPointcb(self, cb):
        self._btnScanPoint['command'] = cb

    def setGoTOcb(self, cb):
        self._btnGoTo['command'] = cb


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
                ttk.Button(self._fr, width=10, text="{}{}".format(chr(i + 65), t)).grid(row=i, column=t)
        c.create_window(0, 0, window=self._fr)
        self._fr.update_idletasks()
        c.config(scrollregion=c.bbox("all"))


class PanelizeFrame(tk.Frame):
    def __init__(self, fenetre, logger, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, width=500, height=300, **kwargs)

        self._controller = controller

        self._countXEntry = CompleteEntry(frame=self, varType='int')
        self._countYEntry = CompleteEntry(frame=self, varType='int')
        self._offsetXEntry = CompleteEntry(frame=self, varType='double')
        self._offsetYEntry = CompleteEntry(frame=self, varType='double')
        self._paneliseBtn = ttk.Button(self, text='Panelize', command=self._localBtnCb)

        tk.Label(self, text='Count').grid(row=0, column=1)
        tk.Label(self, text='Offset').grid(row=0, column=2)
        tk.Label(self, text='X').grid(row=1, column=0)
        tk.Label(self, text='Y').grid(row=2, column=0)

        self._countXEntry.grid(row=1, column=1)
        self._countYEntry.grid(row=2, column=1)
        self._offsetXEntry.grid(row=1, column=2)
        self._offsetYEntry.grid(row=2, column=2)
        self._paneliseBtn.grid(row=3, column=2)

    def _localBtnCb(self):
        self._controller.panelizeBoard(countX=self._countXEntry.var, countY=self._countYEntry.var,
                                       offsetX=self._offsetXEntry.var, offsetY=self._offsetYEntry.var)


class BoardTransformFrame(tk.Frame):
    def __init__(self, fenetre, logger, controller, **kwargs):
        tk.Frame.__init__(self, fenetre, width=500, height=300, **kwargs)

        self._controller = controller

        self._rotateEntry = CompleteEntry(frame=self, varType='double')
        self._applyRotateBtn = ttk.Button(self, text='Apply rotation', command=self._rotation)
        self._applyHMirrorBtn = ttk.Button(self, text='Apply horizontal mirror', command=self._horizontalMirror)
        self._applyVMirrorBtn = ttk.Button(self, text='Apply vertical mirror', command=self._verticalMirror)

        tk.Label(self, text='Rotation in deg').grid(row=0, column=0)
        self._rotateEntry.grid(row=1, column=0)
        self._applyRotateBtn.grid(row=1, column=1)
        self._applyHMirrorBtn.grid(row=2, column=1)
        self._applyVMirrorBtn.grid(row=3, column=1)

    def _rotation(self):
        self._controller.boardRotation(self._rotateEntry.var)

    def _verticalMirror(self):
        self._controller.boardVerticalMirror()

    def _horizontalMirror(self):
        self._controller.boardHorizontalMirror()


class JobConfigurationFrame(tk.Frame):
    def __init__(self, fenetre, parameters, **kwargs):
        tk.Frame.__init__(self, fenetre, width=500, height=300, **kwargs)

        self._parameters = parameters
        self._paramFrame = tk.Frame(self)
        self._btnFrame = tk.Frame(self)

        self._paramFrame.grid(row=0, column=0)
        self._btnFrame.grid(row=1, column=0)

        self._homeCntNumber = CompleteEntry(frame=self._paramFrame, varType='int', traceFunc=self._homeCntNumberChange)
        self._homeCntNumber.var = self._parameters['JOB']['homeCmpCount']

        tk.Label(self._paramFrame, text='Component before home').grid(row=0, column=0)
        self._homeCntNumber.grid(row=0, column=1)

        self._applyRotateBtn = ttk.Button(self._btnFrame, text='Save', command=self._save)
        self._applyRotateBtn.grid(row=0, column=0)

    def _homeCntNumberChange(self):
        self._parameters['JOB']['homeCmpCount'] = str(self._homeCntNumber.var)

    def _save(self):
        self._parameters.saveConf()


class PnpIHM:
    """High level class for IHM view
    """

    def __init__(self, controller, logger):
        self.ctrl = controller  # Hight level class of self.controller.
        self.ctrl.boardCtrl.enableSaveFunc = self.boardIsLoad

        self.mainWindow = tk.Tk()  # Instance of main window.
        self.mainWindow.title('MiniPnp - OXILEC V2.1')
        # self.mainWindow.maxsize(width=1500, height=800)

        self.ctrlWindow = CtrlFrame(self.mainWindow, self.ctrl.directCtrl)
        logger.ihmDirect = self.ctrlWindow

        self.paramWindow = ParamFrame(self.mainWindow, self.ctrl.paramCtrl, self.ctrl.machineConfiguration)
        self.feederWindow = FeederFrame(self.mainWindow, self.ctrl.machineConfiguration, logger, self.ctrl.boardCtrl,
                                        padx=10, pady=10)
        self.basePlateWindow = BasePlateFrame(self.mainWindow, self.ctrl.machineConfiguration, logger,
                                              self.ctrl.boardCtrl)

        self.brdWindow = BoardFrame(self.mainWindow, self.ctrl.boardCtrl, logger, self.ctrl.machineConfiguration)
        self.ctrl.boardCtrl.ihm = self.brdWindow

        self.dtbWindow = DtbFrame(self.mainWindow, self.ctrl.dtbCtrl)
        self.debugWindow = DebugFrame(self.mainWindow)

        self.scanWindow = ScanFrame(self.mainWindow, logger)
        self.panelizeWindow = PanelizeFrame(self.mainWindow, logger, self.ctrl.boardCtrl)
        self.boardTransformWindow = BoardTransformFrame(self.mainWindow, logger, self.ctrl.boardCtrl)
        self.JobConfigurationWindow = JobConfigurationFrame(self.mainWindow, self.ctrl.preferences)

        self.topMenuBar = tk.Menu(self.mainWindow)
        self._menuFile = tk.Menu(self.topMenuBar, tearoff=0)
        self._menuTableTop = tk.Menu(self.topMenuBar, tearoff=0)
        self._menuTools = tk.Menu(self.topMenuBar, tearoff=0)
        self._menuPreferences = tk.Menu(self.topMenuBar, tearoff=0)

        self.topMenuBar.add_cascade(label="File ", menu=self._menuFile)
        self.topMenuBar.add_command(label="Board ", command=self.initBoardMenu, state='disabled')
        self.topMenuBar.add_command(label="DataBase", command=self.initDtbMenu)
        self.topMenuBar.add_command(label="Control", command=self.initCtrlMenu)
        self.topMenuBar.add_cascade(label="TableTop", menu=self._menuTableTop)
        self.topMenuBar.add_cascade(label="Tools", menu=self._menuTools)
        self.topMenuBar.add_cascade(label="Preferences", menu=self._menuPreferences)
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
        self._menuTableTop.add_command(label="Base plate ", command=self.initBasePlateMenu)
        self._menuTableTop.add_command(label="Scan ", command=self.initScanMenu)
        self._menuTableTop.add_separator()
        self._menuTableTop.add_command(label="Save ", command=self.ctrl.machineConfiguration.saveToXml)

        self._menuPreferences.add_command(label="Job ", command=self.initJobPreference)

        self._menuTools.add_command(label="Panelize ", state='disabled', command=self.initPanelizeMenu)
        self._menuTools.add_command(label="Board transfrom ", state='disabled', command=self.initBoardTransformMenu)

        self._statusLabel = tk.Label(self.mainWindow, text='Searching device...', font='Arial 20 bold')
        self.actualFrame = self.paramWindow
        self.initCtrlMenu()

        self.ctrl.setTopIHM(self)
        self.ctrl.bindInit()
        self.ctrl.discoveringDevice()
        self.ctrl.updateStatusOnIHM()
        self.ctrl.scanCtrl.linkCallBack(self.scanWindow)
        self.paramWindow.update()

        self.mainWindow.mainloop()

    def initCtrlMenu(self):
        if self.actualFrame is not self.ctrlWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.ctrlWindow.pack()
            self._statusLabel.pack()
            self.actualFrame = self.ctrlWindow;
            # self.ctrlWindow.serialFrame.listCom()
            self.ctrlWindow.focus_force()

    def initParamMenu(self):
        if self.actualFrame is not self.paramWindow:
            self.paramWindow.update()
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

    def initBasePlateMenu(self):
        if self.actualFrame is not self.basePlateWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.basePlateWindow.pack()
            self.actualFrame = self.basePlateWindow
            self.basePlateWindow.focus_force()
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

    def initScanMenu(self):
        if self.actualFrame is not self.scanWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.scanWindow.pack()
            self.actualFrame = self.scanWindow;
            self._statusLabel.pack()

    def initPanelizeMenu(self):
        if self.actualFrame is not self.panelizeWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.panelizeWindow.pack()
            self.actualFrame = self.panelizeWindow;
            self._statusLabel.pack()

    def initBoardTransformMenu(self):
        if self.actualFrame is not self.boardTransformWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.boardTransformWindow.pack()
            self.actualFrame = self.boardTransformWindow;
            self._statusLabel.pack()

    def initJobPreference(self):
        if self.actualFrame is not self.JobConfigurationWindow:
            self.actualFrame.pack_forget()
            self._statusLabel.pack_forget()
            self.JobConfigurationWindow.pack()
            self.actualFrame = self.JobConfigurationWindow;
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
        self._menuTools.entryconfigure('Panelize ', state=state)
        self._menuTools.entryconfigure('Board transfrom ', state=state)
        # self.panelizeWindow.setPaneliseCallBack(self.ctrl.boardCtrl.panelizeBoard)

    def setStatusLabel(self, text1, text2=''):
        self._statusLabel['text'] = text1 + '\n' + text2

    def setBind(self, event, key, calBack):
        self.mainWindow.bind("<{}-{}>".format(event, key), calBack)
