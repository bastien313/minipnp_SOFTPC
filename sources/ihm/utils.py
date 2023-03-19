import tkinter as tk
from tkinter import ttk


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


class ValidWindow(tk.Toplevel):
    """
    Create a windows with Yes or no button(text can be changed) and a user frame.
    Yer or no button call the user callback with True text if yes is pressed or False if no is pressed.
    """

    def __init__(self, frame, userFrame, callBack=lambda x: None, yesText='Yes', noText='No', **kwargs):
        tk.Toplevel.__init__(self, frame, **kwargs)
        btnFrame = tk.Frame(self)
        ttk.Button(btnFrame, text=yesText, command=lambda: callBack(True)).grid(row=0, column=0)
        ttk.Button(btnFrame, text=noText, command=lambda: callBack(False)).grid(row=0, column=1)
        userFrame.grid(row=0, column=0)
        btnFrame.grid(row=1, column=0)


class EntryWindow:
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

        btnOk = ttk.Button(btnFrame, text='OK', command=self.__okBtn)
        btnCanc = ttk.Button(btnFrame, text='Cancel', command=self.__cancelBtn)

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


class CompleteEntry(tk.Entry):
    """
    Entry wich contain its own Var and traceCotrol.
    Used for disable trace when var is not edited by user IHM.
    """

    def __init__(self, frame, traceFunc=None, varType='str', **kwargs):
        tk.Entry.__init__(self, frame, **kwargs)
        self._frame = frame
        self._traceFunc = traceFunc
        self._varString = tk.StringVar(self._frame, '0')
        self._varString.trace_id = self._varString.trace("w", self._localTrace)
        self._varType = varType
        self.configure(textvariable=self._varString)
        self.lastVar = 0
        self.config(highlightthickness=1)
        self.config(highlightcolor='SystemButtonFace', highlightbackground='SystemButtonFace')

    def setTraceFunc(self, func):
        self._traceFunc = func

    def _localTrace(self, *args):
        newVarIsValid = False
        if self._varType == 'int':
            if self._varString.get().isdecimal():
                self.lastVar = int(self._varString.get())
                newVarIsValid = True
        elif self._varType == 'double' or self._varType == 'float':
            try:
                float(self._varString.get())
            except:
                pass
            else:
                self.lastVar = float(self._varString.get())
                newVarIsValid = True
        else:
            newVarIsValid = True
            self.lastVar = self._varString.get()

        if newVarIsValid:
            self.config(highlightcolor='SystemButtonFace', highlightbackground='SystemButtonFace')

        else:
            self.config(highlightcolor="red", highlightbackground="red")

        if self._traceFunc and newVarIsValid:
            self._traceFunc()

    def _getVar(self):
        return self.lastVar

    def _setVar(self, val):
        self._varString.trace_vdelete("w", self._varString.trace_id)

        if self._varType == 'int' and type(val) is int:
            self._varString.set(f'{val}')
            self.lastVar = val
        elif self._varType == 'double' or self._varType == 'float' and type(val) is float:
            self._varString.set(f'{val}')
            self.lastVar = val
        else:
            self._varString.set(val)
            self.lastVar = val

        self._varString.trace_id = self._varString.trace("w", self._localTrace)

    var = property(fset=_setVar, fget=_getVar)


class MultipleEntryFrame(tk.LabelFrame):
    def __init__(self, fenetre, parametersDict, traceFunc=None, **kwargs):
        tk.LabelFrame.__init__(self, fenetre, **kwargs)
        self.entryDict = {}

        idDict = 0
        for key, varType in parametersDict.items():
            self.entryDict[key] = CompleteEntry(self, traceFunc, varType=varType, width=15)
            tk.Label(self, text=key).grid(row=idDict, column=0)
            self.entryDict[key].grid(row=idDict, column=1)
            idDict += 1

    def __getitem__(self, index):
        """Cette méthode spéciale est appelée quand on fait objet[index]
        Elle redirige vers self._dictionnaire[index]"""
        return self.entryDict[index].var

    def __setitem__(self, index, valeur):
        """Cette méthode est appelée quand on écrit objet[index] = valeur
        On redirige vers self._dictionnaire[index] = valeur"""
        self.entryDict[index].var = valeur

    def disable(self):
        for entry in self.entryDict.values():
            entry['state'] = 'disable'

    def enable(self):
        for entry in self.entryDict.values():
            entry['state'] = 'normal'

    def setTraceFunc(self, func):
        for entry in self.entryDict.values():
            entry.setTraceFunc(func)

    def _getx(self):
        return self.entryDict['X'].var

    def _setx(self, val):
        self.entryDict['X'].var = val

    def _gety(self):
        return self.entryDict['Y'].var

    def _sety(self, val):
        self.entryDict['Y'].var = val

    def _getz(self):
        return self.entryDict['Z'].var

    def _setz(self, val):
        self.entryDict['Z'].var = val

    x = property(fget=_getx, fset=_setx)
    y = property(fget=_gety, fset=_sety)
    z = property(fget=_getz, fset=_setz)


class XYZFrame(MultipleEntryFrame):
    def __init__(self, fenetre, **kwargs):
        parametersDict = {
            'X': 'float',
            'Y': 'float',
            'Z': 'float'
        }
        MultipleEntryFrame.__init__(self, fenetre, parametersDict, **kwargs)

    def _setX(self, val):
        self['X'] = val

    def _setY(self, val):
        self['Y'] = val

    def _setZ(self, val):
        self['Z'] = val

    def _getX(self):
        return self['X']

    def _getY(self):
        return self['Y']

    def _getZ(self):
        return self['Z']

    x = property(fset=_setX, fget=_getX)
    y = property(fset=_setY, fget=_getY)
    z = property(fset=_setZ, fget=_getZ)


class XYZCFrame(XYZFrame):
    def __init__(self, fenetre, **kwargs):
        parametersDict = {
            'X': 'float',
            'Y': 'float',
            'Z': 'float',
            'C': 'float'
        }
        MultipleEntryFrame.__init__(self, fenetre, parametersDict, **kwargs)

    def _setC(self, val):
        self['C'] = val

    def _getC(self):
        return self['C']

    c = property(fset=_setC, fget=_getC)
