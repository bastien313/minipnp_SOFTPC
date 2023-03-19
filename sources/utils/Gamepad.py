from ctypes import WinDLL, WinError, Structure, POINTER, byref, c_ubyte
from ctypes.util import find_library
from ctypes.wintypes import DWORD, WORD, SHORT
import threading, queue
import time

# for some reason wintypes.BYTE is defined as signed c_byte and as c_ubyte
BYTE = c_ubyte

# Max number of controllers supported
XUSER_MAX_COUNT = 4


class XINPUT_BUTTONS(Structure):
    """Bit-fields of XINPUT_GAMEPAD wButtons"""

    _fields_ = [
        ("DPAD_UP", WORD, 1),
        ("DPAD_DOWN", WORD, 1),
        ("DPAD_LEFT", WORD, 1),
        ("DPAD_RIGHT", WORD, 1),
        ("START", WORD, 1),
        ("BACK", WORD, 1),
        ("LEFT_THUMB", WORD, 1),
        ("RIGHT_THUMB", WORD, 1),
        ("LEFT_SHOULDER", WORD, 1),
        ("RIGHT_SHOULDER", WORD, 1),
        ("_reserved_1_", WORD, 1),
        ("_reserved_1_", WORD, 1),
        ("A", WORD, 1),
        ("B", WORD, 1),
        ("X", WORD, 1),
        ("Y", WORD, 1)
    ]

    def __repr__(self):
        r = []
        for name, type, size in self._fields_:
            if "reserved" in name:
                continue
            r.append("{}={}".format(name, getattr(self, name)))
        args = ', '.join(r)
        return f"XINPUT_GAMEPAD({args})"

    def getDictRepr(self):
        dictout = {}
        for name, type, size in self._fields_:
            dictout[name] = getattr(self, name)
        return dictout


class XINPUT_GAMEPAD(Structure):
    """Describes the current state of the Xbox 360 Controller.

    https://docs.microsoft.com/en-us/windows/win32/api/xinput/ns-xinput-xinput_gamepad

    wButtons is a bitfield describing currently pressed buttons
    """
    _fields_ = [
        ("wButtons", XINPUT_BUTTONS),
        ("bLeftTrigger", BYTE),
        ("bRightTrigger", BYTE),
        ("sThumbLX", SHORT),
        ("sThumbLY", SHORT),
        ("sThumbRX", SHORT),
        ("sThumbRY", SHORT),
    ]

    def __repr__(self):
        r = []
        for name, type in self._fields_:
            r.append("{}={}".format(name, getattr(self, name)))
        args = ', '.join(r)
        return f"XINPUT_GAMEPAD({args})"

    def getDictRepr(self):
        dictout = {}
        for name, type in self._fields_:
            dictout[name] = getattr(self, name)
        return dictout


class XINPUT_STATE(Structure):
    """Represents the state of a controller.

    https://docs.microsoft.com/en-us/windows/win32/api/xinput/ns-xinput-xinput_state

    dwPacketNumber: State packet number. The packet number indicates whether
        there have been any changes in the state of the controller. If the
        dwPacketNumber member is the same in sequentially returned XINPUT_STATE
        structures, the controller state has not changed.
    """
    _fields_ = [
        ("dwPacketNumber", DWORD),
        ("Gamepad", XINPUT_GAMEPAD)
    ]

    def __repr__(self):
        return f"XINPUT_STATE(dwPacketNumber={self.dwPacketNumber}, Gamepad={self.Gamepad})"


class XInput:
    """Minimal XInput API wrapper"""

    def __init__(self):
        # https://docs.microsoft.com/en-us/windows/win32/xinput/xinput-versions
        # XInput 1.4 is available only on Windows 8+.
        # Older Windows versions are End Of Life anyway.
        lib_name = "XInput1_4.dll"
        lib_path = find_library(lib_name)
        if not lib_path:
            raise Exception(f"Couldn't find {lib_name}")
        self._XInput_ = WinDLL(lib_path)
        self._XInput_.XInputGetState.argtypes = [DWORD, POINTER(XINPUT_STATE)]
        self._XInput_.XInputGetState.restype = DWORD

    def GetState(self, dwUserIndex):
        state = XINPUT_STATE()
        ret = self._XInput_.XInputGetState(dwUserIndex, byref(state))
        if ret:
            raise WinError(ret)
        return state.dwPacketNumber, state.Gamepad


class AppGamepad(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._xi = XInput()
        self._running = True
        self._deviceDetected = False
        self._oldBtnState = XINPUT_GAMEPAD().getDictRepr()
        self._oldBtnState.update(XINPUT_BUTTONS().getDictRepr())
        del self._oldBtnState['wButtons']

        self._callBack = XINPUT_GAMEPAD().getDictRepr()
        self._callBack.update(XINPUT_BUTTONS().getDictRepr())
        del self._callBack['wButtons']
        keyList = [key for key in self._callBack]
        self._callBack = {}
        for item in keyList:
            self._callBack[item] = {'combo': {}, 'press': lambda: None, 'release': lambda: None}
        self._callBack['connection'] = {'press': lambda: None, 'release': lambda: None}
        self._oldGlobalState = 0

    def run(self):
        while self._running:
            try:
                deviceDetected = True
                newGlobalState, newBtnState = self._xi.GetState(0)

            except:
                deviceDetected = False

            if deviceDetected:
                if newGlobalState != self._oldGlobalState:
                    self._oldGlobalState = newGlobalState
                    self._changeManagment(newBtnState)

            if deviceDetected and not self._deviceDetected:
                self._callBack['connection']['press']()
            elif not deviceDetected and self._deviceDetected:
                self._callBack['connection']['release']()

            self._deviceDetected = deviceDetected
            time.sleep(0.05)

    def _changeManagment(self, newButtonState):
        newDicBtnState = newButtonState.getDictRepr()
        del newDicBtnState['wButtons']
        newDicBtnState.update(newButtonState.wButtons.getDictRepr())

        for key in self._oldBtnState:
            self._keyEvent(key, newDicBtnState)

    def _keyEvent(self, key, newDicBtnState):

        if self._oldBtnState[key] < newDicBtnState[key]:
            for comboKey, comboValue in self._callBack[key]['combo'].items():
                if newDicBtnState[comboKey] and 'press' in comboValue:
                    comboValue['press']()
                    self._oldBtnState[key] = newDicBtnState[key]
                    return
            self._callBack[key]['press']()
        elif self._oldBtnState[key] > newDicBtnState[key]:
            for comboKey, comboValue in self._callBack[key]['combo'].items():
                if newDicBtnState[comboKey] and 'release' in comboValue:
                    comboValue['release']()
                    self._oldBtnState[key] = newDicBtnState[key]
                    return
            self._callBack[key]['release']()
        self._oldBtnState[key] = newDicBtnState[key]

    def setPresCallBack(self, key, callBack):
        self._callBack[key]['press'] = callBack

    def setReleaseCallBack(self, key, callBack):
        self._callBack[key]['release'] = callBack

    def setComboPressCallBack(self, key, comboKey, callBack):
        if comboKey in self._callBack[key]['combo']:
            self._callBack[key]['combo'][comboKey]['press'] = callBack
        else:
            self._callBack[key]['combo'][comboKey] = {'press': callBack, 'release': lambda: None}

    def setComboReleaseCallBack(self, key, comboKey, callBack):
        if comboKey in self._callBack[key]['combo']:
            self._callBack[key]['combo'][comboKey]['release'] = callBack
        else:
            self._callBack[key]['combo'][comboKey] = {'press': lambda: None, 'release': callBack}
