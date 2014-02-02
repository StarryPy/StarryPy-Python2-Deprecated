import logging
TRACE_LVL = 9
logging.addLevelName(TRACE_LVL, "TRACE")

def trace(self, message, *args, **kws):
    self._log(TRACE_LVL, message, args, **kws)
logging.Logger.trace = trace