# encoding:utf-8

'''
created on 2014-4-29
this is thread of crawler
include login and search
'''

import wx
import threading
import sys
import os
import json
import settings
import logfile
import configUser
from sina.loginsinaweb import LoginSinaWeb 
from lxml.html.soupparser import fromstring
from lxml.html import tostring
from sina import settings as sinaSetting

loggerLogin=logfile.LogFile().getLogger('Loginthread')
loggerSearch=logfile.LogFile().getLogger('searchUserThread') 

class LoginThread(threading.Thread):
    
    
    def __init__(self,window,threadNumber,username,password):
        threading.Thread.__init__(self)
        self.threadNumber=threadNumber
        self.window=window
        self.quitTime=threading.Event()
        self.quitTime.clear()
        self.username=username
        self.password=password
        self.userConfig=configUser.ConfigUser(settings.PATH)
        
        #锁
        self.threadLock=threading.Lock()
        self.lockCondition=threading.Condition(self.threadLock)
        
    def stop(self):
        self.quitTime.set()
        
    def run(self):
        print ".....login thread run"
        try:
            settings.LOGINNAME=self.username
            settings.LOGINPASSWOR=self.password
            #保存登录名和密码
            
            laginValid="ok" #登录状态
            if laginValid=="ok":
                settings.MAIN_WINDOW=self.window
                settings.MAIN_GENTHREAD=self
                filePath=os.path.join(settings.PATH,settings.FILE_PATH_DEFAULT)
                print ".....loginsinaweb "
                loginSina=LoginSinaWeb(softPath=filePath,window=settings.MAIN_WINDOW)
                print "login sina web"
                if loginSina.checkCookie(self.username,self.password,filePath):
                    loginValid = "ok"
                    print "login successloginSina.checkCookie!"
                else:
                    loginValid = "用户名或密码有错!"
                
            if loginValid == "ok":
                settings.LOGINWEB=loginSina
                settings.LOGINNAME=self.username
                settings.LOGINPASSWOR=self.password
                loggerLogin.info("用户:%s 登陆成功!" % self.username)
            wx.CallAfter(self.window.loginWinStatus, True)
            wx.CallAfter(self.window.Login, loginValid)
            return None
        except Exception:
            #self.ShowMessage(u"Exception:%s" % str(e), wx.ICON_INFORMATION)
            s=sys.exc_info()
            loggerLogin.error(u"Login thread %s happened on line %d" % 
                         (s[1],s[2].tb_lineno))




class SearchUserThread(threading.Thread):   
    
    def __init__(self,searchUser, window):
        threading.Thread.__init__(self)
        self.window=window
        self.quitTime=threading.Event()
        self.quitTime.clear()
        self.result = {}
        self.searchUser = searchUser
        self.sina = LoginSinaWeb()
        #在登陆模块存入的LoginSinaWeb对象
        print "init search thread success"
                    
    def run(self):
        try:
            wx.CallAfter(self.window.MainPanelStatus, False)
            searchResult = ""
            url = "http://s.weibo.com/user/%s&Refer=SUer_box" % (self.searchUser)
            #用户搜索页面信息
            headers = {'Host':'s.weibo.com',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Accept-Encoding':'gzip, deflate',
                       'Connection':'keep-alive',
                       'Referer':'http://s.weibo.com',
                       }
            contentHead = self.sina.GetContentHead(url, headers)
            if contentHead == "":
                loggerSearch.error(u"%s 失败:获取网页内容为空！" % self.id)
                searchResult = 'error'
            if not self.GetUserInfo(contentHead):
                self.result['fg'] = 4;
                searchResult = 'failure'
            else:
                searchResult = json.dumps(self.result).decode('unicode_escape') 
            #self.window.finishedCount += 1
        except Exception:
            self.result['fg'] = 13;
            searchResult = 'error'
            s=sys.exc_info()
            msg = (u"getSinaUserInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            loggerSearch.error(msg)
        finally:
            wx.CallAfter(self.window.MainPanelStatus, True)
            wx.CallAfter(self.window.ShowSearchResult, searchResult)        
            
 
    def GetUserInfo(self,html):
        try:
            if '搜索结果为空' in html:
                print (u'weibo用户不存在!')
                return False
            if '您当前访问的用户状态异常' in html:
                #print (u'weibo用户状态异常!')
                return False
            html = self.GetHtmlInfo(html, '{\"pid\":\"pl_user_feedList\"')
            root = fromstring(html)
            usersDivise = root.xpath("//div[@class='list_person clearfix']")
            if len(usersDivise) > 0:
                users = []
                for div in usersDivise:
#                     user = dict.fromkeys(sinaSetting.USER_KEY, '')
                    user={}#定义一个用户字典并初始化
                    div = tostring(div , encoding='utf-8')
                    div = fromstring(div)
                    try:
                        iu_node = div.xpath("//div[@class='person_pic']/a/img")[0]
                        user['Imgurl'] = iu_node.get("src")
                        user['nickname'] = div.xpath("//div[@class='person_detail']/p[@class='person_name']")[0].text_content()
                        user['uid'] = iu_node.get("uid")
                        
                        sex_node = div.xpath("//div[@class='person_detail']/p[@class='person_addr']/span[@class='male m_icon']")
                        sex = ''
                        if sex_node:
                            sex = sex_node[0].get('title')
                        user['sex'] = sex
                        addr_node = div.xpath("//div[@class='person_detail']/p[@class='person_addr']")
                        addr = ''
                        if addr_node:
                            addr = addr_node[0].text_content()
                        user['addr'] = addr
                        num_node = div.xpath("//div[@class='person_detail']/p[@class='person_num']")
                        num = ''
                        if num_node:
                            num = num_node[0].text_content()
                        user['num'] = num
                        intro_node = div.xpath("//div[@class='person_detail']/div[@class='person_info']")
                        intro = ''
                        if intro_node:
                            intro = intro_node[0].text_content()
                        user['intro'] = intro
                        users.append(user)
                    except:
                        pass
                self.result['users'] = users
            else:
                return False
        except Exception:
            s=sys.exc_info()
            msg = (u"GetUserInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            loggerSearch.error(msg)
            return False
        return True       
            
    def GetHtmlInfo(self,html,strXPath):
        try:
            repose = html.find(strXPath)
            if repose == -1:
                return ""
            strContent = html[repose:-1]
            repose = strContent.find("})</script>")
            if repose == -1:
                return ""
            strContent = strContent[0:repose+len('})</script>')]
            strContent = strContent[strContent.find("\"html\":\"")+8: -1-(len('})</script>'))]
            strContent = strContent.replace(r"\ /", "")
            strContent = strContent.replace(r"\n", "")
            strContent = strContent.replace(r"\t", "")
            strContent = strContent.replace(r"\/", "/")
            strContent = strContent.replace(r'\"', "'")
            strContent = strContent.decode('unicode_escape')
            if strContent:
                strContent = strContent.replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", "")
            else:
                return ""
        except Exception:
            s=sys.exc_info()
            msg = (u"GetHtmlInfo Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            loggerSearch.error(msg)
            return ""
        return strContent
            
            
            
            
            

