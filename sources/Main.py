# coding: utf-8

from ihm import IHM as ih
from controller import Controller as ct, PnpDriver as drv
from sources.utils import logger as lg

globalLogger = lg.Logger()
pnpDrv = drv.PnpDriver(globalLogger)
pnpCtrl = ct.PnpConroller(pnpDrv, globalLogger)
pnpIhm = ih.PnpIHM(pnpCtrl, globalLogger)
