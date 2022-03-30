# coding: utf-8

import IHM as ih
import Controller as ct
import PnpDriver as drv
import logger as lg

globalLogger = lg.logger()
pnpDrv = drv.pnpDriver(globalLogger)
pnpCtrl = ct.PnpConroller(pnpDrv, globalLogger)
pnpIhm = ih.PnpIHM(pnpCtrl, globalLogger)
