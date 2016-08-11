# encoding:utf-8

'''
created on 2014-5-1
this is login of sinaweibo and cookie
part of src come from Pameng
'''

import os
import sys
import wx
import urllib2
import urllib
import cookielib
import time
import datetime
import json
import re
import random
import base64
import StringIO
import gzip
import rsa
import settings
from crawlermodel import settings as modelsetting
from rsa import transform
from crawlermodel.logfile import LogFile
# from frame.showverifycodeframe import VerifyCodeFrame



logger=LogFile().getLogger('run')

class LoginSinaWeb():
    connectionNum=0
    
    def __init__(self,**kwargs):
        self.cookJar=cookielib.LWPCookieJar()
        '''为了从HTML文档提取cookies，首先得使用cookielib模块的LWPCookieJar()函数
                创建一个cookie jar的实例。LWPCookieJar()函数将返回一个对象，
                该对象可以从硬盘加载Cookie，同时还能向硬盘存放Cookie。'''
        self.cookieProcessor=urllib2.HTTPCookieProcessor(self.cookJar)
        #将cookie对象和Http的cookie处理器绑定
        self.opener=urllib2.build_opener(self.cookieProcessor,urllib2.HTTPHandler)
        #创建一个opener，将保存了cookie的http处理器，和设置一个handler用于处理http的URL打开
        urllib2.install_opener(self.opener)
        self.softPath=os.path.join(settings.PATH,settings.FILE_PATH_DEFAULT)
        self.cookieFile=os.path.join(self.softPath,"cookie.dat")
        self.proxyip=kwargs.get("proxyip","")
        self.window=kwargs.get('window', None)
        
        self.pcid=''
        self.servertime=''
        self.nonce=''
        self.pubkey=''
        self.rsakv=''

    def GetMillTime(self):
        #获得当前时间的微秒
        pre=str(int(time.time()))
        pos=str(datetime.datetime.now().microsecond)[:3]
        return pre+pos
    
    def GetServerTime(self):
        #获得新浪的服务器时间
        url=( 'http://login.sina.com.cn/sso/prelogin.php?entry=account'
                   '&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod'
                   '&client=ssologin.js(v1.4.2)&_=%s' % self.GetMillTime())
        
        headers = self.GetHeaders()
        headers['Host'] = 'login.sina.com.cn'
        headers['Accept'] = '*/*'
        headers['Referer'] = 'http://weibo.com/'
        result = {}#定义一个字典
        del headers['Accept-encoding']
        
        request=self.pack_request(url, headers)
        for i in range(3):
            data=urllib2.urlopen(request).read()
            cp = re.compile('\((.*)\)')
            try:
                jsonData=cp.search(data).group(1)
                data=json.loads(jsonData)
                
                result["servertime"] = str(data['servertime'])
                result["nonce"] = data['nonce']
                result["rsakv"] = str(data['rsakv'])
                result["pubkey"] = str(data['pubkey'])
                self.pcid = str(data['pcid'])
                break
            except:
                logger.error(u'获取服务器时间出错！')
                continue
        return result
                
    def GetGlobalId(self):
        #获取新浪会话ID
        url="http://beacon.sina.com.cn/a.gif"    
        headers=self.GetHeaders()
        headers['Host'] = 'beacon.sina.com.cn'
        headers['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
        headers['Referer'] = 'http://weibo.com/'
        request = self.pack_request(url, headers)
        urllib2.urlopen(request) 
        print ".........get global id ok"
        
    def GetRandomNonce(self,rangeNum=6):
        #获取nonce随机值
        nonce=""
        for i in range(rangeNum):  
            nonce += random.choice('QWERTYUIOPASDFGHJKLZXCVBNM1234567890')
        return nonce
    
    def dec2hex(self,stringNum):
        #rsa 加密算法
        base = [str(x) for x in range(10)] + [chr(x) for x in range(ord('A'), ord('A')+6)]
        number = int(stringNum)
        mid = []
        while True:
            if number == 0: break
            number, rem = divmod(number, 16)
            mid.append(base[rem])
        return ''.join([str(x) for x in mid[::-1]])
    
    def GetPassword(self,password,servertime,nonce):
        #得到加密后的密码
        pkey=int(self.pubkey, 16)
        pub_key  = rsa.PublicKey(pkey, int('10001', 16))
        password = '%s\t%s\n%s' % (servertime, nonce, password)
        password =  (self.dec2hex(transform.bytes2int(rsa.encrypt(password.encode('utf-8'), pub_key))))
        return password

    def GetUser(self,username):
        #得到加密后的用户名
        username_ = urllib.quote(username)
        username = base64.encodestring(username_)[:-1]
        return username

    def SaveVerifyCode(self,url):
        #保存验证码
        try:
            cookieText = ""
            for cookie in self.cookJar.as_lwp_str(True, True).split("\n"):
                cookie = cookie.split(";")[0]
                cookie = cookie.replace("\"", "").replace("Set-Cookie3: ", " ").strip() + ";"
                cookieText += cookie
            headers = {'Host': 'login.sina.com.cn',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                       'Accept': 'image/png,image/*;q=0.8,*/*;q=0.5',
                       'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Connection': 'keep-alive',
                       'Referer'  :  'http://weibo.com/',
                       'Cookie'  :  cookieText,
                      }
            request = self.pack_request(url, headers)
            response = urllib2.urlopen(request, timeout=10)
            content = response.read()
            filename=open(os.path.join(self.softPath, "pin.png"), "wb")
            filename.write(content)
            filename.flush()
            filename.close()
        except:
            logger.error(u"保存验证码出错！.")
   
    def Login(self,loginUname,loginPasword):
        if loginUname is None or loginPasword is None:
            loginUname = modelsetting.LOGINNAME
            loginPasword  = modelsetting.LOGINPASSWOR
        
        assert(loginUname is not None and loginPasword is not None)
        #确保用户名密码不为空
        
        loginFalg=False#登录状态
        try:
            try:
                servertimeObj=self.GetServerTime()
                self.servertime=servertimeObj.get("servertime")
                self.rsakv = servertimeObj.get("rsakv")
                self.nonce = servertimeObj.get("nonce")
                self.pubkey = servertimeObj.get("pubkey")
                #登录必须的四个,主要是对本地明文密码进行加密
            except:
                return False
            print ".............get the servertime ok!..."
            #获取新浪会话ID
            self.GetGlobalId()
            
            try:
                loginHtml = self.doLogin(loginUname, loginPasword)
                loginHtml = loginHtml.replace('"', "'")
                cp=re.compile('location\.replace\(\'(.*?)\'\)')
                loginUrl= cp.search(loginHtml).group(1)
                if "retcode=0" in loginHtml:
                    print ".......retcode=0"
                    return self.reDoLogin(loginUrl)
                #是否需要手动输入验证码
                if settings.VERIFY_INPUT_FLAG:
                    logger.info(u"允许用户手动输入验证码.")
                    pass
                else:
                    logger.error(u"不允许输入验证码 ！.")
                    return False
                #需要验证码
                if "retcode=5" in loginHtml:
                    logger.error(u"需要验证码，请重新登录.")
                    return False
                if "retcode=4040" in loginHtml:
                    logger.error(u"登录频繁！.")
                    return False
                #需要验证码：code 4049
                if "retcode=4049" in loginUrl:
                    print ".....login 需要验证码！"
                    for i in range(3):
                        logger.info(u"需要验证码.")
                        verifycode_url = 'http://login.sina.com.cn/cgi/pin.php?r=%s&s=0&p=%s' % (random.randint(20000000,99999999), self.pcid)
                        self.SaveVerifyCode(verifycode_url)
                        settings.VERIFY_CODE = ""
                        codeImg = os.path.join(os.path.join(settings.PATH, settings.FILE_PATH_DEFAULT), "pin.png")
                        logger.info(u"验证码图片路径:%s." % codeImg)
                        try:
                            window = self.window
                            wx.CallAfter(window.ShowVerifyCode, codeImg)
                            #暂停线程，附加验证码之后再开启线程继续登录
                            print "before self.acquire"
                            genthread = modelsetting.MAIN_GENTHREAD
                            genthread.threadLock.acquire()
                            genthread.lockCondition.wait()
                            genthread.threadLock.release()
                            print "after self.release"
#                             veroifyFrame = VerifyCodeFrame(window, filename=codeImg)
#                             veroifyFrame.Center()
#                             veroifyFrame.Show(True)
                        except:
                            s = sys.exc_info()
                            msg = (u"app error %s happened on line %d" % (s[1], s[2].tb_lineno))
                            logger.error(msg)
                            
                        #加验证码再次登录    
                        verifyCode = settings.VERIFY_CODE
                        logger.info(u"get input verify code:%s" % verifyCode)
                        self.nonce = self.GetRandomNonce()
                        loginHtml = self.doLogin(loginUname, loginPasword, door=verifyCode)
                        loginHtml = loginHtml.replace('"', "'")
                        cp = re.compile('location\.replace\(\'(.*?)\'\)')
                        if cp.search(loginHtml):
                            loginUrl = cp.search(loginHtml).group(1)
                            return self.reDoLogin(loginUrl)
                        else:
                            if "retcode=2070" in loginHtml:
                                logger.error(u"验证码:%s 错误." % verifyCode)
                                continue
                            else:
                                break
    
            except:
                s = sys.exc_info()
                msg = (u"do login %s happened on line %d" % (s[1], s[2].tb_lineno))
                logger.error(msg)
                loginFalg = False
        except Exception:
            s = sys.exc_info()
            msg = (u"login: %s happened on line %d" % (s[1], s[2].tb_lineno))
            logger.error(msg)
        print loginFalg
        return loginFalg 
         
    
    
    def reDoLogin(self,loginUrl):
        print "......redologin"
        try:
            headers = self.GetHeaders()
            headers['Referer'] = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.2)'
            request = self.pack_request(loginUrl, headers)
            urllib2.urlopen(request)
            self.cookJar.save(self.cookieFile, True, True)
            logger.info(u'redologin登陆成功！')
            loginFalg = True
            print "...........登录成功.........."
        except:
            s = sys.exc_info()
            msg = (u"redo_login %s happened on line %d" % (s[1], s[2].tb_lineno))
            logger.error(msg)
            loginFalg = False
        return loginFalg
        
        
        
    def doLogin(self,loginUname,loginPasword,door=""):
        print  "..........dologin..."
        loginFalg=False
        try:
            username=loginUname
            password=loginPasword
            url='http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.2)'
            #通过filefocuse 抓包得到
            postdata = {
#                    'su': '',
#                    'servertime': '',
#                    'nonce': '',
#                    'pwencode': 'wsse',
#                    'sp': '',
                    'entry': 'weibo',
                    'gateway': '1',
                    'from': '',
                    'savestate': '7',
                    'userticket': '1',
                    'pagerefer' : '',
                    'ssosimplelogin': '1',
                    'vsnf': '1',
                    'vsnval': '',
                    'service': 'miniblog',
                    'pwencode': 'rsa2',
                    'rsakv' : self.rsakv,
                    'encoding': 'UTF-8',
                    'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
                    'returntype': 'META',
                    'prelt' : '26',
                }
            postdata['nonce']=self.nonce
            postdata['servertime']=self.servertime
            postdata['su']=self.GetUser(username)#加密后的用户名
            postdata['sp']=self.GetPassword(password, self.servertime, self.nonce).lower()#加密后的密码
            #如果需要验证码登录
            if door:
                postdata['pcid'] = self.pcid
                postdata['door'] = door.lower()
                
            headers = {'Host': 'login.sina.com.cn',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0',
                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-encoding': 'gzip, deflate',
                       'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Connection': 'keep-alive',
                       'Referer'  :  'http://weibo.com/',
                       'Content-Type': 'application/x-www-form-urlencoded',
                      }
            
            request = self.pack_request(url, headers, postdata)
            result = urllib2.urlopen(request)
            if result.info().get("Content-Encoding") == 'gzip':
                text = self.gzipData(result.read())
            else:
                text = result.read()
            return text
        except:
            s = sys.exc_info()
            msg = (u"do_login: %s happened on line %d" % (s[1], s[2].tb_lineno))
            logger.error(msg)
        return loginFalg
            
        
    def gzipData(self,data):
        #从gzip获取数据
        if 0 == len(data):
            return data
        dataStream = StringIO.StringIO(data)
        data = gzip.GzipFile(fileobj=dataStream).read()
        return data
    
    def checkCookie(self,uname=None,pasword=None,softPath=None):
        print "check cookie!"
        if uname is None or pasword is None:
            uname = modelsetting.LOGINNAME
            pasword  = modelsetting.LOGINPASSWOR
        
        assert(uname is not None and pasword is not None)
        
        if softPath is None:
            softPath = self.softPath
            
        loginFalg = True #登录状态
        self.cookieFile=os.path.join(softPath,"cookie.dat")
        if os.path.exists(self.cookieFile):
            logger.info(u"cookie dat 文件已存在")
            print ".....check cookie  存在"
            
            if "Set-Cookie" not in open(self.cookieFile,'r').read():
                logger.info(u"但是没有有效的cookie")
                print "没有有效的cookie"
                
                loginFalg=self.Login(uname, pasword)
                
        else:
            print "没有cookie 文件 调用登录模块！"
            loginFalg = self.Login(uname, pasword)
            
        if loginFalg:
            #登陆成功的话，刷新cookie
            return self.ValidCookie()
        else:
            return False
        #当Html参数为空时，需在Login调用之后返回cookieText or false  
        
        
    def ValidCookie(self,html=""):
        #验证账号合法性？
        print ".....valid cookie"
        html = str(html)
        if not html:
            print "....not html"
            url='http://weibo.com/kaifulee'#李开复的微博地址
            headers = self.GetHeaders()
            print "...getheader"
            html = self.GetContentHead(url, headers=headers)
            return True #跳过验证合法性，注意其他地方是否调用此函数！！！！
        if not html:
            logger.error(u"请重新登录.")
            self.ClearCookieData(self.cookieFile) #清空cookie文件
            print " clear cookie"
            return False
        
        html = str(html)
        html = html.replace('"', "'")
        
        if "sinaSSOController" in html:
            cp = re.compile('location\.replace\(\'(.*?)\'\)')
            #p = re.compile('location\.replace\("(.*?)"\)')
            try:
                loginUrl = cp.search(html).group(1)
                headers = self.GetHeaders()
                headers['Host'] = 'account.weibo.com'
                request = self.pack_request(url=loginUrl, headers=headers)
                result = urllib2.urlopen(request)
                self.cookJar.save(self.cookieFile, True, True)
                if result.info().get("Content-Encoding") == 'gzip':
                    html = self.gzipData(result.read())
                else:
                    html = result.read()
            except:
                logger.error(u"重新登录失败")
                self.ClearCookieData(self.cookieFile)
                return False
            
        if "违反了新浪微博的安全检测规则" in html:
            logger.error(u"cookie 失败")
            self.ClearCookieData(self.cookieFile)
            return False
        elif "您的帐号存在异常" in html and "解除限制" in html:
            logger.error(u"账号被限制.")
            self.ClearCookieData(self.cookieFile)
            return False
        elif "$CONFIG['islogin'] = '0'" in html:
            logger.error(u"登录失败$CONFIG['islogin'] = '0'.")
            self.ClearCookieData(self.cookieFile)
            return False
        elif "$CONFIG['islogin']='1'" in html:
            print "..........validcookie success"
            logger.info(u"cookie 成功")
            self.cookJar.save(self.cookieFile, True, True)
            return True
        else:
            self.ClearCookieData(self.cookieFile)
            logger.error(u"登录失败ValidCookie.")
            return False
        
    def GetContentHead(self,url,headers={},data=None):
        #每一次抓取网页都需要先登录，所以在登录时需要存储登录信息到cookie，
        #这样在抓取其他网页时只需到cookie取登录信息
        contenthead=""
        try:
            #读取cookie文件
            if os.path.exists(self.cookieFile):
                self.cookJar.revert(self.cookieFile, True, True)
                self.cookieProcessor = urllib2.HTTPCookieProcessor(self.cookJar)
                self.opener = urllib2.build_opener(self.cookieProcessor, urllib2.HTTPHandler)
                urllib2.install_opener(self.opener)
            else:
                return ""
            self.connectionNum+=1
            
            request = self.pack_request(url=url, headers=headers, data=data)
            response = self.opener.open(request, timeout=10)
            
            if response.info().get("Content-Encoding") == 'gzip':
                #如果页面是压缩格式就解压页面
                contenthead = self.gzipData(response.read())
            else:
                contenthead = response.read()
        except urllib2.HTTPError, e:
            logger.info(e)
            return e.code
        except:
            s=sys.exc_info()
            msg = u"get_content Error %s happened on line %d" % (s[1], s[2].tb_lineno)
            logger.error(msg)
            contenthead = ""
        return contenthead    
    
    def GetContentCookie(self,Url,headers={},data=None): 
        contentCookie = ""
        try:
            request = self.pack_request(url=Url, headers=headers, data=data)
            opener = urllib2.build_opener(self.cookieProcessor)
            response = opener.open(request, timeout=10)
            if response.info().get("Content-Encoding") == 'gzip':
                contentCookie = self.gzipData(response.read())
            else:
                contentCookie = response.read()
        except:
            s=sys.exc_info()
            msg = u"get_content Error %s happened on line %d" % (s[1], s[2].tb_lineno)
            logger.error(msg)
            contentCookie = ""
        return contentCookie
    
    def ClearCookieData(self,dataPath):
        try:
            os.remove(dataPath)
        except:
            pass
        
    def pack_request(self, url="", headers={}, data=None):
        if data:
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            data = urllib.urlencode(data)
            #一般的HTML表单，data需要编码成标准形式,编码工作使用urllib的函数而非urllib2
            
        request = urllib2.Request(url=url, data=data,headers=headers )                         
        proxyip = self.proxyip
        if proxyip and "127.0.0.1" not in proxyip:
            if proxyip.startswith("http"):
                proxyip = proxyip.replace("http://", "")
            request.set_proxy(proxyip, "http")
        return request        
        
    def GetHeaders(self):
        #字典
        headers = {'Host': 'weibo.com',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-encoding': 'gzip, deflate',
                   'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                   'Connection': 'keep-alive',
                  }
        return headers
        
    ###
       
    def GetHtmlSource(self,url, headers={}, data={}, proxyip=""):
        print "--------GetHtmlSource"
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
            print response
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
#         self.userinfo['uid'] = uid
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
                print content
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
        print "............GetUserBasicData"
        #用户基本消息来自解析的手机版微博
        #自动存储到self.userinfo
        try:
            # import chardet
            # print chardet.detect(html)
            html = html.decode('unicode-escape').encode('utf-8')
            # print html
            # print chardet.detect(html)
            if '用户不存在哦!' in html:
                logger.error('GetUserBasicData用户不存在!')
                return False
            
            # open('prettydad.html','w').write(html)
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
                
                wx.CallAfter(self.window.WriteLogger, u"===================")
                msg = u"正在采集用户： %s,微博数：%s \t" % (self.userinfo['nickname'], self.userinfo['n_weibos'])
                wx.CallAfter(self.window.WriteLogger, msg)
                
                #获取用户微博页数
                maxPage = int((int(self.userinfo['n_weibos'])-1)/44)+1
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
        print self.userinfo
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
            
#     def GetUserWeibos(self,maxPage):        
#             queue=Queue(0)
#             fetcherUser = FetcherWeibos(result_queue=queue, thread_id=1, window=self.window, thread_num=self.threadNum, 
#                                  output_path=self.outPath, user=self.userinfo, max_page=maxPage, loginweb=settings.LOGINWEB)
#             fetcherUser.run()
#             msgList = []
#             try:
#                 for i in range(queue.qsize()): #@UnusedVariable
#                     msgList.extend(queue.get(block=False))
#             except Empty:
#                 pass # 微博信息复制完成
#             return msgList
#             
            
            
#         
# if __name__== '__main__':
#     app=wx.App()
#     frame =mainframe.MainFrame(parent=None, id= wx.NewId(), title=u'新浪微博爬虫', framesize=(550,700))
#     frame.CenterOnScreen()
#     frame.Show(True)
#     app.MainLoop()    
#             

if __name__ == '__main__':
    login = LoginSinaWeb()
    login.checkCookie(uname='XXXX@qq.com',pasword='XXXXXXXX')
        