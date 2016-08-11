# encoding:utf-8

'''
created on 2014-5-5
this is frame of crawler
to show the result of searching user
'''

import wx
import sys
import json
from wx import html
from crawlermodel import logfile 
from crawlermodel import settings
# from sina import settings as sinaSetting

logger=logfile.LogFile().getLogger('searchFrame')

class SearchResultFrame(wx.Frame):
    def __init__(self, parent, title ,usersData=None):
        wx.Frame.__init__(self, parent, -1, title, size=(600,500))
        self.parent = parent
        #self.CreateStatusBar()
        html = HtmlWindow(self, parent)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()
        html.SetRelatedFrame(self, self.GetTitle() + " -- %s") #关联HTML到框架
        #html.SetRelatedStatusBar(0) #关联HTML到状态栏
        htmlStr = self.ParseData2Html(usersData)
        wx.CallAfter(html.SetPage, htmlStr)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    
    def OnCloseWindow(self, event):
        wx.CallAfter(self.parent.MainPanelStatus, True)
        self.Destroy()
    
    def ParseData2Html(self, userData):
        htmlString = ""
        try:
            if not userData:
                htmlString = u"<h2>获取搜索结果失败</h2><hr/>请检查您的网络状态."
            else:
                if userData == "failure" or userData == "error":
                    htmlString = u"<h2>未搜索到结果</h2><hr/>您搜索的用户不存在."
                    logger.error(u'userdata failure or error')
                else:
                    resultObj = json.loads(userData)
                    flag = resultObj.get("fg", -1)
                    #初始化为-1，如果搜索没有发生错误则不会被赋值为4-failure或13error
                    if flag == -1:
                        userLst = resultObj.get("users", [])
                        htmlString = u"<h3>搜索结果:[点击头像选定采集用户]</h3><hr><div>"
                        for user in userLst:
                            sex = user['sex']
                            if sex == "m":
                                sex = "男"
                            elif sex == "f":
                                sex = "女"
                            htmlString += u'''<div><div><a href=\"%s\"><img src=\"%s\"></a>&nbsp;&nbsp;昵称： %s\t性别 ：%s\t<br>地区：%s\t%s</div><p>%s</p></div></div>
                            ''' % (user["uid"]+"_._"+user.get('nickname'), user.get('Imgurl').replace("/180/", "/50/"), user.get('nickname'), sex, user['addr'], user['num'], user['intro'])
                            htmlString += "<hr/>"
                        htmlString += u"</div>"
                    else:
                        htmlString = u"<h2>未搜索到结果</h2><hr/>您搜索的用户不存在or状态异常."
        except Exception:
            s=sys.exc_info()
            msg = (u"ParseData2Html Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(msg)
        return htmlString

class HtmlWindow(html.HtmlWindow):
    def __init__(self, parent, mainFrame):
        html.HtmlWindow.__init__(self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        self.parent = parent
        self.mainFrame = mainFrame
    
    def OnLinkClicked(self, linkInfor):
        #获得选中的用户ID
        infors =  linkInfor.GetHref().split("_._")
        if infors and len(infors)>=2:
            msg = u"选择了爬取用户 :%s" % infors[1]
            wx.CallAfter(self.mainFrame.WriteLogger, msg)
            settings.SEARCHUID["CRAWLERUID"] = [infors[0]]#给字典赋值
            wx.CallAfter(self.mainFrame.MainPanelStatus, True)
            logger.info(u"crawler the user:%s"%infors[1])
            logger.info(infors[0])
            self.parent.Destroy()
        else:
            msg = u"无效的链接 :%s" % str(infors)
            wx.CallAfter(self.mainFrame.WriteLogger, msg)

