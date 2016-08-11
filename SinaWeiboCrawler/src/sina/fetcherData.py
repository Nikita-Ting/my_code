# encoding:utf-8

'''
created on 2014-5-6
this is a master to control the thread of crawler
include :user (fans and follows),weibo(weibos of uers,comment,forward of one item)
and in this part,the weibos of each user will be output
and users information will be collected together then output in crawlerThread
part of src come from the Pameng
'''

from Queue import Empty, Queue
import csv
import json#?import simplejson 有什么区别？
import os
import sys
import time

import wx

from crawlermodel import logfile
from fetcherUser import FetcherUser
from sina import settings
from sina.fetcherUser import FetcherUserFollows, FetcherUserFans
from sina.loginsinaweb import LoginSinaWeb
import threadpool


logger=logfile.LogFile().getLogger('run')

class FetcherData(threadpool.Job):
    #集合所有爬取的数据
    def __init__(self, result_queue, uid, task_info, threadID, window, threadNum, output_path, proxylist=[]):
        self.result_queue = result_queue
        self.uid = uid
        self.proxylist = proxylist
        self.gsid = task_info.get("gsid")[0]
        self.threadId = threadID
        self.window = window
        self.threadNum = threadNum
        self.outputPath = output_path
        
        self.userinfo = {}
        self.msginfo = []
        #result：采集返回的数据
        #包含：用户信息和用户首页基本信息
        self.result = {}
  
  
    def run(self):
        print "-------------fetcherData"
        #爬虫程序没有被停止时，继续采集下一个用户
        while self.window.crawlerRunning:
            userId=self.uid
            proxyip = self.GetProxyIp()
            try:
                #开始采集该用户的时间
                nowTime = str(time.time()).replace(".", "")
                gsid = self.gsid
                userIndexUrl = "http://m.weibo.cn/home/homeData?hideAvanta=1&u=%s&page=1&&_=%s" % (userId, nowTime)
                userInfoUrl = "http://m.weibo.cn/setting/userInfoSetting?uid=%s&st=569d&" % (userId)
                #采集指定用户信息
                status=self.GetUserInfo(userIndexUrl,userInfoUrl,userId, gsid, proxyip)
                if status:
                    #如果用户信息采集成功，并选择采集关注列表
                    if settings.CrawlerContent["cwlFollows"]:
                        self.GetUserFollows()
                    if settings.CrawlerContent["cwlFans"]:
                        self.GetUserFans()

                self.window.curCount += 2
                self.window.finishedCount += 1
            except Exception:
                self.userinfo['fg'] = 13;
#                 self.result["user"] = self.userinfo
#                 self.result_queue.put(self.result)
                s=sys.exc_info()
                msg = (u"fetcher user data Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                logger.error(msg)
            finally:
                wx.CallAfter(self.window.UpdateProcessBar, self.window.finishedCount)
                logger.info(u"采集用户完成")
                break
                
    def GetUserInfo(self,userIndexUrl,userInfoUrl,userId,gsid,proxyip):
        try:
            now = time.time()
            #创建一个用户采集的控制器
            fetcherUser=FetcherUser(self.window,self.threadNum,self.outputPath)
            #采集用户基本信息的页面
            content =fetcherUser.GetHtmlData(userIndexUrl, userId, gsid, "http://m.weibo.cn/u/%s?" % userId, proxyip)
            if content == "":
                msg = u"用户： %s 采集失败(返回用户信息为空！)" % userId
                logger.error(msg)
                wx.CallAfter(self.window.WriteLogger, msg)
                    # print content.decode('gbk').encode('utf-8')
            if not fetcherUser.GetUserBasicData(content):
                wx.CallAfter(self.window.WriteLogger, u"===================")
                msg = u"无效的用户ID：%s." % (userId)
                wx.CallAfter(self.window.WriteLogger, msg)
                self.userinfo['fg'] = 4;
                self.result["user"] = self.userinfo
                    #采集用户详细信息页面
    #                 content =fetcherUser.GetHtmlData(userInfoUrl, userId, gsid, "http://m.weibo.cn/users/%s?" % userId, proxyip)
    #                 print content  
    #                 infoStatus = fetcherUser.GetUserDetailData(content)
    #                 print infoStatus 
    #                 if infoStatus=='success':
    #                     logger.info(u"获取用户详细信息成功")
    #                 else:
    #                     #只采集到了用户的基本信息
    #                     logger.info(infoStatus)
            self.userinfo=fetcherUser.userinfo 
            self.userinfo['uid'] = userId.encode('utf-8')
            self.result["user"] = self.userinfo
            self.result_queue.put(self.result)

            #若用户选择爬取微博信息
            if settings.CrawlerContent["cwlWeibos"]:        
                #将采集到的该用户的所有微博信息单独写到一个文件中
                self.msginfo = fetcherUser.msginfo
                t = time.strftime( '%Y-%m-%d-%H-%M', time.localtime( time.time() ))
                self.msginfo.sort(key=lambda obj:obj.get('publtime'))
                OutPutMsgList2Csv(self.outputPath, t+"-"+str(self.userinfo.get("nickname", "").decode("utf8")), self.msginfo)
                         
                #每采集一个用户的微博都记录耗时
                costTime = time.time() - now
                msg = u'耗时 : %ds ;采集用户：%s , 微博数(原创+转发): %d' % (int(costTime), self.userinfo['nickname'], len(self.msginfo))
                logger.info(msg)
                wx.CallAfter(self.window.WriteLogger, msg)
        except Exception:
            self.userinfo['fg'] = 13;
            self.result["user"] = self.userinfo
#                 self.result["msg"] = self.msginfo
            self.result_queue.put(self.result)
            s=sys.exc_info()
            msg = (u"get user data Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return False
        return True
            
    def GetProxyIp(self):
        if len(self.proxylist)>=1:
            ip = self.proxylist[0]
            self.proxylist.remove(ip)
            self.proxylist.append(ip)
        else:
            return ""
        return ip        
                
    def GetUserFollows(self):
        print "GetUserFollows"
        #获取用户关注页数，由于新浪限制，只能查看用户200个关注信息，所以页面最大限制是10页
        try:
            maxPage = int((int(self.userinfo['n_follows'])-1)/20)+1
            if maxPage> 10:
                maxPage=10
            if maxPage >= 1:
                wx.CallAfter(self.window.SetProcessBarRange, (maxPage*1+self.window.processBarValue))
                self.window.totalCount += (maxPage)
                #爬取该用户的所有关注用户信息
                pool = threadpool.WorkerPool(self.threadNum)
                q = Queue(0)
                for i in range(1, maxPage+1):
                    try:
                        #开启翻页采集线程
                        job = FetcherUserFollows(result_queue=q,thread_id=i,user=self.userinfo,
                                         max_page=maxPage,window=self.window)
                        pool.put(job)
                    except:
                        s=sys.exc_info()
                        msg = (u"jobThread ERROR %s happened on line %d" % (s[1],s[2].tb_lineno))
                        logger.error(msg)
    #             pool.shutdown()
                pool.wait()#等待所有工作结束
                FollowList=[]
                try:
                    for i in range(q.qsize()):
                        FollowList.extend(q.get(block=False))
                except Empty:
                    pass # Success
                
                #输出用户关注信息
                t = time.strftime( '%Y-%m-%d-%H-%M', time.localtime( time.time() ))
                OutPutFollowsList2Csv(self.outputPath, t+"-"+str(self.userinfo.get("nickname", "").decode("utf8")), FollowList)
                msg = u'采集用户：%s ,  %d关注用户' % (self.userinfo['nickname'], len(FollowList))
                logger.info(msg)
                wx.CallAfter(self.window.WriteLogger, msg)         
        except:
            s=sys.exc_info()
            msg = (u"fetcher GetUserFollows Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
         
    def GetUserFans(self):
        #获取用户关注页数，由于新浪限制，只能查看用户200个粉丝信息，所以页面最大限制是10页
        try:
            maxPage = int((int(self.userinfo['n_fans'])-1)/20)+1
            if maxPage> 10:
                maxPage=10
            if maxPage >= 1:
                wx.CallAfter(self.window.SetProcessBarRange, (maxPage*1+self.window.processBarValue))
                self.window.totalCount += (maxPage)
                #爬取该用户的所有关注用户信息
                pool = threadpool.WorkerPool(self.threadNum)
                q = Queue(0)
                for i in range(1, maxPage+1):
                    try:
                        #开启翻页采集线程
                        job = FetcherUserFans(result_queue=q,thread_id=i,user=self.userinfo,
                                         max_page=maxPage,window=self.window)
                        pool.put(job)
                    except:
                        s=sys.exc_info()
                        msg = (u"fans jobThread ERROR %s happened on line %d" % (s[1],s[2].tb_lineno))
                        logger.error(msg)
    #             pool.shutdown()
                pool.wait()#等待所有工作结束
                FansList=[]
                try:
                    for i in range(q.qsize()):
                        FansList.extend(q.get(block=False))
                except Empty:
                    pass # Success
                
                #输出用户关注信息
                t = time.strftime( '%Y-%m-%d-%H-%M', time.localtime( time.time() ))
                OutPutFansList2Csv(self.outputPath, t+"-"+str(self.userinfo.get("nickname", "").decode("utf8")), FansList)
                msg = u'采集用户：%s ,  %d粉丝用户' % (self.userinfo['nickname'], len(FansList))
                logger.info(msg)
                wx.CallAfter(self.window.WriteLogger, msg)         
        except:
            s=sys.exc_info()
            msg = (u"fetcher GetUserFans Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
   
            
 #输出单个用户的微博信息               
def OutPutMsgList2Csv(outPath,fileName,msgList):   
    try:
        writer=csv.writer(file(os.path.join(outPath,fileName+".msg.csv"),'a+b'))
        header=['消息ID','用户ID','用户名','屏幕名','转发消息ID',\
                             '消息内容','消息URL','来源','图片URL','音频URL','视频URL',\
                             '转发数','评论数','发布时间','@用户']    
        writer.writerow(header)
        for r in msgList:
                writer.writerow([r.get('msg_id'), 
                                 r.get('uid'), 
                                 r.get('uname', ""), 
                                 r.get('nickname', ""), 
#                                  r.get('Imgurl', ""), #用户头像，暂时不用
                                 r.get('forwId', ""), 
                                 r.get('msg'), 
                                 r.get('msgurl'), 
                                 r.get('msgfrom'), 
                                 r.get('picUrl'), 
                                 r.get('audioUrl'), 
                                 r.get('vedioUrl'), 
                                 r.get('n_forward'), 
                                 r.get('n_comment'), 
                                 r.get('publtime'), 
                                 r.get('aiteUser'), 
                                 ])      
                
    
    except Exception:
            s=sys.exc_info()
            msg = (u"OutPutMsgList2Csv Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)             
                
def OutPutFollowsList2Csv(outPath,fileName,followList):
    try:
        writer=csv.writer(file(os.path.join(outPath,fileName+".follows.csv"),'a+b'))
        header=['博主ID','关注用户ID','用户名','屏幕名','性别',\
                             '头像地址','达人','新浪认证','会员','所在地','关注数','粉丝数',\
                             '微博数','简介','最新微博','来自设备']    
        writer.writerow(header)
        print len(followList)
        for r in followList:
            writer.writerow([r.get('userid'), 
                            r.get('uid'), 
                            r.get('uname', ""), 
                            r.get('nickname', ""), 
                            r.get('sex', ""), 
                            r.get('Imgurl'), 
                            r.get('daren'), 
                            r.get('verify'), 
                            r.get('vip'), 
                            r.get('addr'), 
                            r.get('n_follows'), 
                            r.get('n_fans'), 
                            r.get('n_weibos'), 
                            r.get('intro'), 
                            r.get('latestweibo'), 
                            r.get('p_from'),
                            ])      
    
    except Exception:
        s=sys.exc_info()
        msg = (u"OutPutFollowsList2Csv Error %s happened on line %d" % (s[1],s[2].tb_lineno))
        logger.error(msg)                 
                
def OutPutFansList2Csv(outPath,fileName,fansList):
    try:
        fp = file(os.path.join(outPath,fileName+".fans.csv"),'a+b')
        writer=csv.writer(fp)
        header=['博主ID','粉丝ID','用户名','屏幕名','性别',\
                             '头像地址','达人','新浪认证','会员','所在地','关注数','粉丝数',\
                             '微博数','简介','最新微博','来自设备']    
        writer.writerow(header)
        print len(fansList)
        for r in fansList:
            print r
            writer.writerow([r.get('userid'), 
                            r.get('uid'), 
                            r.get('uname', ""), 
                            r.get('nickname', ""), 
                            r.get('sex', ""), 
                            r.get('Imgurl'), 
                            r.get('daren'), 
                            r.get('verify'), 
                            r.get('vip'), 
                            r.get('addr'), 
                            r.get('n_follows'), 
                            r.get('n_fans'), 
                            r.get('n_weibos'), 
                            r.get('intro'), 
                            r.get('latestweibo'), 
                            r.get('p_from'),
                            ])   
                
    except Exception:
        s=sys.exc_info()
        msg = (u"OutPutFansList2Csv Error %s happened on line %d" % (s[1],s[2].tb_lineno))
        logger.error(msg)
    finally:
        fp.close()           

if __name__== '__main__':
    taskInfo={}
    taskInfo["gsid"]=['gsid']
    gsid=taskInfo.get("gsid")[0]
    user={}
    user["uid"]=[1970889791]
#     fetcger=FetcherData("",1970889791,taskInfo,1,
#                                 "",1,
#                                 "C:\Python27\file",proxylist=[])
#     fetcger.GetUserFollows()
    login = LoginSinaWeb()
    login.checkCookie(uname='XXXXX',pasword='XXXXXXXXX')
    job1=FetcherUserFollows(thread_id=1,user=user)
    job1.run()
            
                
                
    
    
        

    