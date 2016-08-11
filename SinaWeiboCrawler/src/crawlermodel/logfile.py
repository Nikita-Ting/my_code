# encoding:utf-8

'''
created on 2014-4-29
this is logging part of crawler
'''

import logging
import os
import time
import settings


class LogFile(object):

    def __init__(self):
        self.filePath=settings.PATH
        self.logPath=os.path.join(self.filePath,settings.FILE_PATH_DEFAULT)
        #日志文件保存路径
         
    def getLogger(self, className):
#         logger=logging.getLogger('run')
#         logger.setLevel(logging.ERROR)
        dayDate = str(time.strftime("%Y-%m-%d"))#获取系统时间
        self.logDayName = dayDate
        logFileName = os.path.join(self.logPath,
                                   ("%s_%s_run.log" % (className,self.logDayName)))
#         handler=logging.FileHandler(logFileName)
#         formatter = logging.Formatter(fmt=('%(asctime)s-%(module)s.%(funcName)s.'
#                                        '%(lineno)d-%(levelname)s-%(message)s'))
#         handler.setFormatter(formatter)
#         handler.setLevel(logging.ERROR)
        logLevel = logging.DEBUG
        logging.basicConfig(level=logLevel,
                            format='%(asctime)s %(levelname)s %(message)s',
                            filename=logFileName,
                            filemode='a')
        return logging.getLogger(className)
    
    def debugMsg(self, msg):
        self.getLogger("DEBUG").debug(msg)
         
if __name__ == '__main__':        
    logger = LogFile().getLogger('logfile')
    logger.debug('test')
