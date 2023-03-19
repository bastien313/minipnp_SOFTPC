# coding: utf-8


from utils import logger
from controller import PnpDriver, Controller
from ihm import IHM

globalLogger = logger.Logger()
pnpDrv = PnpDriver.PnpDriver(globalLogger)
pnpCtrl = Controller.PnpConroller(pnpDrv, globalLogger)
pnpIhm = IHM.PnpIHM(pnpCtrl, globalLogger)
