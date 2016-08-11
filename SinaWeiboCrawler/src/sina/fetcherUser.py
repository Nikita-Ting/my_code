# encoding:utf-8

'''
created on 2014-5-6
this is a master to control the thread of crawler user
include :user (fans and follows)
part of src come from the Pameng
'''


from Queue import Queue, Empty 
import StringIO
import cookielib
import datetime
import gzip
import json#?import simplejson 有什么区别？
import sys
import time
import urllib
import urllib2

from lxml.html import tostring
from lxml.html.soupparser import fromstring
import wx

from crawlermodel import logfile
from crawlermodel import settings
from sina import settings as sinasettings
from sina import loginsinaweb
from sina.fetcherWeibo import FetcherWeibos
from sina.loginsinaweb import LoginSinaWeb
import threadpool


logger=logfile.LogFile().getLogger('run')

class FetcherUser():
    
    def __init__(self,window,threadNum,outPath):
        self.window=window
        self.threadNum=threadNum
        self.outPath=outPath
        self.userinfo={}
        self.msginfo = []
        self.cookieJar= cookielib.CookieJar()
        self.cookieProcessor = urllib2.HTTPCookieProcessor(self.cookieJar)
        self.opener=urllib2.build_opener(self.cookieProcessor)
        urllib2.install_opener(self.opener)
            
    def setCookie(self,cookie):
        self.cookieJar.set_cookie(cookie)
    
    def getMillitime(self):
        pre = str(int(time.time()))
        pos = str(datetime.datetime.now().microsecond)[:3]
        return pre + pos
    
    def gzipData(self,spiderData):
        if 0 == len(spiderData):
            return spiderData
        spiderDataStream = StringIO.StringIO(spiderData)
        spiderData = gzip.GzipFile(fileobj=spiderDataStream).read()
        return spiderData
    
    def GetHtmlSource(self,url, headers={}, data={}, proxyip=""):
        #是否需要到cookie读取登录信息
        content=""
        try:
            if not url.startswith("http://"):
                url = "http://" + url
            request = urllib2.Request(url=url.strip(), headers=headers)
            if data:
                logger.info("Add post data.")
                request.add_data(urllib.urlencode(data))
            if proxyip and "127.0.0.1" not in proxyip:
                if not proxyip.startswith("http"):
                    proxyip = "http://" + proxyip
                
                proxy_handler = urllib2.ProxyHandler({'http': proxyip})
                self.opener = urllib2.build_opener(self.cookieProcessor, proxy_handler) 
            else:
                self.opener = urllib2.build_opener(self.cookieProcessor)
            urllib2.install_opener(self.opener)
            response = self.opener.open(request, timeout=10)
            if response.info().get("Content-Encoding") == 'gzip':
                content = self.gzipData(response.read())
            else:
                content = response.read()
            if "抱歉，你的帐号存在异常，暂时无法访问" in content and "解除限制" in content:
                content = ""
        except:
            s = sys.exc_info()
            msg = (u"ip:%s getHtmlSource Error %s happened on line %d" % (proxyip, s[1], s[2].tb_lineno))
            logger.error(msg)
            logger.error(url)
        return content
        
    def GetHtmlData(self,url,uid,gsid,refUrl,proxyip):
        content=""
        self.userinfo['uid'] = uid
        for i in range(3):
            proxyip=proxyip
            try:
                if not url.startswith("http://"):
                    url = "http://"+url
                headers = {'Host': 'm.weibo.cn',
                            'User-Agent': 'android',
                            'Accept': '*/*',
                            'Connection': 'keep-alive',
                            'Accept-encoding': 'gzip, deflate',
                            'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                            'X-Requested-With': 'XMLHttpRequest',
                            }
                if refUrl:
                    headers['Referer'] = refUrl
                headers['Cookie'] = 'gsid_CTandWM=' + gsid + '; _WEIBO_UID='+uid
                content = self.GetHtmlSource(url, headers=headers, proxyip=proxyip)
                print "--------GetHtmlData"
                if "登录" in content and "密码" in content and "注册" in content :
                        content = ""
                        logger.info(u"登录，密码，注册")
                elif "微博精选" in content and "热门转发" in content:
                        content = ""
                        logger.info(u"微博精选。。。。。")
                elif "抱歉，你的帐号存在异常，暂时无法访问" in content and "解除访问限制" in content:
                        content = ""
                        logger.info(u"账号异常")
                    #time.sleep(0.2*random.randint(1, 10))
            except Exception:
                s=sys.exc_info()
                msg = (u"gethtmldata Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                logger.error(msg)
                content = ""
            if content != "":
                break
        return content    
            
    def GetUserBasicData(self, html):
        #用户基本消息来自解析的手机版微博
        #自动存储到self.userinfo
        try:
            html = html.decode('unicode-escape').encode('utf-8')
            if '用户不存在哦!' in html:
                logger.error('GetUserBasicData用户不存在!')
                return False
            userinfoObj = None
            try:
                userinfoObj = json.loads(html)
            except:
                html = html.replace('\n', '')
                html = html.replace('\r', '')
                html = html.replace('"', '\\"')
                html = html.replace(':\\"', ':"')
                html = html.replace('\\":', '":')
                html = html.replace(',\\"', ',"')
                html = html.replace('\\",', '",')
                html = html.replace('{\\"', '{"')
                html = html.replace('\\"}', '"}')
                html = html.replace('[\\"', '["')
                html = html.replace('\\"]', '"]')
                html = html.replace('\\(', '\\\\(')
                userinfoObj = json.loads(html)
            #user base info
            user = userinfoObj.get("userInfo", None)
            if user:
                #user name
                weibohao = user.get("weihao","")
                if weibohao == 0:
                    weibohao = user.get("id","")
                self.userinfo['uname'] = weibohao
                #screen name
                self.userinfo['nickname'] = user.get("name","").encode('utf-8')
                #profile_image_url
                self.userinfo['Imgurl'] = user.get("profile_image_url","").encode('utf-8')
                #description
                self.userinfo['intro'] = user.get("description","").encode('utf-8')
                #mblogNum
                self.userinfo['n_weibos'] = user.get("mblogNum",0)
                #attNum
                self.userinfo['n_follows'] = user.get("attNum",0)
                #fansNum
                self.userinfo['n_fans'] = user.get("fansNum",0)
                #ta
                userSex = user.get("ta","").encode('utf-8')
                if userSex == "他":
                    sex = "男"
                elif userSex == "她" :
                    sex = "女"
                else:
                    sex = "ta"
                self.userinfo['sex'] = sex
                #nativePlace
                self.userinfo['locat'] = user.get("nativePlace","").encode('utf-8')
                #vip
                vipFlag = user.get("vip")
                if vipFlag and vipFlag!=0 and len(vipFlag) > 0:
                    vipFlag = vipFlag[0]
                vip = 0
                popman = 0
                vipFlag = str(vipFlag)
                if "5338.gif" in vipFlag:
                    vip = 1
                elif "5547.gif" in vipFlag:
                    popman = 1
                else:
                    pass
                self.userinfo['daren'] = popman
                self.userinfo['verified'] = vip
                msg = u"用户： %s 个人信息采集完成 \t" % (self.userinfo['nickname'])
                wx.CallAfter(self.window.WriteLogger, msg)
                wx.CallAfter(self.window.WriteLogger, u"===================")
               
                
                if sinasettings.CrawlerContent["cwlWeibos"]:
                    msg = u"正在采集用户： %s,微博数：%s \t" % (self.userinfo['nickname'], self.userinfo['n_weibos'])
                    wx.CallAfter(self.window.WriteLogger, msg)
                    #若用户指定采集微博，则获取用户微博页数，采集微博信息
                    maxPage = int((int(self.userinfo['n_weibos'])-1)/44)+1
                    print "weibo pages:"
                    print maxPage
                    if maxPage >= 1:
                        wx.CallAfter(self.window.SetProcessBarRange, (maxPage*1+self.window.processBarValue))
                        #爬取该用户的所有微博信息
                        msgList = self.GetUserWeibos(maxPage)
                        self.window.totalCount += (maxPage)
                        self.msginfo.extend(msgList)
            else:
                logger.error('新浪数据格式可能发生了变化!')
                return False
               
        except Exception:
            s=sys.exc_info()
            msg = (u"GetUserBasicData Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return False
        return True
            
    def GetUserDetailData(self,html):
        print "............GetUserDetailData"
        print html
        try:
            html = html.encode('utf-8')
            if '用户不存在哦!' in html:
                logger.error('GetUserDetailData用户不存在哦!')
                return 'user is empty'
            #用户的详细信息
            userinfoObj = json.loads(html)
            userDetailInfo = userinfoObj.get("userInfoDetail", None)
            if userDetailInfo:
                if userDetailInfo.get("ok", 0) == 1:
                    #basicInfo
                    detailInfoObj = userDetailInfo.get("basicInfo", None)
                    if detailInfoObj:
                        #created_at
                        self.userinfo['creatTime'] = detailInfoObj.get("created_at", "").encode('utf-8')
                        #birthday
                        self.userinfo['birth'] = detailInfoObj.get("birthday", "")
                        #verified
                        #verified_reason
                        self.userinfo['verifInfo'] = detailInfoObj.get("verified_reason", "").encode('utf-8')
                        #用户联系方式
                        #qq
                        self.userinfo['QQ'] = detailInfoObj.get("qq", "").encode('utf-8')
                        #email
                        self.userinfo['email'] = detailInfoObj.get("email", "").encode('utf-8')
                        #msn
                        self.userinfo['MSN'] = detailInfoObj.get("msn", "").encode('utf-8') 
                    #用户教育信息
                    infoObjs = userDetailInfo.get("editInfo", None)
                    editInfo = ""
                    if infoObjs:
                        for info in infoObjs:
                            editInfo += info.get("school")+","
                    editInfo = editInfo[:editInfo.rfind(',')]
                    #careerInfo
                    infoObjs = userDetailInfo.get("careerInfo", None)
                    careerInfo = ""
                    if infoObjs:
                        for info in infoObjs:
                            careerInfo += info.get("company")+","
                    careerInfo = careerInfo[:careerInfo.rfind(',')]
                    self.userinfo['school'] = editInfo.encode('utf-8')
                    self.userinfo['company'] = careerInfo.encode('utf-8')
                else:
                    return 'user detail load failure'
            #用户标签
            #tags
            userTagsObj = userinfoObj.get("tags", None)
            userTagStr = ""
            if userTagsObj:
                if userTagsObj.get("ok", 0) == 1:
                    #usertags
                    tags = (userTagsObj.get("usertags"))
                    for tag in tags:
                        userTagStr += tag.get("name", "")+","
                    userTagStr = userTagStr[:userTagStr.rfind(',')]
                    self.userinfo['tags'] = userTagStr
                else:
                    return 'user tag load failure'
        except Exception:
            s=sys.exc_info()
            msg = (u"GetUserDetailData Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return "exception"
        return 'success'
            
    def GetUserWeibos(self,maxPage):
        queue = Queue(0)
        weiboCrawler = FetcherWeibos(result_queue=queue, thread_id=1, window=self.window, thread_num=self.threadNum, 
                                 output_path=self.outPath, user=self.userinfo, max_page=maxPage, loginweb=settings.LOGINWEB)
        weiboCrawler.run()
        msgList = []
        try:
            for i in range(queue.qsize()): 
                msgList.extend(queue.get(block=False))
        except Empty:
            pass # 
            logger.info(u"微博消息复制成功")
        return msgList




class FetcherUserFollows(threadpool.Job):
    def __init__(self,**kwargs):
        print "--------------FetcherUserFollows init-"
        self.loginweb=settings.LOGINWEB
        self.result=kwargs.get("result_queue"," ")
        self.threadId=kwargs.get("thread_id"," ")
        self.user=kwargs.get("user", " ")
        self.maxPage=kwargs.get("max_page",10)
        self.window=kwargs.get("window"," ")
#         self.loginweb=loginsinaweb.LoginSinaWeb()
        self.follows=[]
        
      
    def run(self):
        print "FetcherUserFollows run"
        while self.window.crawlerRunning:
            msg = u"正在采集用户:%s  第  %s 页 / 共 %s 页 关注列表." % (self.user.get("nickname"), self.threadId, self.maxPage)
            wx.CallAfter(self.window.WriteLogger, msg)
            uid=self.user.get("uid")
            try:
                self.GetHtmlData(uid,self.threadId)
            except:
                s=sys.exc_info()
                msg = (u"FetcherUserFollows Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                logger.error(msg)
            finally:
                self.result.put(self.follows)
                self.window.finishedCount += 1
                wx.CallAfter(self.window.UpdateProcessBar, self.window.finishedCount)
                logger.info(u"add the follows in to the queue")
                break
     
    #获取html内容   
    def GetHtmlData(self,uid,pageNum):
        try:
            url = "http://weibo.com/%s/follow?page=%s" % (uid,pageNum)
            #用户搜索页面信息
            #浏览器确认自己身份是通过User-Agent头
            headers = {'Host':'weibo.com',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Accept-Encoding':'gzip, deflate',
                       'Connection':'keep-alive',
                       'Referer':'http://weibo.com',
                       }
            #获取cookie的登录信息之后再访问页面
            contentHead = self.loginweb.GetContentHead(url, headers)
            if contentHead == "":
                logger.error(u"%s 失败:获取网页内容为空！" % uid)
            follows=self.GetFollowsInfo(contentHead)
            self.follows.extend(follows)
#             if not self.GetFollowsInfo(contentHead):
#                 logger.info(u"getFollowsInfo fail")
#             else:
#                 logger.info(u"getFollowsInfo success")
            #self.window.finishedCount += 1
        except Exception:
            s=sys.exc_info()
            msg = (u"getFollowsInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
        
    #解析获取到的网页，并将对应信息分离出来     
    def GetFollowsInfo(self,html): 
        follows=[]
        try:
            if '搜索结果为空' in html:
                print (u'weibo用户不存在!')
                return False
            if '您当前访问的用户状态异常' in html:
                #print (u'weibo用户状态异常!')
                return False
            html = self.GetHtmlInfo(html, '"domid":"Pl_Official_LeftHisRelation__')
            root = fromstring(html)#将网页转化为树形
            #新浪关注用户界面分为两部分，一部分是推荐感兴趣的用户，这些用户与登录用户之间有共同的粉丝,这一部分页面标签没取到
            #另一部分是爬取用户的其他关注用户，与关注用户之间没有较强关系
            usersDivise = root.xpath("//li[@class='clearfix S_line1']")
            if len(usersDivise) > 0:
                
                for div in usersDivise:
#                     user = dict.fromkeys(sinaSetting.USER_KEY, '')
                    follow=dict.fromkeys(sinasettings.F_KEY, '')#定义一个用户字典并初始化
                    #用户Id
                    follow['userid']=self.user.get("uid")
                    div = tostring(div , encoding='utf-8')
                    div = fromstring(div)
                    try:
                        #主页等信息
                        d_node = div.xpath("//div[@class='left']/div[@class='face mbspace']/a/img")[0]
                        h_node=div.xpath("//div[@class='left']/div[@class='face mbspace']/a")[0]
                        follow['Imgurl'] = d_node.get("src",'')
                        follow['uid'] = d_node.get("usercard",'').split("=")[1]#关注用户的ID
                        follow['uname'] = h_node.get("href"," ").split("/")[-1]#主页地址,也有可能是uname
#                         follow['nickname1'] = h_node.get("title",'')
                        
                        #用户等级信息
#                         follow['nickname'] = div.xpath("//div[@class='con']/div[@class='con_left']/div['name']/a")[0].text_content()
                        n_node=div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='name']/a")
                        follow['nickname']=n_node[0].text_content()
                        vip=0#会员
                        verify=0#认证
                        daren=0
                        if len(n_node)>1:
                            href=n_node[1].get("href")
                            if href.startswith('http://verified'):
                                verify=1
                            elif href.startswith('http://vip'):
                                vip=1    
                            elif href.startswith('http://club'):
                                daren=1
                        if len(n_node)==3:
                            href=n_node[2].get("href")
                            if href.startswith('http://vip'):
                                vip=1 
                        follow['vip']=vip 
                        follow['verify']=verify
                        follow['daren']=daren   
                        #性别、地址
                        sex_node=div.xpath("//div[@class='con']/div[@class='con_left']/div['name']/span[@class='addr']/em")
                        sex = ''
                        if sex_node:
                            sex = sex_node[0].get("class").split(" ")[1]
                        follow['sex'] = sex
                        addr_node = div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='name']/span")
                        addr = ''
                        if addr_node:
                            addr = addr_node[0].text_content()
                        follow['addr'] = addr
#                         num_node=[]
                        num_node = div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='connect']/a")
                        if num_node:
                            follow['n_follows'] = num_node[0].text_content()
                            follow['n_fans'] = num_node[1].text_content()
                            follow['n_weibos'] = num_node[2].text_content()
                        
                        intro_node = div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='info']")
                        intro = ''
                        if intro_node:
                            intro = intro_node[0].text_content()
                        follow['intro'] = intro
                        #最近的微博
                        lw_node=div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='weibo']/a")
                        if lw_node:
                            follow['latestweibo']=lw_node[0].text_content()
                        #关注设备
                        fw_node=div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='from W_textb']/a")
                        if fw_node:
                            follow['p_from']=fw_node[0].text_content()
                        follows.append(follow)
                    except:
                        s=sys.exc_info()
                        msg = (u"getFollowsInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                        logger.error(msg)
#                         pass
            else:
                pass
        except Exception: 
            s=sys.exc_info()
            msg = (u"GetFollowsInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            follows=[]
            return follows
        return follows       
     
    
     
          
    #处理html页面，是页面具有更高的可读性;从指定路径开始抓取网页内容     
    
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
            
   
#采集用户粉丝  


class FetcherUserFans():
    
    def __init__(self,**kwargs):
        print "--------------FetcherUserFollows init-"
        self.loginweb=settings.LOGINWEB
        self.result=kwargs.get("result_queue"," ")
        self.threadId=kwargs.get("thread_id"," ")
        self.user=kwargs.get("user", " ")
        self.maxPage=kwargs.get("max_page",10)
        self.window=kwargs.get("window"," ")
#         self.loginweb=loginsinaweb.LoginSinaWeb()
        self.fans=[]
        
      
    def run(self):
        print "FetcherUserFans run"
        while self.window.crawlerRunning:
            msg = u"正在采集用户:%s  第  %s 页 / 共 %s 页 粉丝列表." % (self.user.get("nickname"), self.threadId, self.maxPage)
            wx.CallAfter(self.window.WriteLogger, msg)
            uid=self.user.get("uid")
            try:
                self.GetHtmlData(uid,self.threadId)
            except:
                s=sys.exc_info()
                msg = (u"FetcherUserFans Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                logger.error(msg)
            finally:
                self.result.put(self.fans)
                self.window.finishedCount += 1
                wx.CallAfter(self.window.UpdateProcessBar, self.window.finishedCount)
                logger.info(u"add the fans in to the queue")
                break
    
    #获取html内容   
    def GetHtmlData(self,uid,pageNum):
        try:
            url = "http://weibo.com/%s/fans??page=%s" % (uid,pageNum)
            #用户搜索页面信息
            #浏览器确认自己身份是通过User-Agent头
            headers = {'Host':'weibo.com',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Accept-Encoding':'gzip, deflate',
                       'Connection':'keep-alive',
                       'Referer':'http://weibo.com',
                       }
            #获取cookie的登录信息之后再访问页面
            contentHead = self.loginweb.GetContentHead(url, headers)
            if contentHead == "":
                logger.error(u"%s 失败:获取网页内容为空！" % uid)
            fans=self.GetFansInfo(contentHead)
            self.fans.extend(fans)

        except Exception:
            s=sys.exc_info()
            msg = (u"getFansInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
        
    #解析获取到的网页，并将对应信息分离出来     
    def GetFansInfo(self,html): 
        fans=[]
        try:
            if '搜索结果为空' in html:
                print (u'weibo用户不存在!')
                return False
            if '您当前访问的用户状态异常' in html:
                #print (u'weibo用户状态异常!')
                return False
            html = self.GetHtmlInfo(html, '"domid":"Pl_Official_LeftHisRelation__')
            root = fromstring(html)#将网页转化为树形
            #新浪关注用户界面分为两部分，一部分是推荐感兴趣的用户，这些用户与登录用户之间有共同的粉丝,这一部分页面标签没取到
            #另一部分是爬取用户的其他关注用户，与关注用户之间没有较强关系
            usersDivise = root.xpath("//li[@class='clearfix S_line1']")
            if len(usersDivise) > 0:
                
                for div in usersDivise:
#                     user = dict.fromkeys(sinaSetting.USER_KEY, '')
                    fan=dict.fromkeys(sinasettings.F_KEY, '')#定义一个用户字典并初始化
                    #用户Id
                    fan['userid']=self.user.get("uid")
                    div = tostring(div , encoding='utf-8')
                    div = fromstring(div)
                    try:
                        #主页等信息
                        d_node = div.xpath("//div[@class='left']/div[@class='face mbspace']/a/img")[0]
                        h_node=div.xpath("//div[@class='left']/div[@class='face mbspace']/a")[0]
                        fan['Imgurl'] = d_node.get("src",'')
                        fan['uid'] = d_node.get("usercard",'').split("id=")[1]#关注用户的ID
                        fan['uname'] = h_node.get("href"," ").split("/")[-1]#主页地址,也有可能是uname
                        fan['nickname'] = h_node.get("title",'')
                        
                        #用户等级信息
#                         follow['nickname'] = div.xpath("//div[@class='con']/div[@class='con_left']/div['name']/a")[0].text_content()
                        n_node=div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='name']/a")
#                         fan['nickname']=n_node[0].text_content()
                        vip=0#会员
                        verify=0#认证
                        daren=0
                        if len(n_node)>1:
                            href=n_node[1].get("href")
                            if href.startswith('http://verified'):
                                verify=1
                            elif href.startswith('http://vip'):
                                vip=1    
                            elif href.startswith('http://club'):
                                daren=1
                        if len(n_node)==3:
                            href=n_node[2].get("href")
                            if href.startswith('http://vip'):
                                vip=1 
                        fan['vip']=vip 
                        fan['verify']=verify
                        fan['daren']=daren   
                        #性别、地址
                        sex_node=div.xpath("//div[@class='con']/div[@class='con_left']/div['name']/span[@class='addr']/em")
                        sex = ''
                        if sex_node:
                            sex = sex_node[0].get("class").split(" ")[1]
                        fan['sex'] = sex
                        addr_node = div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='name']/span")
                        addr = ''
                        if addr_node:
                            addr = addr_node[0].text_content()
                        fan['addr'] = addr
#                         num_node=[]
                        num_node = div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='connect']/a")
                        if num_node:
                            fan['n_follows'] = num_node[0].text_content()
                            fan['n_fans'] = num_node[1].text_content()
                            fan['n_weibos'] = num_node[2].text_content()
                        
                        intro_node = div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='info']")
                        intro = ''
                        if intro_node:
                            intro = intro_node[0].text_content()
                        fan['intro'] = intro
                        #最近的微博
                        lw_node=div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='weibo']/a")
                        if lw_node:
                            fan['latestweibo']=lw_node[0].text_content()
                        #关注设备
                        fw_node=div.xpath("//div[@class='con']/div[@class='con_left']/div[@class='from W_textb']/a")
                        if fw_node:
                            fan['p_from']=fw_node[0].text_content()
                        fans.append(fan)
                    except:
                        s=sys.exc_info()
                        msg = (u"getFollowsInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
                        logger.error(msg)
#                         pass
            else:
                pass
        except Exception: 
            s=sys.exc_info()
            msg = (u"GetFollowsInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            fans=[]
            return fans
        return fans      
     
     
               
  
    #处理html页面，是页面具有更高的可读性,#从指定路径开始抓取网页内容
    
    def GetHtmlInfo(self,html,xpathStr):
        try:
            for i in range(3):
                repose = html.find(xpathStr)
                #find 方法在很长的字符串中查找子字符串，并返回子字符串所在位置的左端索引，没有则返回-1
                print repose
                if repose != -1:
                    break
            if repose == -1:
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
    
    
     
if __name__== '__main__':
    fetcherFollows=FetcherUserFollows()

    login = LoginSinaWeb()
#     login.checkCookie(uname=,pasword)
    login.Login(loginUname='XXXXXqq.com', loginPasword='XXXX')
    fetcherFollows.GetHtmlData(1819724603, 1)
    
            
            