# encoding:utf-8

'''
created on 2014-5-6
this is a thread to prepar start crawler action
part of src come from the Pameng
'''


import wx
import sys
import threading
import settings

from crawlermodel.logfile import LogFile
from crawlermodel.configUser import ConfigUser
from sina.crawlerthread import Crawlerthread


logger=LogFile().getLogger("StartCrawlerThread")

class StartCrawlerThread(threading.Thread):

    def __init__(self,threadNumber,window,event):
        threading.Thread.__init__(self)
        self.threadNum=threadNumber
        self.window=window
        self.quitTime=threading.Event()
        self.quitTime.clear()
        self.event=event
        self.configUser=ConfigUser(settings.PATH)
        
    def run(self):
        try:
            if self.window.CRAWLER_STATUS==0:#非采集状态时开启线程
                if self.event is None:#？
                    self.window.crawlerCount +=1
                msg=u"--------开始第 %d 次采集--------" % self.window.crawlerCount
                wx.CallAfter(self.window.WriteLogger,msg)
                logger.info(msg)
                wx.CallAfter(self.window.ReInit)#更新数据/在采集线程结束时也该更新？Crawlerrunning=false
                savePath=self.window.savePathText.GetValue().strip() 
                print savePath
                if savePath=="":
                    savePath=self.window.taskPath
                self.window.resultPath=savePath
                self.configUser.WriteUserConfig("savePath",savePath)
                self.StartCrawler()
            else:
                wx.CallAfter(self.window.StopCrawler,None)
                logger.info(u"停止采集线程！")
            return None
        except Exception:
            s=sys.exc_info()
            logger.error(u"StartCrawlThread thread %s happened on line %d" % (s[1],s[2].tb_lineno))
            wx.CallAfter(self.window.WriteLogger, u"开启采集线程失败!case %s" % s[1])
    
    def stop(self):
        self.quitTime.set()
        
        
    def StartCrawler(self):
        print ".............StartCrawler."
        taskPath=self.window.taskPath
        crawlerType=self.window.CRAWLER_TYPE
        self.setCrawlerData(taskPath, 'gsid', 1, crawlerType) 
        #创建一个爬虫线程
        thread = Crawlerthread(self.threadNum, self.crawlerData, self.window)
        self.window.threads.append(thread)
        #启动线程
        thread.start()
            
    def setCrawlerData(self,taskPath=None,gsid=None,
                           threadNumber=10,crawlerType=0):
        crawlerData={}
        crawlerData["taskPath"]=taskPath
        crawlerData["resultPath"]=self.window.resultPath
        crawlerData["threadNum"]=threadNumber
        crawlerData["gsid"]=gsid
        crawlerData["crawlerType"]=crawlerType
        self.crawlerData=crawlerData
        self.threadNum=threadNumber
        logger.info(crawlerData)
            
            
            
            
            
            
            
            
            