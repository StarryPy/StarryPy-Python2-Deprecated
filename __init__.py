import logging

VDEBUG_LVL = 9 
logging.addLevelName(VDEBUG_LVL, "VDEBUG")
def vdebug(self, message, *args, **kws):
    if self.isEnabledFor(VDEBUG_LVL):
        self._log(VDEBUG_LVL, message, args, **kws) 
logging.Logger.vdebug = vdebug
