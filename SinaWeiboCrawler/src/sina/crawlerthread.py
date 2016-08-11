# encoding:utf-8

'''
created on 2014-5-6
this is a cralerthread 
part of src come from the Pameng
'''


from Queue import Queue, Empty
import csv
import os
import sys
import threading
import time

import wx

from crawlermodel import logfile
from crawlermodel import settings as modelSettings
from crawlermodel.getloginuserinfo import GetLoginUser
from fetcherData import FetcherData
from sina import settings
from sina.fetcherWeibo import GetWeiboInfo
import threadpool


logger=logfile.LogFile().getLogger('run')
class Crawlerthread(threading.Thread):
    print "--------------Crawlerthread"
    def __init__(self,threadNum,crawlerData,window):
        self.threadNum=threadNum
        self.crawlerData=crawlerData
        self.window=window
        threading.Thread.__init__(self)
        self.quitTime=threading.Event()
        self.quitTime.clear()
        #线程数默认为1
        self.pool=threadpool.WorkerPool(self.threadNum)
        self.count=1
        
    def stop(self):
        self.quitTime.set()
        
    #运行一个线程
    def run(self):
        print "----------crawler run"
        self.window.CRAWLER_STATUS=1#更新系统为采集状态
        crawlerData=self.crawlerData
        outputPath=crawlerData["resultPath"]
        try:
            now=time.time()
            crawlerType=crawlerData.get("crawlerType")
            print crawlerType
            if crawlerType==1 or crawlerType==0:#搜索用户采集或者批量采集
                taskInfo={}
                uids=[]#列表
                if self.window.CRAWLER_SELF:
                    self.window.CRAWLER_SELF=0
                    userSearch=GetLoginUser("",modelSettings.LOGINWEB)
                    loginUser=userSearch.GetLoginUserInfo()
                    if loginUser:
                        wx.CallAfter(self.window.WriteLogger,u"已选定采集用户：%s" % loginUser.get("nickname"))
                        uids.append(loginUser["uid"])
                    else:
                        uids=[]
                        msg=u"获取当前用户信息失败：%s" % loginUser
                        wx.CallAfter(self.window.WriteLogger,msg)
                        logger.error(msg)
                        return None
                #若有其他用户一起添加到采集任务
                if modelSettings.SEARCHUID.get("CRAWLERUID", None):
                    uids.extend(modelSettings.SEARCHUID.get("CRAWLERUID"))
                taskInfo["gsid"]=[crawlerData["gsid"]]
                logger.info("threadPool size:%d" % self.threadNum)
                    
                msg1=u"需要执行的任务数：%d" %len(uids)
                msg2=u"请稍等，正在创建线程-------"
                wx.CallAfter(self.window.WriteLogger,msg1)
                wx.CallAfter(self.window.WriteLogger,msg2)
                logger.info(u"创建线程 SIZE %d"%len(uids))
                    
                queue = Queue(0)#队列
                #采集所有指定的用户信息
                for i in range(len(uids)):
                    try:
                #任务排队加载到队列中开始采集
                        if uids[i].strip():
                            job=FetcherData(queue,uids[i],taskInfo,i,
                                            self.window,self.threadNum,
                                            outputPath,proxylist=[])
                            self.pool.put(job)
                    except:
                            s=sys.exc_info()
                            msg = (u"crawlerthread jobThread ERROR %s happened on line %d" % (s[1],s[2].tb_lineno))
                            logger.error(msg)
                self.pool.wait()
                #爬取的所有结果   
                resultList=[]   
                try:
                    for i in range(queue.qsize()):
                        resultList.append(queue.get(block=False))
                except Empty:
                    pass#结果加载完成
                
                #分别提取出对应结果包含user和msg
                userList=[]
                for result in resultList:
                    userList.append(result.get("user"))# append() 方法向列表的尾部添加任意，甚至是tuple类型的一个新的元素。
    #                 msgList.extend(result.get("msg"))#extend() 方法只接受一个列表作为参数，并将该参数的每个元素都添加到原有的列表中。
                #输出用户信息
                t = time.strftime( '%Y-%m-%d-%H-%M', time.localtime(time.time()))
                self.OutputUserData2Csv(outputPath, str(t), userList)
                
            if crawlerType==2: #采集指定微博
                weiboUrl=modelSettings.WeiboUrl
                msg=u"请稍等，正在创建线程-------"
                wx.CallAfter(self.window.WriteLogger,msg)
                if settings.CrawlerContent["cwlComment"]:
                    CommentJob=GetWeiboInfo(window=self.window,weiboUrl=weiboUrl,c_type='comment')
                    CommentJob.run()
                    commentList=CommentJob.usersinfo
                    weiboinfo=CommentJob.msg
                    mid=weiboinfo.get('msgid')
                    t = time.strftime( '%Y-%m-%d-%H-%M', time.localtime( time.time() ))
                    self.OutputComUserData2Csv(outputPath, t+"-"+str(mid.decode("utf8")),commentList,weiboinfo)
                if settings.CrawlerContent["cwlForward"]:
                    RepostJob=GetWeiboInfo(window=self.window,weiboUrl=weiboUrl,c_type='repost')
                    RepostJob.run()
                    repostList=RepostJob.usersinfo
                    weiboinfo=RepostJob.msg
                    mid=weiboinfo.get('msgid')
                    #保存输出采集指定微博的评论和转发信息
                    t = time.strftime( '%Y-%m-%d-%H-%M', time.localtime( time.time() ))
                    self.OutputRepUserData2Csv(outputPath, t+"-"+str(mid.decode("utf8")),repostList,weiboinfo)
                
            #------------采集进程结束    
            msg="=========================="
            wx.CallAfter(self.window.WriteLogger,msg)
            costTime=time.time()-now
            logger.info("当前回复 %d/总回复 %d" %
                        (self.window.curCount,self.window.totalCount))
            msg=u'总耗时：%d s 发送请求：%d '% (int(costTime),int(self.window.totalCount))
            logger.info(msg)
            wx.CallAfter(self.window.WriteLogger,msg)
            #本次采集结束
            self.window.CRAWLER_STATUS = 0
#             wx.CallAfter(self.window.UpdateProcessBar, 
#                          int(self.window.totalCount)*2+27)
            wx.CallAfter(self.window.UpdateProcessBar, int(self.window.totalCount)*2+27)#进度条完全显示
            wx.CallAfter(self.window.ThreadFinished, self)
            msg=u"本次采集完成!线程结束"
            logger.info(msg)
            wx.CallAfter(self.window.WriteLogger,msg)
            
        except :
            s=sys.exc_info()
            msg = (u"crawlerthread jobThread ERROR %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
#             wx.CallAfter(self.window.ThreadFinished, self)
#             wx.CallAfter(self.window.WriteLogger, u'采集出错: %s'+str(e))
#             logger.error(u"采集Exception: %s" % str(e))
                
        finally:
            wx.CallAfter(self.window.UpdateBtnLabel,u"开始采集")
            wx.CallAfter(self.window.UpdateButStatus, False)
#             wx.CallAfter(self.window.UpdateProcessBar, int(self.window.totalCount)*2+27)
            modelSettings.SEARCHUID["CRAWLERUID"] = None  
            modelSettings.WeiboUrl=None    
                    
    def OutputUserData2Csv(self,outPath,fileName,userList): 
        try:
            writer=csv.writer(file(os.path.join(outPath,fileName+".user.csv"),'a+b')) 
            header=['用户ID','用户名','昵称','性别',
                    '头像地址','达人(1是0否)','认证(1是0否)','认证信息','会员',
                    '所在地','关注数','粉丝数','微博数','个人说明','注册时间',
                    '生日','Email','QQ','MSN','学校','公司','标签']      
            writer.writerow(header)
            for user in userList:
                writer.writerow([user.get('uid',''),
                                 user.get('uname',''),
                                 user.get('nickname',''),
                                 user.get('sex',''),
                                 user.get('Imgurl',''),
                                 user.get('daren',''),
                                 user.get('verified',''),
                                 user.get('verifInfo',''),
                                 user.get('vip',''),
                                 user.get('locat',''),
                                 user.get('n_follows',''),
                                 user.get('n_fans',''),
                                 user.get('n_weibos',''),
                                 user.get('intro',''),
                                 user.get('creatTime',''),
                                 user.get('birth',''),
                                 user.get('email',''),                            
                                 user.get('QQ',''),
                                 user.get('MSN',''),
                                 user.get('school',''),
                                 user.get('company',''),
                                 user.get('tags',''),                         
                                 ])
            logger.info(u"写入用户信息到文件成功")
        except Exception:
            s=sys.exc_info()
            msg = (u"write csv Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg) 
     
    
    def OutputComUserData2Csv(self,outPath,fileName,commentList,weiboinfo): 
        try:
            writer=csv.writer(file(os.path.join(outPath,fileName+".comment.csv"),'a+b')) 
            header=['微博ID','博主ID','评论信息ID','评论用户ID',
                    '评论用户名','评论用户昵称','评论用户头像',
                    '达人(1是0否)','认证(1是0否)','会员',                   
                    '评论内容','评论时间','此微博是否转发','原用户ID','原微博ID']      
            writer.writerow(header)
            for user in commentList:
                writer.writerow([user.get('msgid',''),
                                 user.get('ouid',''),
                                 user.get('mid',''),
                                 user.get('uid',''),
                                 user.get('uname',''),
                                 user.get('nickname',''),
                                 user.get('Imgurl',''),
                                 user.get('daren',''),
                                 user.get('verify',''),
                                 user.get('vip',''),
                                 user.get('msg',''),
                                 user.get('date',''),
                                 weiboinfo.get('isforward',0),
                                 weiboinfo.get('rouid',''),
                                 weiboinfo.get('omid',''),
                                 ])
            logger.info(u"写入评论用户信息到文件成功")
        except Exception:
            s=sys.exc_info()
            msg = (u"write ComUser csv Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)   

    
    def OutputRepUserData2Csv(self,outPath,fileName,repostList,weiboinfo): 
        try:
            writer=csv.writer(file(os.path.join(outPath,fileName+".repost.csv"),'a+b')) 
            header=['微博ID','博主ID','转发信息ID','转发用户ID',
                    '转发用户名','转发用户昵称','转发用户头像',
                    '达人(1是0否)','认证(1是0否)','会员',                   
                    '转发内容','转发消息地址','转发时间','此微博是否转发','原用户ID','原微博ID']      
            writer.writerow(header)
            for user in repostList:
                writer.writerow([user.get('msgid',''),
                                 user.get('ouid',''),
                                 user.get('mid',''),
                                 user.get('uid',''),
                                 user.get('uname',''),
                                 user.get('nickname',''),
                                 user.get('Imgurl',''),
                                 user.get('daren',''),
                                 user.get('verify',''),
                                 user.get('vip',''),
                                 user.get('msg',''),
                                 user.get('msgurl',''),
                                 user.get('date',''),
                                 weiboinfo.get('isforward',0),
                                 weiboinfo.get('rouid',''),
                                 weiboinfo.get('omid',''),
                                 ])
            logger.info(u"写入转发用户信息到文件成功")
        except Exception:
            s=sys.exc_info()
            msg = (u"write RepUser csv Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            
            
            
        
                
          
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        