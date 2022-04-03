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
