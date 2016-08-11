# encoding:utf-8

'''
created on 2014-4-28
this is the main frame of the crawler
part of src come from the Pameng
'''

import os
import sys

import wx
from wx.lib import platebtn
from wx.lib.wordwrap import wordwrap

from crawlermodel import configUser
from crawlermodel import logfile
from crawlermodel import logo
from crawlermodel import settings
from sina import settings as sinaSettings
from crawlermodel.thread import SearchUserThread
from searchuserframe import  SearchResultFrame
from sina import loginsinaweb
from sina.fetcherUser import FetcherUser
from sina.startCrawlerThread import StartCrawlerThread


#test
logger=logfile.LogFile().getLogger('MainFrame')
#新建mainframe的日志文件

wildcard = "DAT files|*.dat|"     \
           "All files (*.*)|*.*"
           
           
class MainFrame(wx.Frame):
    
    def __init__(self,parent,id,title,framesize):
        try:
            wx.Frame.__init__(self,parent,id,title,size=framesize,
                              style=wx.DEFAULT_FRAME_STYLE^(wx.RESIZE_BORDER |wx.MAXIMIZE_BOX))
            
            self.SetIcon(logo.get_icon())#设置窗口图标为选定图标
            #窗口不能调整大小和最大化
            self.createMainPanel() 
            self.userConfig = configUser.ConfigUser(settings.PATH)
            #定义采集方式，0：multiple版，1：SEARCH版 ,2:weiboinfo版
            self.CRAWLER_TYPE = 1
            #定义采集状态：0未开始； 1正在采集
            self.CRAWLER_STATUS = 0
            #定义是否采集登录用户自己 0：不采集 1：采集
            self.CRAWLER_SELF = 0
            #定义工作路径和结果路径
            self.taskPath=os.path.join(settings.PATH,settings.FILE_PATH_DEFAULT)
            self.resultPath=""
            self.crawlerRunning=True#爬虫运行状态标识
            self.processBarValue=0#进度条的值
            self.crawlerCount=0#采集次数
            self.threads=[]#程序的线程池
            
            
            #绑定窗口的关闭事件
            self.Bind(wx.EVT_CLOSE, self.CloseWin)
#             self.Bind(wx.EVT_ICONIZE, self.OnMinimized)
                       
        except Exception:
            #self.ShowMessage(u"Exception:%s" % str(e), wx.ICON_INFORMATION)
            s=sys.exc_info()
            msg = (u"Main Error '%s' happened on line %d" % (s[1],s[2].tb_lineno))
            wx.MessageBox(msg)
            logger.error(u"Main Error:%s" % str(msg))
    
    def ReInit(self):
        self.finishedCount = 0
        self.curCount = 0
        self.totalCount = 0
        self.UpdateProcessBar(0)
        self.crawlerRunning = True
        self.processBarValue = 0
                
    def createMainPanel(self):
        try:
            mainPanel=wx.Panel(self)
            northSizer=self.createNorthPanel(mainPanel)
            savePathSizer=self.createSavePathPanel(mainPanel)
            centerSizer=self.createCenterPanel(mainPanel)
            southSizer=self.createSouthPanel(mainPanel)
            
            mainSizer=wx.BoxSizer(wx.VERTICAL)
            mainSizer.Add(northSizer,0,wx.ALL,5)
            #add的第四个参数指定边框宽度，第三个参数wx.ALL是一套标志中的一个，它控制那些边套用第四个
            #参数指定的边框宽度，wx.ALL表明对象的四个边都套用
            mainSizer.Add(wx.StaticLine(mainPanel),0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
            mainSizer.Add(savePathSizer,0,wx.ALL,5)
            mainSizer.Add(wx.StaticLine(mainPanel),0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
            mainSizer.Add(centerSizer,0,wx.ALL,5)
            mainSizer.Add(wx.StaticLine(mainPanel),0,wx.EXPAND|wx.TOP|wx.BOTTOM,5)
            mainSizer.Add(southSizer,0,wx.ALL,5)
            mainPanel.SetSizer(mainSizer)
            mainSizer.Fit(mainPanel)
            #参数是control panel，告诉panel调整自身尺寸以匹配sizer认为所需要的最小化尺寸。
            mainSizer.SetSizeHints(self)
            #Tell the sizer to set (and `Fit`) the minimal size of the *window* to match the sizer's minimal size.
           
            #页面布局初始化
            self.informationPanel.Show(False)
            self.userPanel.Show(True)
#             self.userContentPanel.Show(True)
#             self.webInforPanel.Show(False)     
                   
            self.mainPanel=mainPanel
            mainPanel.Enable() 
            currentUseer= settings.LOGINNAME
            self.WriteLogger(u"运行...")
            self.WriteLogger(u"当前登录用户：%s"%currentUseer)
            self.WriteLogger(u"当前采集器版本：%s"%settings.CRAWLER_VERSION)
            
        except Exception:
            s=sys.exc_info()
            msgs=(u"Main Error '%s' happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(u"Main Error:%s" % str(msgs))
            wx.MessageBox(msgs)
            
    def createNorthPanel(self,panel):  
        try:
            loginuser=settings.LOGINNAME#登录用户账户
            #创建头部画板部件
            versionLable=wx.StaticText(panel,-1,u" Version：1.1.2 ")
            userLable=wx.StaticText(panel,-1,u"用户账号：")
            userBtn=platebtn.PlateButton(panel,-1,loginuser,None)
            userBtn.SetToolTipString(u"登录用户账号名")
            helpBtn=platebtn.PlateButton(panel,-1,u"帮助？",None)
            
            #创建头部画板
            leftSizer=wx.BoxSizer(wx.HORIZONTAL)
            rightSizer=wx.BoxSizer(wx.HORIZONTAL)
            
            leftSizer.Add((5,5), 2)
            leftSizer.Add(userLable,0)
            leftSizer.Add(userBtn,0)
            rightSizer.Add(helpBtn,0)
            rightSizer.Add(versionLable,0)
            
            northSizer=wx.GridSizer(cols=2, hgap=10)
            #：FlexGridSizer是一个固定的二维网格，参数: rows 定义GridSizer 行数
            # cols  定义GridSizer 列数       vgap 定义垂直方向上行间距        hgap 定义水平方向上列间距
            northSizer.Add(leftSizer,1,wx.ALIGN_CENTER)
            northSizer.Add(rightSizer,1,wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
            
            #绑定按钮的单击事件 
            helpBtn.Bind(wx.EVT_BUTTON, self.ShowHelpInfo, helpBtn)
            
        except Exception:
            s=sys.exc_info()
            msg = (u"Main Error '%s' happened on line %d" % (s[1],s[2].tb_lineno))
            wx.MessageBox(msg)
        #    logger.error(u"Main Error:%s" % str(msg))
        return northSizer
            
    def createSavePathPanel(self,panel):   
        saveBtn=wx.Button(panel,label=u"选择结果路径",size=(100,35))
        saveBtn.SetToolTipString(u"程序运行目录<file>为默认结果保存路径")
        savePathDefault=os.path.join(settings.PATH,settings.FILE_PATH_DEFAULT)
        savePathText=wx.TextCtrl(panel,-1,savePathDefault,size=(300,-1))
        #自动填写默认路径
        savePathText.SetEditable(False)  
          
        #创建保存路径画板
        savePathSizer=wx.BoxSizer(wx.HORIZONTAL)
        savePathSizer.Add(saveBtn,0)  
        savePathSizer.Add((10,5),0, wx.EXPAND)
        savePathSizer.Add(savePathText, 1, wx.CENTER) 
        
        #绑定按钮的单击事件 
        saveBtn.Bind(wx.EVT_BUTTON, self.ShowSavePath, saveBtn)
        self.savePathText=savePathText
        self.saveBtn=saveBtn
        
        return savePathSizer
    
    def createCenterPanel(self,panel):
        try:
            
            #top left sizer button
            userBtn=wx.Button(panel,label=u"用户昵称/ID",size=(100,35))
            userBtn.SetToolTipString(u"请输入需要采集的用户的用户昵称或ID！")
            infoBtn=wx.Button(panel,label=u"微博URL",size=(100,35))
            infoBtn.SetToolTipString(u"请输入需要采集的微博的URL地址！")
            multCrawBtn=wx.Button(panel,label=u"批量采集",size=(100,35))
            multCrawBtn.SetToolTipString(u"请输入需要采集的用户ID列表，以英文\",\"(逗号)分割!可采集用户范围（2-20）")
            btnSizer=wx.BoxSizer(wx.VERTICAL)
            btnSizer.Add(userBtn,0)
            btnSizer.Add(infoBtn,0)
            btnSizer.Add(multCrawBtn,0)
            userBtn.Disable()
            infoBtn.Enable()
            multCrawBtn.Enable()
            self.userBtn=userBtn
            self.infoBtn=infoBtn
            self.multCrawBtn=multCrawBtn
            
            #top center part
            userPanel=wx.Panel(panel)#用户昵称、Id模块
            informationPanel=wx.Panel(panel)#指定微博消息模块
            multipleCrawlerPanel=wx.Panel(panel)#批量采集模块
            #search框
            userText=wx.SearchCtrl(userPanel,size=(300,-1),style=wx.TE_PROCESS_ENTER) 
            userInfoInputSizer=wx.BoxSizer(wx.HORIZONTAL)
            userInfoInputSizer.Add(userText,2)
            userPanel.SetSizer(userInfoInputSizer)
            self.userText=userText
            
            #指定微博消息URL输入框
            infoUrlText=wx.TextCtrl(informationPanel, -1, "" , size=(300, 70),
                             style = wx.TE_MULTILINE
                             #| wx.TE_RICH
                             | wx.TE_RICH2
                             )
            self.infoUrlText=infoUrlText
            infoUrlText.SetToolTipString(u"请输入微博URL")
            inforInputSizer=wx.BoxSizer(wx.HORIZONTAL)
            inforInputSizer.Add(infoUrlText,2)
            informationPanel.SetSizer(inforInputSizer)

            
            #批量采集用户ID输入框
#             uidsText = wx.TextCtrl(multipleCrawlerPanel, -1, "" , size=(300, 70),
#                              style = wx.TE_MULTILINE
#                              #| wx.TE_RICH
#                              | wx.TE_RICH2
#                              )
#             self.uidsText=uidsText
#             multiInputSizer=wx.BoxSizer(wx.HORIZONTAL)
#             multiInputSizer.Add(uidsText,2)
#             multipleCrawlerPanel.SetSizer(multiInputSizer)
#             multipleCrawlerPanel.Show(False)
            
            #输入模块整合
            inputSizer=wx.BoxSizer(wx.VERTICAL)
            inputSizer.Add((5,5), 0)
            inputSizer.Add(userPanel, 0)
            inputSizer.Add(informationPanel, 0)
#             inputSizer.Add(multipleCrawlerPanel, 0)
            
            
            self.userPanel=userPanel
            self.informationPanel=informationPanel
            self.multipleCrawlerPanel=multipleCrawlerPanel
            self.inputSizer=inputSizer
            
            #box for crawler content  
            userContentPanel=wx.Panel(panel)#采集指定用户的指定内容
            webInforPanel=wx.Panel(panel)  #采集指定微博的指定内容            
            
            contentBtn=platebtn.PlateButton(userContentPanel,-1,u"采集内容：",None)
            contentBtn.SetToolTipString(u"请选择要采集的内容")
            crawSelfCkBox = wx.CheckBox(userContentPanel, -1, u"采集自己")
#             crawSelfCkBox.SetValue(True)
            followsCkBox = wx.CheckBox(userContentPanel, -1, u"关注列表")
            followsCkBox.SetValue(True)
            fansCkBox = wx.CheckBox(userContentPanel, -1, u"粉丝列表")
            fansCkBox.SetValue(True)
            weibosCkBox = wx.CheckBox(userContentPanel, -1, u"微博消息")
            weibosCkBox.SetValue(True)
            userContentSizer=wx.BoxSizer(wx.HORIZONTAL)
            userContentSizer.Add(contentBtn,0)
            userContentSizer.Add((20,20),0, wx.EXPAND)
            userContentSizer.Add(crawSelfCkBox,0)
            userContentSizer.Add(followsCkBox,0)
            userContentSizer.Add(fansCkBox,0)
            userContentSizer.Add(weibosCkBox,0)
            userContentPanel.SetSizer(userContentSizer)
#             userContentPanel.Show(True)
            self.crawSelfCkBox=crawSelfCkBox
            self.followsCkBox=followsCkBox
            self.fansCkBox=fansCkBox
            self.weibosCkBox=weibosCkBox          
            
            contentBtn=platebtn.PlateButton(webInforPanel,-1,u"采集内容：",None)
            contentBtn.SetToolTipString(u"请选择要采集的内容")
            commentCkBox = wx.CheckBox(webInforPanel, -1, u"评论信息")
            forwardCkBox = wx.CheckBox(webInforPanel, -1, u"转发信息")
            webInfoContentSizer=wx.BoxSizer(wx.HORIZONTAL)
            webInfoContentSizer.Add(contentBtn,0)
            webInfoContentSizer.Add((20,20),0, wx.EXPAND)
            webInfoContentSizer.Add(commentCkBox,0)
            webInfoContentSizer.Add(forwardCkBox,0)
            webInforPanel.SetSizer(webInfoContentSizer)
            webInforPanel.Show(False)
            self.commentCkBox=commentCkBox
            self.forwardCkBox=forwardCkBox
            
            #内容模块整合
            choseSizer=wx.BoxSizer(wx.VERTICAL)
            choseSizer.Add(userContentPanel, 0)
            choseSizer.Add(webInforPanel,0)
            
            contentSizer=wx.BoxSizer(wx.HORIZONTAL)
#             contentSizer.Add(contentBtn,0)  
#             contentSizer.Add((10,5),0, wx.EXPAND)
            contentSizer.Add(choseSizer, 0) 
            
            self.userContentPanel=userContentPanel
            self.webInforPanel=webInforPanel
            self.contentSizer=contentSizer
            self.choseSizer=choseSizer
            
            
            #进度条
            box=wx.StaticBox(panel,-1,u"采集进度")
            #采集当前进度/总请求次数，初始0
            self.finishedCount = 0
            self.curCount = 0
            self.totalCount = 0
            
            processBar=wx.Gauge(panel,-1,100,(20,50),(300,35))
            processBar.SetBezelFace(3)
            processBar.SetShadowWidth(3)
            crawlerBtn = wx.Button(panel, label=u"开始采集")
            boxSizer = wx.StaticBoxSizer(box, wx.HORIZONTAL)
            boxSizer.Add(processBar, 0, wx.TOP|wx.LEFT, 1)
            boxSizer.Add((40, 40), 0)
            boxSizer.Add(crawlerBtn,0)   
#             bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
#             bottomSizer.Add(boxSizer, 0)
#             bottomSizer.Add((10, 10), 0)
#             bottomSizer.Add(crawlerBtn, 0,wx.BOTTOM|wx.RIGHT)
            

            self.processBar = processBar
            self.crawlerBtn=crawlerBtn
            
            #top part整合;按钮+输入框+搜索按钮
            searchBtn = wx.Button(panel, label=u" 搜索 ",size=(100, 30))
            topSizer=wx.BoxSizer(wx.HORIZONTAL)
            topSizer.Add(btnSizer, 0)
            topSizer.Add((10,5), 0)
            topSizer.Add(inputSizer, 0)
            topSizer.Add((10,5), 0)
            topSizer.Add(searchBtn, 0)
            self.searchBtn=searchBtn
            
            centerSizer=wx.BoxSizer(wx.VERTICAL)
            centerSizer.Add(topSizer,1,wx.EXPAND)
            centerSizer.Add((10,10), 0, wx.EXPAND)
            centerSizer.Add(contentSizer, 0, wx.EXPAND)
            centerSizer.Add((10,10), 0, wx.EXPAND)
            centerSizer.Add(boxSizer, 0, wx.EXPAND)
            self.centerSizer=centerSizer
            
            #事件绑定
            self.Bind(wx.EVT_BUTTON,self.OnUserBtnClick,userBtn)
            self.Bind(wx.EVT_BUTTON,self.OnInfoBtnClick,infoBtn)
            self.Bind(wx.EVT_BUTTON,self.OnMultCrawBtnClick,multCrawBtn)
            searchBtn.Bind(wx.EVT_BUTTON, self.StartSearchUser, searchBtn)
            self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.StartSearchUser, self.userText)
            self.Bind(wx.EVT_TEXT_ENTER, self.StartSearchUser, self.userText)
            crawlerBtn.Bind(wx.EVT_BUTTON, self.StartCrawler, crawlerBtn)
            #复选框选中事件
            self.Bind(wx.EVT_CHECKBOX, self.OnCrawlSelfCheckBox, crawSelfCkBox)
            
        except Exception:
            s=sys.exc_info()
            msg = (u"createCenterPanel Error '%s' happened on line %d" % (s[1],s[2].tb_lineno))
            logger.error(u"createCenterPanel Error:%s" % str(msg))
        return centerSizer

    def createSouthPanel(self,panel):  
        #日志框 
        clearBtn = platebtn.PlateButton(panel, -1, u"清空日志", None)
        logText = wx.TextCtrl(panel, -1, "" , size=(550, 300),
                         style = wx.TE_MULTILINE
                         #| wx.TE_RICH
                         | wx.TE_RICH2
                         )
        logText.SetEditable(False)
        self.logText = logText
        southSizer = wx.BoxSizer(wx.VERTICAL)
        southSizer.Add(clearBtn, 0)
        southSizer.Add(logText, 0)        
       
        #事件绑定
        clearBtn.Bind(wx.EVT_BUTTON, self.ClearLogger, clearBtn)
        return southSizer

    def ShowHelpInfo(self,event):
        #首先创建一个About窗口
        helpInfo = wx.AboutDialogInfo()
        helpInfo.Name = "新浪爬虫软件"
        helpInfo.SetIcon(logo.get_icon())
        helpInfo.Version = settings.CRAWLER_VERSION
        helpInfo.Copyright = settings.COPYRIGHT
        helpInfo.Description = wordwrap(settings.CRAWLER_HELP_DOC, 400, wx.ClientDC(self))
        
        helpInfo.WebSite = (settings.HOME_PAGE, "实验室主页")
        helpInfo.Developers =settings.DEVELOPERS
        helpInfo.Licence = settings.LICENCE
        wx.AboutBox(helpInfo)
    
    def OnMinimized(self,event):
        #An EVT_ICONIZE event is sent when a frame is iconized (minimized) or restored
        self.Hide()
        event.Skip()
            
    def ShowSavePath(self,event):
        dialog = wx.DirDialog(self, u"请选择保存数据的路径",
                           style=wx.DD_DEFAULT_STYLE
                           #| wx.DD_DIR_MUST_EXIST
                           #| wx.DD_CHANGE_DIR
                           )
        if dialog.ShowModal() == wx.ID_OK:
            self.resultPath = dialog.GetPath()
            self.WriteLogger(u"爬取数据文件保存路径: %s" % (self.resultPath))
            self.savePathText.SetValue(self.resultPath)
        dialog.Destroy()
       
    def OnUserBtnClick(self,event):
        self.userContentPanel.Show(True)
        self.webInforPanel.Show(False)
        self.choseSizer.Detach(self.webInforPanel)
        self.choseSizer.Layout()
        self.CRAWLER_TYPE = 1
        #self.OnSearch(None)
        self.userBtn.Disable()
        self.searchBtn.Enable()
        #清空输入框
        self.userText.SetValue("")
        self.infoUrlText.SetValue("")
        self.searchBtn.LabelText="搜索"
        self.infoBtn.Enable()
        self.multCrawBtn.Enable()
        self.informationPanel.Show(False)
#         self.multipleCrawlerPanel.Show(False)
        self.userPanel.Show(True)
        #Detaches an item from the sizer without destroying it.
        self.inputSizer.Detach(self.informationPanel)
#         self.inputSizer.Detach(self.multipleCrawlerPanel)
        self.inputSizer.Layout()
      
    def OnInfoBtnClick(self,event):
        self.webInforPanel.Show(True)
        self.userContentPanel.Show(False)
        self.choseSizer.Detach(self.userContentPanel)
        self.choseSizer.Layout()
        self.CRAWLER_TYPE = 2
        #self.OnSearch(None)
        #清空输入框
        self.userText.SetValue("")
        self.infoUrlText.SetValue("")
        self.searchBtn.Disable()
        self.userBtn.Enable()
        self.infoBtn.Disable()
        self.multCrawBtn.Enable()
        self.informationPanel.Show(True)
#         self.multipleCrawlerPanel.Show(False)
        self.userPanel.Show(False)
        
        self.inputSizer.Detach(self.userPanel)
#         self.inputSizer.Detach(self.multipleCrawlerPanel)
        self.inputSizer.Layout()  
        
    def OnMultCrawBtnClick(self,event):
        self.userContentPanel.Show(True)
        self.webInforPanel.Show(False)
        self.choseSizer.Detach(self.webInforPanel)
        self.choseSizer.Layout()
        self.CRAWLER_TYPE = 0
        #self.OnSearch(None)
        #清空输入框
        self.userText.SetValue("")
        self.infoUrlText.SetValue("")
        self.userBtn.Enable()
        self.infoBtn.Enable()
        self.multCrawBtn.Disable()
        self.informationPanel.Show(True)
#         self.multipleCrawlerPanel.Show(True)
        self.userPanel.Show(False)
        
#         self.inputSizer.Detach(self.informationPanel)
        self.inputSizer.Detach(self.userPanel)
        self.inputSizer.Layout()  
    
    def StartSearchUser(self,event):
        searchUser = self.userText.GetValue().strip().encode("utf-8")
        if searchUser == "":
            self.MessageBox(u"请输入用户昵称或者用户ID搜索!")
        else:
#            if str.isdigit(nickname):
#                print "ID"
#            else:
#                print "nickname"
            userSearch = SearchUserThread(searchUser, self)
            userSearch.start()
            userSearch.join()
    
    def ShowSearchResult(self,searchResult):
        self.searchFrame = SearchResultFrame(self, u"新浪用户搜索结果", searchResult)
        self.searchFrame.Center()
        self.MainPanelStatus(False)
        self.searchFrame.Show(True)
    
    def StartCrawler(self,event):
#         settings.SEARCHUID["CRAWLERUID"]=['1970889791']
        self.crawlerCount+=1
        CrawlerContent=dict.fromkeys(sinaSettings.CrawlerContent, False)
        if self.followsCkBox.IsChecked():
            CrawlerContent["cwlFollows"]=True
        if self.fansCkBox.IsChecked():
            CrawlerContent["cwlFans"]=True
        if self.weibosCkBox.IsChecked():
            CrawlerContent["cwlWeibos"]=True
        if self.commentCkBox.IsChecked():
            CrawlerContent["cwlComment"]=True
        if self.forwardCkBox.IsChecked():
            CrawlerContent["cwlForward"]=True
        sinaSettings.CrawlerContent=CrawlerContent
        try:
            if self.CRAWLER_SELF:
                self.WriteLogger(u"采集当前登录用户-----")
            if self.CRAWLER_TYPE == 0:#批量采集
                uids = str(self.infoUrlText.GetValue().strip())
                if "," not in uids:
                    wx.MessageBox(u"没有找到用逗号分隔开的批量采集用户ID.",u"Warning")
                    return False
                else:
                    uidList =  uids.split(",")
                    if len(uidList) > 20:
                        wx.MessageBox(u"批量采集的范围最多为20个用户!",u"Warning")
                        return False
                    else:
                        for uid in uidList:
                            if not uid:
                                uidList.remove(uid)
                        settings.SEARCHUID["CRAWLERUID"] = uidList
            if self.CRAWLER_TYPE == 2:#采集指定微博消息    
                weiboUrl = str(self.infoUrlText.GetValue().strip())
                if weiboUrl.startswith('http://weibo.com/'):
                    if not sinaSettings.CrawlerContent["cwlComment"] and not sinaSettings.CrawlerContent["cwlForward"]:
                        wx.MessageBox(u"请选择要采集的内容!",u"Warning")
                        return False
                    settings.WeiboUrl=weiboUrl
                else:
                    wx.MessageBox(u"请输入正确的微博地址!",u"Warning")
                    return False                        
                        
            if not self.CRAWLER_SELF and not settings.SEARCHUID.get("CRAWLERUID", None) and not settings.WeiboUrl:
                wx.MessageBox(u"请先输入要采集的用户或者微博地址!",u"Warning")
                return False
            else:
                self.UpdateBtnLabel(u"停止采集")
                self.UpdateButStatus(True)
                self.WriteLogger(u"验证中-----")
                self.UpdateProcessBar(2)#更新进度条
                startThread = StartCrawlerThread(1, self, event)
                startThread.start()
                startThread.stop()
                
        except Exception:
            s=sys.exc_info()
            msg = (u"Exception %s happened on line %d" % (s[1],s[2].tb_lineno))
            wx.MessageBox(msg,u"Warning")
            logger.error(msg)
            self.WriteLogger(msg)
    
    def UpdateButStatus(self, flag):
        #采集进程开始，则不能执行其他操作
        if flag:
            self.saveBtn.Disable()
            self.userBtn.Disable()
            self.infoBtn.Disable()
            self.searchBtn.Disable()
            self.multCrawBtn.Disable()
            self.userText.Disable()
            self.infoUrlText.Disable()
        else:
            self.saveBtn.Enable()
            self.searchBtn.Enable() 
            self.infoBtn.Disable()
            self.multCrawBtn.Enable()
            self.crawSelfCkBox.SetValue(False)
            self.userText.Enable()
            self.infoUrlText.Enable()
           
     
    def UpdateProcessBar(self,processValue):      
        self.processBar.SetValue(processValue) 
    
    def UpdateBtnLabel(self, labelStr):
        self.crawlerBtn.SetLabel(labelStr)
         
    def StopCrawler(self,event):
        if self.ConfirmWin(u"正在采集数据，确定要终止采集吗?(当前采集的数据会丢失!!)")== wx.ID_YES:
            self.WriteLogger(u"用户执行了停止采集操作！")
            self.WriteLogger(u"正在结束线程--------")
            self.crawlerRunning=False  
            self.UpdateBtnLabel(u"开始采集")
            self.UpdateButStatus(False) 
            self.UpdateProcessBar(0)#更新进度条
            self.CRAWLER_STATUS = 0#？or1#采集状态为0
            self.StopThread()
                  
    def ThreadFinished(self,thread):
        #删除该线程
        try:
            self.threads.remove(thread)
            self.CRAWLER_STATUS=0
        except Exception:
            logger.error(u"线程被终止，采集结束！")
            self.WriteLogger(u"线程被终止,采集结束!")
            
#         self.UpdateProcessBar(0)#更新进度条    
            
    def StopThread(self):
        while self.threads:
            thread=self.threads[0]   
            thread.stop()
            self.threads.remove(thread) 
        
           
    def OnCrawlSelfCheckBox(self, event):
        status = event.IsChecked()
        self.CRAWLER_SELF = status
        
        
    def CloseWin(self,event):
        if self.ConfirmWin(u'你确定要退出吗?请保存数据!') == wx.ID_YES:
#             self.taskBarIcon.Destroy()
            self.Destroy()
    
    def ConfirmWin(self,message):
        dialog= wx.MessageDialog(self, message,
                      '系统提示', wx.YES_NO | wx.ICON_EXCLAMATION)
        dlgModal = dialog.ShowModal()
        dialog.Destroy()
        return dlgModal

    def MessageBox(self, message):
        msgDlg = wx.MessageDialog(self, message,
                               '系统提示',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        msgDlg.ShowModal()
        msgDlg.Destroy()
    
    def SetProcessBarRange(self,value):
        self.processBarValue=value
        self.processBar.SetRange(value+27)
        
        
        
    def MainPanelStatus(self,status):
        if status:
            self.mainPanel.Enable()
        else:
            self.mainPanel.Disable()
        
    def WriteLogger(self, logger):
        rows = self.logText.GetNumberOfLines()
        #日志最多显示400行
        if rows > 400:
            self.logText.Clear()
        lastPosition = self.logText.GetLastPosition()
        self.logText.SetInsertionPoint(lastPosition)
        self.logText.WriteText(logger+"\n")
    
    def ClearLogger(self, event):
        self.logText.Clear()            
      
    def testuser(self):
        import time       
#         fetcherUser=FetcherUser(self,1,"")
        fetcherUser = loginsinaweb.LoginSinaWeb()
        fetcherUser.Login('ssh2222@qq.com', '2222ssh')
        userId="1970889791"
        now = time.time()
        nowTime = str(time.time()).replace(".", "")
        taskInfo={}
        taskInfo["gsid"]=['gsid']
        gsid=taskInfo.get("gsid")[0]
        userIndexUrl = "http://m.weibo.cn/home/homeData?hideAvanta=1&u=%s&page=1&&_=%s" % (userId, nowTime)
        userInfoUrl = "http://m.weibo.cn/setting/userInfoSetting?uid=%s&st=569d&" % (userId)
        
        #采集详细信息
        content =fetcherUser.GetHtmlData(userInfoUrl, userId, gsid, "http://m.weibo.cn/users/%s?" % userId, '')
        infoStatus = fetcherUser.GetUserDetailData(content)
        print infoStatus  
        #采集基本信息
        content =fetcherUser.GetHtmlData(userIndexUrl, userId, gsid, "http://m.weibo.cn/u/%s?" % userId, '')
        if content == "":
            msg = u"用户： %s 采集失败(返回用户信息为空！)" % userId
            logger.error(msg)
            wx.CallAfter(frame.WriteLogger, msg)
                    
        if not fetcherUser.GetUserBasicData(content):
            wx.CallAfter(frame.WriteLogger, u"===================")
            msg = u"无效的用户ID：%s." % (userId)
            wx.CallAfter(frame.WriteLogger, msg) 
        # print content.decode('gbk').encode('utf-8')

if __name__== '__main__':
    app=wx.App()
    frame = MainFrame(parent=None, id= wx.NewId(), title=u'新浪微博爬虫', framesize=(550,700))
    frame.CenterOnScreen()
    frame.Show(True)
    fetcherUesr=FetcherUser(frame,1,"C:\Python27\file")
    fetcherUesr.GetUserWeibos(8)
    frame.testuser()
    app.MainLoop()
    
    
        
                 
            
            
            