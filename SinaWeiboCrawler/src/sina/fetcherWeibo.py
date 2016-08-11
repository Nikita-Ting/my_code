# encoding:utf-8

'''
created on 2014-5-6
this is a master to control the thread of crawler user
include :weibo(weibos of uers,comment,forward of one item)
part of src come from the Pameng
'''

from __future__ import division

from Queue import Queue, Empty
import datetime
import json
import random
import re
import sys
import time

from lxml.html import tostring
from lxml.html.soupparser import fromstring
import wx
from crawlermodel import settings as modelsettings
from crawlermodel import logfile
import settings
from sina import loginsinaweb
import threadpool
from weibourl2ID import midToStr, sinaWburl2ID
from loginsinaweb import *


# from sina.fetcherUser import FetcherUser
logger=logfile.LogFile().getLogger('run')
 
def getMillitime():
    pre = str(int(time.time()))
    pos = str(datetime.datetime.now().microsecond)[:3]
    return pre + pos
 
 #采集指定用户的新浪微博，网页版，调用采集工作类，解析首页
class FetcherWeibos(threadpool.Job):
     
    def __init__(self,**kwargs):
        #print kwargs
        self.result_queue = kwargs.get("result_queue", "")
        self.thread_id = kwargs.get("thread_id", "")
        self.window = kwargs.get("window", "")
        self.thread_num = kwargs.get("thread_num", "")
        self.output_path = kwargs.get("output_path", "")
        self.user = kwargs.get("user", {})
        self.max_page = kwargs.get("max_page", 1)
#         self.sina = kwargs.get("loginweb", 1)
        self.sina = loginsinaweb.LoginSinaWeb()
        
        #用户消息列表
        self.msgLst = []
        self.xpathconfig = XpathConfig()
        self.xpathType = ""
        
    def run(self):
        try:
            self.parsePagelist(self.max_page)
        except:
            s=sys.exc_info()
            msg = (u"FetcherWeibos thread Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
        finally:
            self.result_queue.put(self.msgLst)
            logger.info(u"add the msgList in to the queue")
            wx.CallAfter(self.window.UpdateProcessBar, self.window.finishedCount)
    
    #解析更多页
    #需要先抽取用户首页最新微博id作为end_id
    #首页需要刷新三次才能显示完全
    def parsePagelist(self, maxPage):
        print "--------parsePagelist"
        
        msg = u"正在采集用户:%s  第  %s 页 / 共 %s 页 微博." % (self.user.get("nickname"), 1, maxPage)
        wx.CallAfter(self.window.WriteLogger, msg)
        wx.CallAfter(self.window.UpdateProcessBar, 2)
        try:
            #抽取第一页微博
            #每页循环lazy load MAX:[0,1,2]3次,每页需要刷新三次才能显示完该页所有微博
            url = ""
            userid = self.user.get("uid", "")
            max_id = ""
            end_id = ""
            html = ""
            eachpageCount = 0
            hasMore = 1
            while hasMore and eachpageCount <= 2:
                rnd = getMillitime()
                k_rnd = random.randint(10, 60)
                page = 1
                if eachpageCount == 0:
                    url = "http://weibo.com/aj/mblog/mbloglist?_wv=5&page=%s&count=50&pre_page=%s&end_id=%s&_k=%s&_t=0&end_msign=-1&uid=%s&__rnd=%s" % (page, (page-1), end_id, rnd+str(k_rnd), userid, rnd)
                else:
                    #url 中 _k 为 时间戳（毫秒计）
                    url = "http://weibo.com/aj/mblog/mbloglist?_wv=5&page=%s&count=15&pre_page=%s&end_id=%s&_k=%s&_t=0&max_id=%s&pagebar=%s&uid=%s&__rnd=%s" % (page, (page), end_id, rnd+str(k_rnd+1), max_id, eachpageCount-1, userid,  getMillitime())
                if not html:
#                     html= self.getAjaxmsg(url, "http://weibo.com/u/%s" % userid)
                    html= self.getHtmlFromJson(html)
                hasMore,feedmsgLst,max_id = self.parseFeedlist(html)
                if eachpageCount == 0:
                    end_id = feedmsgLst[0].get("mid", "0")
                #存入消息列表返回
                self.msgLst.extend(feedmsgLst)
                eachpageCount += 1
                html = ""
            
            self.window.totalCount += maxPage*3
            wx.CallAfter(self.window.SetProcessBarRange, (maxPage*1+self.window.processBarValue))
            pool = threadpool.WorkerPool( self.thread_num )
            q = Queue(0)
            for i in range(2, maxPage+1):
                try:
                    #开启翻页采集线程
                    job = UsermsgJob(result_queue=q,thread_id=i,user=self.user,end_id=end_id,
                                     max_page=maxPage, msg_crawler=self,window=self.window)
                    pool.put(job)
                except:
                    s=sys.exc_info()
                    msg = (u"jobThread ERROR %s happened on line %d" % (s[1],s[2].tb_lineno))
                    logger.error(msg)
#             pool.shutdown()
            pool.wait()#等待所有工作结束
            try:
                for i in range(q.qsize()):
                    self.msgLst.extend(q.get(block=False))
            except Empty:
                pass # Success
            logger.info(u"add msglst to usermsgjob queue success")
        except:
            s=sys.exc_info()
            msg = (u"parsePagelist Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
    
    #解析用户消息列表
    def parseFeedlist(self, html):
        feedDoc = fromstring(html)#解析页面
        self.config = self.xpathconfig.getIndexConfig('v1')#获取元素标签
        nodeLst = feedDoc.xpath(self.config.get("USER_FEEDLIST_XPATH"))
        moreNode = feedDoc.xpath(self.config.get("MORE_FEEDLIST_XPATH"))
        feedmsgLst = []
        hasMore = 0
        max_id = ""
        for node in nodeLst:
            try:
                msg,rtmsg = self.parseFeed(node)
                if msg:
                    max_id = msg.get("mid")
                    feedmsgLst.append(msg)
                if rtmsg:
                    feedmsgLst.append(rtmsg)
            except:
                #s=sys.exc_info()
                #msg = (u"parseFeedlist Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                #logger.error(msg)
                continue
        if moreNode:
            #需要解析更多
            hasMore = 1
        return hasMore,feedmsgLst,max_id
    
    def getHtmlFromJson(self, html):     
        return json.loads(html).get("data")
        # json.dumps()方法返回了一个str对象encodedjson，得到原始数据，需要使用的json.loads()函数
    
    #解析消息
    def parseFeed(self, node):
        rtmsg = dict.fromkeys(settings.WEIBO_KEY, '')#转发微博初始化，赋空值
        msg = dict.fromkeys(settings.WEIBO_KEY, '')
#         rtmsg = {}#转发微博
#         msg = {}
        try:
            #消息id
            mid = node.get("mid", "")
            if mid:
                try:
                    node = fromstring(tostring(node).decode('unicode-escape'))
                except:
                    node = fromstring(tostring(node))
                msg = self.parseCommon(node, "msg")
                if msg:
                    #转发微博
                    rtmsgNode = node.xpath(self.config.get("MSG_RETWEET_XPATH"))
                    if rtmsgNode:
                        try:
                            rtmsg = self.parseRefeed(rtmsgNode[0])
                            #转发id
                            msg['forwId'] = rtmsg.get("mid", "")
                        except:
                            #s=sys.exc_info()
                            #msg = (u"rtmsgNode Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                            #logger.error(msg)
                            pass
                    #消息ID
                    msg['msg_id'] = mid
                    msg['msgurl'] = midToStr(mid)
                    msg['uname'] = self.user.get("uname", "")
                    msg['uid'] = self.user.get("uid", "")
                    msg['nickname'] = self.user.get("nickname", "")
#                     msg['Imgurl'] = self.user.get("Imgurl", "")#用户头像
                    # print '解析微博成功：', msg[COLUMN_MSGCONTENT]
        except:
            s=sys.exc_info()
            errmsg = (u"rtmsgNode Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(errmsg)
            msg = {}
        #self.msgLst.append(msg)
        return msg,rtmsg
    
    #解析转发消息
   
    def parseRefeed(self, node):
        node = fromstring(tostring(node))
        #ui
        userNode = node.xpath(self.config.get("RT_USER_XPATH"))
        if userNode:
            userNode = userNode[0]
            ui = userNode.get("usercard", "").replace("id=", "")
            sn = userNode.get("nick-name", " ")
            un = userNode.get("href", "").replace("/", "")
        else:
            return {}
        rtmsg = self.parseCommon(node, "rtmsg")
        if rtmsg:
            rtmsg['uid'] = ui
            rtmsg['uname'] = un
            rtmsg['nickname'] = sn
            #转发消息URL
            muNode = node.xpath("//div/div/div/div[@class='WB_from']/a[@title]")
            mu = ""
            mid = ""
            if muNode:
                mu = muNode[0].get("href", "").split("/")[-1]
                mid = sinaWburl2ID(mu)
            rtmsg['msg_id'] = mid
            rtmsg['msgurl'] = mu#微博消息url
        return rtmsg
        
    def parseCommon(self, node , type="msg"): #@ReservedAssignment
        try:
            config = self.xpathconfig.getMsgConfig_V1(type)
            #发布时间
            ptNode = node.xpath(config.get("MSG_TIME_XPATH"))
            pt = ""
            if ptNode:
                pt = ptNode[0].get("title")
                pt = self.parsePubtime(pt)
            else:
                return {}
            #消息文本
            mt = node.xpath(config.get("MSG_TEXT_XPATH"))[0].text_content()
            #@提及用户
            nc = []
            for ncNode in node.xpath(config.get("MSG_NAMECARD_XPATH")):
                nc.append(ncNode.text_content())
            nc = ",".join(nc)
            #来自
            srn = "新浪微博"
            srnNode = node.xpath(config.get("MSG_FROM_XPATH"))
            if srnNode:
                srn = srnNode[0].text_content()
            #评论 转发
            fromStr = node.xpath(config.get("MSG_BASE_XPATH"))[0].text_content()
            rc = 0
            cc = 0
            rcNode = re.findall("转发\((.\d*)\)", str(fromStr))
            if rcNode:
                rc = int(rcNode[0])
            rcNode = re.findall("评论\((.\d*)\)", str(fromStr))
            if rcNode:
                cc = int(rcNode[0])
            #图片和视频/音频
            mediaNode = node.xpath(config.get("MSG_PIC_XPATH"))
            pu = ""
            if mediaNode:
                pu = mediaNode[0].get("src")
            mediaNode = node.xpath(config.get("MSG_VIDEO_XPATH"))
            vu = ""
            if mediaNode:
                vu = mediaNode[0].get("action-data")
            return self.initMsg(mt=mt, nc=nc, srn=srn, pt=pt, rc=rc, cc=cc, pu=pu, vu=vu)
        except Exception:
            s=sys.exc_info()
            msg = (u"parseCommon Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return {}
    
    def initMsg(self, **kwargs):
        try:
            msg = {}
            msg['msg_id'] = kwargs.get("mid", "")
            msg['uname'] = kwargs.get("un", "").strip().encode("utf-8")
            msg['uid'] = kwargs.get("ui", "")
            msg['nickname'] = kwargs.get("sn", "").strip().encode("utf-8")
#             msg['Imgurl'] = kwargs.get("iu", "")
            msg['msg'] = kwargs.get("mt", "").encode("utf-8")
            msg['msgurl'] = kwargs.get("mu", "")
            msg['msgfrom'] = kwargs.get("srn", "").strip().encode("utf-8")#消息来源
            msg['picUrl'] = kwargs.get("pu", "")#图片信息
            msg['audioUrl'] = kwargs.get("au", "")#音频信息
            msg['vedioUrl'] = kwargs.get("vu", "")#视频信息
            msg['n_forward'] = kwargs.get("rc", "")#转发数
            msg['n_comment'] = kwargs.get("cc", "")#评论数
            msg['publtime'] = kwargs.get("pt", "")#发布时间
            msg['aiteUser'] = kwargs.get("nc", "").strip().encode("utf-8")#@用户
            msg['forwId'] = kwargs.get("ri", "")#转发消息ID
        except Exception:
            s=sys.exc_info()
            msg = (u"initMsg Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
        return msg
    
    #转换时间为UNIX时间戳
    
    def parsePubtime(self, ptStr):
        try:
            pt = int(time.mktime(time.strptime(ptStr,'%Y-%m-%d %H:%M')))
        except:
            pt = int(time.time())
        return pt
    
    #获取用户首页HTML
    
    def getUserIndex(self, url):
        headers = {"Host":"weibo.com",
                   "User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1",
                   "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                   "Accept-Language":"zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
                   "Accept-Encoding":"gzip, deflate",
                   "Connection":"keep-alive",
                   }
        for i in range(3): #@UnusedVariable
            try:
                self.window.curCount += 1
                html = self.sina.GetContentHead(url, headers=headers)
            except:
                continue
            if html:
                break
        return html
    
    #获取AJAX加载消息HTML
    
    def getAjaxmsg(self, url, refUrl):
        headers = {"Host":"weibo.com",
                   "User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.146 Safari/537.36",
#                    "User-Agent":"Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1",
                   "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                   "Accept-Language":"zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.6",
                   "Accept-Encoding":"gzip, deflate，sdch",
                   "Connection":"keep-alive",
                   "Content-Type":"application/x-www-form-urlencoded",
                   "X-Requested-With":"XMLHttpRequest",
                   "Referer":refUrl,
                   }
        for i in range(3): #@UnusedVariable
            try:
                self.window.curCount += 1
                html = self.sina.GetContentHead(url, headers=headers)
            except:
                continue
            if html:
                break
        return html
        
    def getPanelInfo(self, doc, strXPath):
        try:
            npos = doc.text_content().find(strXPath)
            if npos == -1:
                return ""
            strContent = doc.text_content()[npos:-1]
            npos = strContent.find("})")
            if npos == -1:
                return ""
            strContent = strContent[0:npos+1]
            strContent = (strContent[strContent.find("\"html\":\"")+8:-4])
            if "v2" in self.xpathType:
                strContent = strContent.decode('unicode-escape')
            strContent = re.sub(r"(\\n)*(\\t)*(\\ /)*(\\)*", "", strContent)
            strContent = re.sub(r"\\/", "/", strContent)
            if strContent:
                strContent = strContent.replace("&lt;", "<").replace("&gt;", ">").replace("nbsp;", "")
            else:
                return ""
        except Exception:
            s=sys.exc_info()
            msg = (u"getPanelInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return ""
        return strContent




#用户消息采集job
#从第二页开始线程采集

class UsermsgJob(threadpool.Job):
    
    def __init__(self, **kwargs):
        self.result_queue = kwargs.get("result_queue", "")
        #thread id同时作为页数
        self.thread_id = kwargs.get("thread_id", "")
        self.user = kwargs.get("user", "")
        self.end_id = kwargs.get("end_id", "")
        self.msgcrawler = kwargs.get("msg_crawler", "")
        self.window = kwargs.get("window", "")
        self.max_page = kwargs.get("max_page", 1)
        #用户消息列表
        self.msgLst = []
        
    def run(self):
        while self.window.crawlerRunning :
            page = self.thread_id
            msg = u"正在采集用户:%s 第  %s 页 / 共 %s 页 微博." % (self.user.get("nickname"), page, self.max_page)
            #print msg
            wx.CallAfter(self.window.WriteLogger, msg)
            try:
                html = ""
                userid = self.user.get("uid")
                end_id = self.end_id
                eachpageCount = 0
                hasMore = 1
                max_id = ""
                crawler = self.msgcrawler
                #每页循环lazy load MAX:[0,1,2]3次
                while hasMore and eachpageCount <= 2:
                    rnd = getMillitime()
                    k_rnd = random.randint(10, 60)
                    if eachpageCount == 0:
                        url = "http://weibo.com/aj/mblog/mbloglist?_wv=5&page=%s&count=50&pre_page=%s&end_id=%s&_k=%s&_t=0&end_msign=-1&uid=%s&__rnd=%s" % (page, (page-1), end_id, rnd+str(k_rnd), userid, rnd)
                    else:
                        #url 中 _k 为 时间戳（毫米计）
                        url = "http://weibo.com/aj/mblog/mbloglist?_wv=5&page=%s&count=15&pre_page=%s&end_id=%s&_k=%s&_t=0&max_id=%s&pagebar=%s&uid=%s&__rnd=%s" % (page, (page), end_id, rnd+str(k_rnd+1), max_id, eachpageCount-1, userid, getMillitime())
                    html = crawler.getAjaxmsg(url, "http://weibo.com/u/%s" % userid)
                    html = crawler.getHtmlFromJson(html)
                    hasMore,feedmsgLst,max_id = crawler.parseFeedlist(html)
                    #存入消息列表返回
                    self.msgLst.extend(feedmsgLst)
                    eachpageCount += 1
                self.result_queue.put(self.msgLst)
                self.window.finishedCount += 1
            except:
                s=sys.exc_info()
                msg = (u"parsePagelist Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                logger.error(msg)
            finally:
                wx.CallAfter(self.window.UpdateProcessBar, self.window.finishedCount)
                logger.info(u"updateprocessBar success")
                break
            
class XpathConfig():
    
    def __init__(self):
        pass
    
    def getMsgConfig_V1(self, _type="msg"):
        #用户消息xpath配置
        __usermsgXpath = {"MSG_TEXT_XPATH":"//div[@class='WB_detail']/div[@class='WB_text']",
                        "MSG_NAMECARD_XPATH":"//div[@class='WB_detail']/div[@class='WB_text']/a[@usercard]",
                        "MSG_TIME_XPATH":"//div[@class='WB_detail']/div[@class='WB_func clearfix']/div[@class='WB_from']/a[@date]",
                        "MSG_FROM_XPATH":"//div[@class='WB_detail']/div[@class='WB_func clearfix']/div[@class='WB_from']/a[@target and not(@date)]",
                        "MSG_BASE_XPATH":"//div[@class='WB_detail']/div[@class='WB_func clearfix']/div[@class='WB_handle']",
                        "MSG_PIC_XPATH":"//div[@class='WB_detail']/ul/li[not(@action-type)]/div/img",
                        "MSG_VIDEO_XPATH":"//div[@class='WB_detail']/ul/li[@action-type]",
                        }
        #用户转发消息xpath配置
        __userrtmsgXpath = {"MSG_TEXT_XPATH":"//div/div[@class='WB_text']",
                          "MSG_NAMECARD_XPATH":"//div/div[@class='WB_text']/a[@usercard]",
                          "MSG_TIME_XPATH":"//div/div/div/div[@class='WB_from']/a[@date]",
                          "MSG_FROM_XPATH":"//div/div/div/div[@class='WB_from']/a[@target and not(@date)]",
                          "MSG_BASE_XPATH":"//div/div/div/div[@class='WB_handle']",
                          "MSG_PIC_XPATH":"//div/ul/li[not(@action-type)]/div/img",
                          "MSG_VIDEO_XPATH":"//div/ul/li[@action-type]",
                        }
        
        #供调用配置
        msgxpath = {"msg":__usermsgXpath, "rtmsg":__userrtmsgXpath}
        return msgxpath.get(_type, "")
    
    def getMsgConfig_V2(self, _type="msg"):
        #用户消息xpath配置
        __usermsgXpath = {"MSG_TEXT_XPATH":"//dl/dd[@class]/p[@node-type]",
                        "MSG_NAMECARD_XPATH":"//dl/dd/p[@node-type]/a[@usercard]",
                        "MSG_TIME_XPATH":"//dl/dd/p/a[@class='date']",
                        "MSG_FROM_XPATH":"//dl/dd/p/a[(@target) and not(@action-type)]",
                        "MSG_BASE_XPATH":"//dl/dd/p/span",
                        "MSG_PIC_XPATH":"//div[@class='WB_detail']/ul/li[not(@action-type)]/div/img",
                        "MSG_VIDEO_XPATH":"//div[@class='WB_detail']/ul/li[@action-type]",
                        }
        #用户转发消息xpath配置
        __userrtmsgXpath = {"MSG_TEXT_XPATH":"//div/div[@class='WB_text']",
                          "MSG_NAMECARD_XPATH":"//div/div[@class='WB_text']/a[@usercard]",
                          "MSG_TIME_XPATH":"//div/div/div/div[@class='WB_from']/a[@title]",
                          "MSG_FROM_XPATH":"//div/div/div/div[@class='WB_from']/a[@target]",
                          "MSG_BASE_XPATH":"//div/div/div/div[@class='WB_handle']",
                          "MSG_PIC_XPATH":"//div/ul/li[not(@action-type)]/div/img",
                          "MSG_VIDEO_XPATH":"//div/ul/li[@action-type]",
                        }
        
        #供调用配置
        msgxpath = {"msg":__usermsgXpath, "rtmsg":__userrtmsgXpath}
        return msgxpath.get(_type, "")
    
    def getIndexConfig(self, name="v1"):
        __newindexXpath = {"USER_PROFILE_BLOCK" : "{\"pid\":\"pl_profile_photo\"",
                           "MSG_COUNT_XPATH" : "//ul/li[3]/a/strong",
                           "USER_IMG_XPATH" : "//div/img",
                           "MSG_COUNT_XPATH_BV" : "//ul/li[3]/div/a[@id]",
                           "USER_IMG_XPATH_BV" : "//div[@id='profileHead']/div/div/a/img",
                           "USER_HISINFO_BLOCK" : "{\"pid\":\"pl_profile_hisInfo\"",
                           "USER_SCREENNAME_XPATH" : "//div/span[@class='name']",
                           "USER_USERNAME_XPATH" : "//div/div/div/a[@class]",
                           "USER_USERNAME_XPATH_BV" : "//div[@class='other_info']/p/a",
                           "USER_FEEDLIST_BLOCK" : "{\"pid\":\"pl_content_hisFeed\"",
                           "USER_FEEDLIST_XPATH" : "//div[(@mid) and (@action-type)]",
                           "MORE_FEEDLIST_XPATH" : "//div[@class='W_loading']",
                           "MSG_RETWEET_XPATH" : "//div[@class='WB_detail']/div[@node-type='feed_list_forwardContent']",
                           "RT_USER_XPATH" : "//div/div[@class='WB_info']/a[@usercard]",
                           }
        __trialindexXpath = {"USER_PROFILE_BLOCK" : "{\"pid\":\"pl_content_litePersonInfo\"",
                           "MSG_COUNT_XPATH" : "//ul/li[3]/a/strong",
                           "USER_IMG_XPATH" : "//div/div/div/a[@class='face']/img",
                           "MSG_COUNT_XPATH_BV" : "//div[@id='profileHead']/div/div/a/img",
                           "USER_IMG_XPATH_BV" : "//div[@id='profileHead']/div/div/a/img",
                           "USER_HISINFO_BLOCK" : "{\"pid\":\"pl_content_hisPersonalInfo\"",
                           "USER_SCREENNAME_XPATH" : "//div/span[@class='name']",
                           "USER_USERNAME_XPATH" : "//div[@class='perAll_info']/p/a[@class]",
                           "USER_USERNAME_XPATH_BV" : "//div[@class='other_info']/p/a",
                           "USER_FEEDLIST_BLOCK" : "{\"pid\":\"pl_content_hisFeed\"",
                           "USER_FEEDLIST_XPATH" : "//div[(@mid) and (@action-type)]",
                           #"USER_FEEDLIST_XPATH" : "//dl[(@mid) and (@action-type)]",
                           "MORE_FEEDLIST_XPATH" : "//div[@class='W_loading']",
                           #"MSG_RETWEET_XPATH" : "//dl/dt[@node-type='feed_list_forwardContent']",
                           "MSG_RETWEET_XPATH" : "//div[@class='WB_detail']/div[@node-type='feed_list_forwardContent']",
                           #"RT_USER_XPATH" : "//dl/dt/a[@usercard]",
                           "RT_USER_XPATH" : "//div/div[@class='WB_info']/a[@usercard]",
                           }
        
        
        xpathConfig = {"v1": __newindexXpath, "v2": __trialindexXpath}
        return xpathConfig.get(name, "")


#采集指定微博的评论或者转发
class GetWeiboInfo():
    
    def __init__(self,**kwargs):
        self.weiboUrl=kwargs.get("weiboUrl","")
#         self.loginweb=loginsinaweb.LoginSinaWeb()
        self.loginweb=modelsettings.LOGINWEB
        self.window=kwargs.get("window","")
        self.CrawlerType=kwargs.get("c_type","")
        self.usersinfo=[]
        self.msg={}
     
    def run(self):
        try:
#             if self.GetHtmlData():
            #单线程
#                 job=FetcherWeiboReorCom(weiboUrl=self.weiboUrl,
#                                                     msg=self.msg,c_type=self.CrawlerType,
#                                                     threadId=1)
#                 job.GetHtmlData()
#             self.usersinfo=job.usersInfo
            #多线程
            if self.GetHtmlData():
                maxPage=int(self.msg.get('totalpage'))
                print maxPage
                if maxPage >= 1:
                    wx.CallAfter(self.window.SetProcessBarRange, (maxPage*1+self.window.processBarValue))
                    self.window.totalCount += (maxPage)
                    pool = threadpool.WorkerPool(1)
                    q = Queue(0)
                    for i in range(1, maxPage+1):
                        try:
                            job=FetcherWeiboReorCom(result_queue=q,weiboUrl=self.weiboUrl,
                                                     msg=self.msg,c_type=self.CrawlerType,
                                                     threadId=i,window=self.window)
                            pool.put(job)
                        except:
                            s=sys.exc_info()
                            msg = (u"GetWeiboInfo jobThread ERROR %s happened on line %d" % (s[1],s[2].tb_lineno))
                            logger.error(msg)
                    pool.wait()#等待所有工作结束
                    try:
                        for i in range(q.qsize()):
                            self.usersinfo.extend(q.get(block=False))
                        print "all number of user"
                        print len(self.usersinfo)
                    except Empty:
                        pass # Success
            else:
                msg=u"页面数据获取失败！"
                logger.info(msg)
                wx.CallAfter(self.window.WriteLogger,msg)
                wx.CallAfter(self.window.UpdateProcessBar, int(self.window.totalCount)*2+27)#进度条完全显示
                wx.CallAfter(self.window.ThreadFinished, self)
                wx.CallAfter(self.window.UpdateButStatus, False)
                    
        except:
            s=sys.exc_info()
            msg = (u"GetWeiboInfo run Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            
    def GetHtmlData(self):
        #输入的微博地址形如：http://weibo.com/1400788390/B49Gxqgp4?type=repost/comment
        weiboUrl=self.weiboUrl
        if not weiboUrl.startswith("http://"):
            weiboUrl = "http://" + weiboUrl
        url=(weiboUrl+"?type=%s" % self.CrawlerType)
        try:
            #用户搜索页面信息
            #浏览器确认自己身份是通过User-Agent头
            headers = {'Host':'weibo.com',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Accept-Encoding':'gzip, deflate',
                       'Connection':'keep-alive',
                       'Referer':weiboUrl,
                       }
            #获取cookie的登录信息之后再访问页面
            contentHead = self.loginweb.GetContentHead(url, headers)
            if contentHead == "":
                logger.error(u"获取指定微博页面信息失败！")
                msg=u"获取指定微博页面信息失败！新浪中断了本次连接！"
                wx.MessageBox(msg,u"Warning")
                return False
            else:
                self.msg=self.GetWeiboDetailInfo(contentHead)
                if self.getTotalPage():
                    msg=u"微博地址：%s 验证正确" %self.weiboUrl
                    wx.CallAfter(self.window.WriteLogger, msg)
                else:
                    msg=u"微博地址：%s 验证错误" %self.weiboUrl
                    wx.CallAfter(self.window.WriteLogger, msg)
                    return False

        except Exception:
            s=sys.exc_info()
            msg = (u"Getweiboinfo GetHtmlData Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return False
        return True
    
    def GetWeiboDetailInfo(self,html):
        print html
        msg={}
        try:
            if '抱歉，你访问的页面地址有误，或者该页面不存在' in html:
                msg=u'指定微博页面不存在'
                wx.CallAfter(self.window.WriteLogger, msg)
                return False
            if '您当前访问的用户状态异常' in html:
                msg=u'weibo用户状态异常!'
                wx.CallAfter(self.window.WriteLogger, msg)
                return False
            html = self.GetHtmlInfo(html, '"domid":"Pl_Official_LeftWeiboDetail__')
            
            root = fromstring(html)#将网页转化为树形
            
            #提取微博信息
            x=root.xpath("//div[@class='WB_feed_datail S_line2 clearfix']")
            p=x[0].xpath("//div[@class='WB_detail']/div")#微博信息段
            
            msg['msgid']=p[0].get("mid")
            isforward=0#此微博是否为转发
            ouid=''#转发用户ID
            rouid=''#原消息用户ID
            omid=''#原消息ID
            x=root.xpath("//div[@class='WB_feed_datail S_line2 clearfix']/div[@class='WB_detail']/div")
            if len(x)>1:#该微博是转发微博
                omid=x[0].get("omid")
                isforward=1
                ids_node=x[0].get("tbinfo").replace('&', ',').replace('=', ',')
                ids=ids_node.split(',')
                ouid=ids[1]
                rouid=ids[3]
            else:
                ouid=x[0].get("tbinfo").split("=")[-1]
            
            msg['isforward']=isforward
            msg['ouid']=ouid
            msg['rouid']=rouid
            msg['omid']=omid
            
            #采集总页面数
#             if self.CrawlerType=="repost":#采集转发
#                 print x[3]
#                 p=x[3].xpath("//div[@action-type='feed_list_item']/div[@class='W_pages_minibtn']/a[@action-data]")
#                 msg['totalpage']=p[-1].text_content()
#             if self.CrawlerType=="comment":#采集评论
#                 print x[2]
#                 p=x[2].xpath("//div[@action-type='feed_list_item']/div[@class='W_pages_minibtn']/a[@action-data]")
#                 msg['totalpage']=p[-1].text_content()
            
        except Exception: 
            s=sys.exc_info()
            strmsg = (u"GetWeiboDetailInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(strmsg)
            msg={}
            return msg
        return msg 

    def GetHtmlInfo(self,html,xpathStr):
        try:
            for i in range(3):
                repose = html.find(xpathStr)
                #find 方法在很长的字符串中查找子字符串，并返回子字符串所在位置的左端索引，没有则返回-1
                if repose != -1:
                    break
            #find 方法在很长的字符串中查找子字符串，并返回子字符串所在位置的左端索引，没有则返回-1
            print repose
            if repose == -1:
                msg=u'指定微博页面标签信息获取失败，请检查页面地址！'
                wx.CallAfter(self.window.WriteLogger, msg)
                return ""
            strContent = html[repose:-1]#去指定范围内的字符
            repose = strContent.find("})</script>")
            if repose == -1:
                return ""
            strContent = strContent[0:repose+len('})</script>')]#指定字符串长度
            strContent = strContent[strContent.find("\"html\":\"")+8: -1-(len('})</script>'))]#取指定长度区间的字符串
            strContent = strContent.replace(r"\ /", "")
            strContent = strContent.replace(r"\n", "")
            strContent = strContent.replace(r"\t", "")
            strContent = strContent.replace(r"\r", "")
            strContent = strContent.replace(r"\/", "/")
            strContent = strContent.replace(r'\"', "'")
#             strContent = strContent.decode('unicode_escape')
            if strContent:
                strContent = strContent.replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", "")
            else:
                return ""
        except Exception:
            s=sys.exc_info()
            msg = (u"GetHtmlInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return ""
        return strContent
    
    
   
    def getTotalPage(self):
        #获取返回的data里面的totalpage属性值获取总页数
        weiboUrl=self.weiboUrl
        msgid=self.msg.get('msgid')
        pageNum=1
        try:
            rnd = getMillitime()#或者str(int(time.time() * 1000)
            if self.CrawlerType=="comment":#采集转发
                url = "http://weibo.com/aj/comment/big?_wv=5&id=%s&page=%s&__rnd=%s" %(msgid,pageNum,rnd)
            if self.CrawlerType=="repost":#采集评论
                url = "http://weibo.com/aj/mblog/info/big?_wv=5&id=%s&page=%s&__rnd=%s" %(msgid,pageNum,rnd)
            #用户搜索页面信息
            #浏览器确认自己身份是通过User-Agent头
            headers = {'Host':'weibo.com',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Accept-Encoding':'gzip, deflate',
                       'Connection':'keep-alive',
                       'Referer':weiboUrl,
                       }
            for i in range(3): #@UnusedVariable
                try:
                    self.window.curCount += 1
                    content = self.loginweb.GetContentHead(url, headers=headers)
                except:
                    continue
                if content:
                    break
            #获取cookie的登录信息之后再访问页面
            if content == "":
                logger.error(u"%s 失败:获取网页内容为空！")
            contentData=json.loads(content).get("data")
            totalPage= int(contentData['page']['totalpage'])
            self.msg['totalpage']=totalPage
            return True
            
        except Exception:
            s=sys.exc_info()
            msg = (u"getTotalPage Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg) 
            return False
            
        
class FetcherWeiboReorCom(threadpool.Job):
    
    def __init__(self,**kwargs):
        self.weiboUrl=kwargs.get("weiboUrl","")
        self.msg=kwargs.get("msg","")
        self.threadId=kwargs.get("threadId","")
        self.CrawlerType=kwargs.get("c_type","")
        self.result=kwargs.get("result_queue","")
        self.window=kwargs.get("window","")
        self.loginweb=modelsettings.LOGINWEB
#         self.loginweb=loginsinaweb.LoginSinaWeb()
        self.usersInfo=[]
    
    def run(self):
        while self.window.crawlerRunning:
#         while 1:
            page = self.threadId
            msg = u"正在采集微博:%s 第  %s 页 / 共 %s 页  %s信息." % (self.msg.get("msgid"), page, self.msg.get('totalpage'),self.CrawlerType)
            wx.CallAfter(self.window.WriteLogger, msg)
            try:
                self.GetHtmlData()
            except:
                s=sys.exc_info()
                msg = (u"FetcherWeiboReorCom Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                logger.error(msg)
            finally:
                self.result.put(self.usersInfo)
                self.window.finishedCount += 1
                wx.CallAfter(self.window.UpdateProcessBar, self.window.finishedCount)
                logger.info(u"add the ReorCom user in to the queue")
                break
            
    #获取第一页微博，取到指定消息的ID
    def GetHtmlData(self):
        weiboUrl=self.weiboUrl
        msgid=self.msg.get('msgid')
        pageNum=self.threadId
        try:
            rnd = getMillitime()#或者str(int(time.time() * 1000)
            if self.CrawlerType=="comment":#采集转发
                url = "http://weibo.com/aj/comment/big?_wv=5&id=%s&page=%s&__rnd=%s" %(msgid,pageNum,rnd)
            if self.CrawlerType=="repost":#采集评论
                url = "http://weibo.com/aj/mblog/info/big?_wv=5&id=%s&page=%s&__rnd=%s" %(msgid,pageNum,rnd)
            #用户搜索页面信息
            #浏览器确认自己身份是通过User-Agent头
            headers = {'Host':'weibo.com',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Accept-Encoding':'gzip, deflate',
                       'Connection':'keep-alive',
                       'Referer':weiboUrl,
                       }
            for i in range(3): #@UnusedVariable
                try:
                    self.window.curCount += 1
                    content = self.loginweb.GetContentHead(url, headers=headers)
                except:
                    continue
                if content:
                    break
            #获取cookie的登录信息之后再访问页面
            if content == "":
                logger.error(u"%s 失败:获取网页内容为空！")
            contentData=self.getHtmlFromJson(content)
            #获取到了json格式的页面可以直接根据标签取得对应信息
            #分为评论和转发，两者数据获取标签不一致
            if self.CrawlerType=="comment":#采集转发
                users=self.GetCommentUserInfo(contentData)
            if self.CrawlerType=="repost":#采集评论
                users=self.GetRepostUserInfo(contentData)
            self.usersInfo.extend(users)

        except Exception:
            s=sys.exc_info()
            msg = (u"FetcherWeiboReorCom GetHtmlData Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)  
        
    def getHtmlFromJson(self, html): 
        if json.loads(html)['code'] == '100000':    
            return json.loads(html).get("data") 
        else:
            msg = (u"getHtmlFromJson Error 获取Json页面信息错误！ ")
            logger.error(msg)
    
    def GetRepostUserInfo(self,html):
        users=[]
        try:
            if '抱歉，你访问的页面地址有误，或者该页面不存在' in html:
                print (u'指定微博页面不存在')
                return users
            if '您当前访问的用户状态异常' in html:
                #print (u'weibo用户状态异常!')
                return users
            html=html['html']
            html=str(html)
            html = self.GetHtmlInfo(html,'<dl class="comment_list S_line1 clearfix "')
            root = fromstring(html)
            
            usersDivise=root.xpath('//dl[@class="comment_list S_line1 clearfix "]')
            if len(usersDivise) > 0:
                for div in usersDivise:
    #                 user = dict.fromkeys(sinaSetting.USER_KEY, '')#初始化用户
                    user={}
                    user['msgid']=self.msg.get('msgid')
                    user['ouid']=self.msg.get('ouid')
                    user['mid']=div.get("mid")#评论或者转发消息Id
                    div = tostring(div , encoding='utf-8')
                    div = fromstring(div)
                    try:
                        #基本等信息
                        d_node = div.xpath("//dt/a/img")[0]
                        user['Imgurl']=d_node.get("src")
                        user['uid']=d_node.get("usercard").split("=")[-1]
                        #等级信息
                        h_node=div.xpath("//dd/a")
                        user['nickname']=h_node[0].get("nick-name")
                        user['uname']=h_node[0].get("href").split('/')[-1]
                        vip=0#会员
                        verify=0#认证
                        daren=0
                        if len(h_node)>1:
                            href=h_node[1].get("href")
                            if href.startswith('http://verified'):
                                verify=1
                            elif href.startswith('http://vip'):
                                vip=1    
                            elif href.startswith('http://club'):
                                daren=1
                        if len(h_node)==3:
                            href=h_node[2].get("href")
                            if href.startswith('http://vip'):
                                vip=1 
                        user['vip']=vip 
                        user['verify']=verify
                        user['daren']=daren  
                        #微博内容
                        m_node=div.xpath("//dd/em")
                        msg=''
                        if m_node:
                            msg=m_node[0].text_content()
                        user['msg']=msg
                        #操作时间等信息
                        i_node=div.xpath("//dd/div[@class='info']/div[@class='info']/span[@class='fl']/em[@class='S_txt2']/a")
                        if len(i_node)==0:
                            i_node=div.xpath("//dd/div[@class='info']/span[@class='fl']/em[@class='S_txt2']/a")
                        date=''
                        if i_node[0].get("date"):
                            date=i_node[0].get("date")
                        user['date']=date
                        msgurl=''
                        if i_node[0].get("href"):
                            msgurl="http://weibo.com"+i_node[0].get("href")
                        user['msgurl']=msgurl#转发或者评论消息Url
                        users.append(user)
                    except:
                            s=sys.exc_info()
                            msg = (u"GetRepostUserInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                            logger.error(msg)
                else:
                    pass
        except Exception: 
            s=sys.exc_info()
            msg = (u"GetRepostUserInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            users=[]
            return users
        return users

    def GetCommentUserInfo(self,html):
        users=[]
        try:
            if '抱歉，你访问的页面地址有误，或者该页面不存在' in html:
                print (u'指定微博页面不存在')
                return users
            if '您当前访问的用户状态异常' in html:
                #print (u'weibo用户状态异常!')
                return users
            html=html['html']
            html=str(html)
            html = self.GetHtmlInfo(html, '<dl class="comment_list S_line1"')
            root = fromstring(html)
            
            usersDivise=root.xpath('//dl[@class="comment_list S_line1"]')
            if len(usersDivise) > 0:
                for div in usersDivise:
    #                 user = dict.fromkeys(sinaSetting.USER_KEY, '')#初始化用户
                    user={}
                    user['msgid']=self.msg.get('msgid')
                    user['ouid']=self.msg.get('ouid')
                    user['mid']=div.get("mid")#评论消息id,与微博消息ID相同
                    div = tostring(div , encoding='utf-8')
                    div = fromstring(div)
                    try:
                        #基本等信息
                        d_node = div.xpath("//dt/a/img")[0]
                        user['Imgurl']=d_node.get("src")
                        user['uid']=d_node.get("usercard").split("=")[-1]
                        #等级信息
                        h_node=div.xpath("//dd/a")
                        user['nickname']=h_node[0].get("title")
                        user['uname']=h_node[0].get("href").split('/')[-1]
                        vip=0#会员
                        verify=0#认证
                        daren=0
                        if len(h_node)>1:
                            href=h_node[1].get("href")
                            if href.startswith('http://verified'):
                                verify=1
                            elif href.startswith('http://vip'):
                                vip=1    
                            elif href.startswith('http://club'):
                                daren=1
                        if len(h_node)==3:
                            href=h_node[2].get("href")
                            if href.startswith('http://vip'):
                                vip=1 
                        user['vip']=vip 
                        user['verify']=verify
                        user['daren']=daren  
                        
                        #操作时间等信息
                        i_node=div.xpath("//dd/span[@class='S_txt2']")
                        date=''#评论时间为汉字
                        if i_node[0].text_content():
                            date=i_node[0].text_content()
                        parserdate=self.parse_datetime(date.replace("(", "").replace(")", ""))
                        user['date']=parserdate
                        #微博内容
                        m_node=div.xpath("//dd/img")
                        msg=''
                        msgcontent=div.xpath("//dd")[0].text_content()
                        content=msgcontent.split(date)[0].strip().replace(',', u'，').replace(';', u'；')
                        if m_node>0:
                            for i in range(len(m_node)):
                                msg=str(m_node[i].get("title"))+msg#表情
                        user['msg']=content+msg
                        users.append(user)
                    except:
                            s=sys.exc_info()
                            msg = (u"GetCommentUserInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                            logger.error(msg)
                else:
                    pass
        except Exception: 
            s=sys.exc_info()
            msg = (u"GetCommentUserInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            users=[]
            return users
        return users
        
    def GetHtmlInfo(self,html,xpathStr):
        try:
            for i in range(3):
                repose = html.find(xpathStr)
                #find 方法在很长的字符串中查找子字符串，并返回子字符串所在位置的左端索引，没有则返回-1
                if repose != -1:
                    break
            #find 方法在很长的字符串中查找子字符串，并返回子字符串所在位置的左端索引，没有则返回-1
            print repose
            if repose == -1:
                return ""
            strContent = html[repose:-1]#去指定范围内的字符

            strContent = strContent.replace(r"\ /", "")
            strContent = strContent.replace(r"\n", "")
            strContent = strContent.replace(r"\t", "")
            strContent = strContent.replace(r"\r", "")
            strContent = strContent.replace(r"\/", "/")
            strContent = strContent.replace(r'\"', "'")
#             strContent = strContent.decode('unicode_escape')
            if strContent:
                strContent = strContent.replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", "")
            else:
                return ""
        except Exception:
            s=sys.exc_info()
            msg = (u"GetHtmlInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return ""
        return strContent
    
    def _strptime(self, string, format_):
        try:
            return datetime.datetime.strptime(string, format_)
        except:
            logger.error(u"getweiboinfo _strptime error")
        
    def parse_datetime(self, dt_str):
        dt = None
        if u'今天' in dt_str:
            dt_str = dt_str.replace(u'今天', datetime.datetime.now().strftime('%Y-%m-%d'))
            dt = self._strptime(dt_str, '%Y-%m-%d %H:%M')
        elif u'月' in dt_str and u'日' in dt_str:
            this_year = datetime.datetime.now().year
            dt = self._strptime('%s %s' % (this_year, dt_str), '%Y %m月%d日 %H:%M')
        elif u'分钟' in dt_str:
            sec = int(dt_str.split(u'分钟', 1)[0].strip()) * 60
            dt = datetime.datetime.now() - datetime.timedelta(seconds=sec)
        else:
            dt = self._strptime(dt_str, '%Y-%m-%d %H:%M')
            
        return time.mktime(dt.timetuple())
   
   
def _strptime(string, format_):
    try:
        return datetime.datetime.strptime(string, format_)
    except:
        logger.error(u"getweiboinfo _strptime error")
        
def parse_datetime(dt_str):
    dt = None
    if u'今天' in dt_str:
        dt_str = dt_str.replace(u'今天', datetime.datetime.now().strftime('%Y-%m-%d'))
        dt = _strptime(dt_str, '%Y-%m-%d %H:%M')
    elif u'月' in dt_str and u'日' in dt_str:
        this_year = datetime.datetime.now().year
        dt = _strptime('%s %s' % (this_year, dt_str), '%Y %m月%d日 %H:%M')
    else:
        dt = _strptime(dt_str, '%Y-%m-%d %H:%M')
    return time.mktime(dt.timetuple()) 




if __name__== '__main__':
    url="http://weibo.com/1400788390/B49Gxqgp4"
    getweibo=GetWeiboInfo(weiboUrl=url,c_type='repost')
#     timestr="5月14日 18:50"
#     parse_datetime(timestr)
    login=loginsinaweb()
    login.Login(loginUname='XXXXX@qq.com', loginPasword='XXXXXX')
#     weiboCrawler = FetcherWeibos(result_queue=queue, thread_id=1, window=self.window, thread_num=1, 
#                                  output_path=self.outPath, user=self.userinfo, max_page=50, loginweb=settings.LOGINWEB)
#         weiboCrawler.run()
#     fetcherFollows.GetHtmlData(1819724603, 1)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
        