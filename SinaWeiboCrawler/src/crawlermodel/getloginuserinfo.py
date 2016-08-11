# encoding:utf-8

'''
created on 2014-5-6
this is a action to get the login user informatons 
part of src come from the Pameng
'''

import sys
import logfile

logger=logfile.LogFile().getLogger('run')

class GetLoginUser():
    
    def __init__(self,uid,loginweb):
        self.uid=uid
        self.loginweb=loginweb
        
    def GetLoginUserInfo(self):
        user={}
        url="http://weibo.com"
        try:
            headers={'Host':'weibo.com',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:13.0) Gecko/20100101 Firefox/13.0.1',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language':'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
                       'Accept-Encoding':'gzip, deflate',
                       'Connection':'keep-alive',}
            html=self.loginweb.GetContentHead(url,headers)
            if '用户不存在哦!' in html:
                logger.error(u'weibo用户不存在!')
                return None
            if '您当前访问的用户状态异常' in html:
                logger.error(u'weibo用户状态异常!')
                return None
            #获取登录用户基本信息
            if html:
                sindex = html.find("$CONFIG['uid']")
                uid = html[sindex: html.find("';", sindex)]  
                #uid
                user["uid"] = uid.replace("$CONFIG['uid']", '').replace('=', '').replace("'", '').strip()
                #nickname
                sindex = html.find("$CONFIG['nick']")
                nick = html[sindex: html.find("';", sindex)]
                user["nickname"] = nick.replace("$CONFIG['nick']", '').replace('=', '').replace("'", '').strip()
            else:
                return None
        except Exception:
            s=sys.exc_info()
            msg=(u"parse user basic info Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
            return None
        return user    
         
    def stop(self):
        self.quitTime.set()       
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
