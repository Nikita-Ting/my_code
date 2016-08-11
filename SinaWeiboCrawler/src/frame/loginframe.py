# encoding:utf-8

'''
created on 2014-4-9
this is the login frame of the crawler
part of src come from the Pameng
'''
import wx
import os
import sys
from crawlermodel import logo 
import wx.lib.agw.hyperlink as hl
import crawlermodel.settings as settings
from crawlermodel.configUser import ConfigUser
from crawlermodel.thread import LoginThread
# from sina.loginsinaweb import LoginSinaWeb 
import showverifycodeframe
from mainframe import MainFrame
from crawlermodel.startimg import StartImg

class LoginFrame(wx.Frame):
      
    def __init__(self,parent,id,title,framesize):
        try:
            wx.Frame.__init__(self,parent,id,title,size=framesize,
                              style=wx.DEFAULT_FRAME_STYLE^(wx.RESIZE_BORDER |wx.MAXIMIZE_BOX))
            self.createLoginPanel()
            self.SetIcon(logo.get_icon())
            
            
        except:
            s=sys.exc_info()
            msg = (u"Login frame Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            wx.MessageBox(msg)
          
    def createLoginPanel(self):
        try:
            loginPanel=wx.Panel(self)
            box=wx.StaticBox(loginPanel,-1,u"登录")
            boxsizer=wx.StaticBoxSizer(box,wx.VERTICAL)          
            self.config=ConfigUser(settings.PATH)
           
            unameLabel=wx.StaticText(loginPanel,-1,u"微博账号")
            passwordLabel=wx.StaticText(loginPanel,-1,u"微博密码")
            unameText=wx.TextCtrl(loginPanel,-1,self.config.GetConfig("loginUserName", "uName"),size=(200, -1))
            passwordText=wx.TextCtrl(loginPanel,-1,self.config.GetConfig("loginUserPassword", "password"),size=(200, -1),style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
            rememberPswCkBox = wx.CheckBox(loginPanel, -1, u"记住密码")
            
            inputSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
            inputSizer.Add(unameLabel, 0)
            inputSizer.Add(unameText, 2)
            inputSizer.Add(passwordLabel, 0)
            inputSizer.Add(passwordText, 2)
            inputSizer.Add((10,10), 0)
            inputSizer.Add(rememberPswCkBox, 2)
            
            
            boxsizer.Add(inputSizer,0,wx.TOP|wx.ALIGN_CENTER,10)
            
            submitBtn=wx.Button(loginPanel,label=u"登录",size=(100,35))
            cancelBtn=wx.Button(loginPanel,label=u"取消",size=(100,35))
            buttonSizer=wx.BoxSizer(wx.HORIZONTAL)
            buttonSizer.Add(submitBtn,1,wx.RIGHT,1)
            buttonSizer.Add(cancelBtn,1,wx.LEFT,1)
            
            self._hyper1 = hl.HyperLinkCtrl(loginPanel, wx.ID_ANY, u"  [实验室主页]访问:http://cins.swpu.edu.cn/  ",
                                            URL="http://cins.swpu.edu.cn/")
           
            
            border = wx.BoxSizer(wx.VERTICAL)
            border.Add((15,15), 0)
            border.Add(boxsizer, 2, wx.ALIGN_CENTER, 25)
            border.Add((15,15), 0)
            border.Add(buttonSizer, 1, wx.ALIGN_CENTER, 25)
            border.Add(self._hyper1, 1, wx.ALIGN_CENTER, 5)
            
            loginPanel.SetSizer(border)
            loginPanel.Fit()
            loginPanel.Enable()
            
            self.loginPanel = loginPanel
            
            self.Fit()
            border.SetSizeHints(self)
            
            self.unameText = unameText
            self.passwordText = passwordText
            self.submitBtn = submitBtn
            self.cancelBtn = cancelBtn
            self.rememberPswCkBox=rememberPswCkBox
            
            #事件绑定
            self.Bind(wx.EVT_CLOSE, self.Close)
            self.Bind(wx.EVT_BUTTON, self.StartLogin, submitBtn)
            self.Bind(wx.EVT_BUTTON, self.Cancel, cancelBtn)
            self.Bind(wx.EVT_TEXT_ENTER, self.KeyPress, passwordText)
            
        except Exception:
            s=sys.exc_info()
            msg=(u"Main Error '%s' happened on line %d" % (s[1],s[2].tb_lineno))
            wx.MessageBox(msg)
             
    def KeyPress(self,event):
        self.StartLogin(None)    
    
    def Close(self, event):
        self.Destroy()
        
    def StartLogin(self,event):
        try:
            username=self.unameText.GetValue().strip().encode('UTF-8')
            password=self.passwordText.GetValue().strip().encode('UTF-8')
            if username=="" or password=="":
                self.MessageBox(u"新浪账号或密码不能为空，请重试！",u"Warning",wx.ICON_WARNING)
                return False
            else:
                rememberPswCkBox=self.rememberPswCkBox.IsChecked()
                if rememberPswCkBox:#若用户选择记住密码
                    self.config.WriteConfig(uname=username,psw=password)
                else:
                    #保存登录用户名，下次登录时自动填写
                    self.config.WriteConfig(uname=username,psw=None)
                    
            self.loginWinStatus(False)
            thread=LoginThread(self,1,username,password)
            thread.start()
            thread.stop()
            #不用线程登录
#             loginSina=LoginSinaWeb(username=username,password=password,window=self)
#             if loginSina.checkCookie(username,password):
#                 loginSina.window=None
#                 settings.LOGINWEB=loginSina
#                 settings.LOGINNAME=username
#                 settings.LOGINPASSWOR=password
#                 self.Login(loginValid="ok")
#                 print "login success!"
#             else:
#                 self.MessageBox(u"用户名或密码有错,请重试!",u"Warning", wx.ICON_ERROR)


            
        except Exception:
            s=sys.exc_info()
            self.MessageBox(u"Main Error '%s' happened on line %d"% (s[1],s[2].tb_lineno),u"Warning",wx.ICON_WARNING)
          
            
    def ShowVerifyCode(self, filename=""):
        self.veroifyFrame = showverifycodeframe.VerifyCodeFrame(self, filename=filename)
        self.veroifyFrame.Center()
        self.loginWinStatus(False)
        self.veroifyFrame.Show(True)
        
    def Login(self,loginValid): 
        try:
            if loginValid=="ok":
                self.Destroy()#登陆成功，登录窗口关闭
                #添加启动图片
                wx.SplashScreen(StartImg.GetBitmap(), wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                                1000, None, -1)
                wx.Yield()
                #激活主窗口
                frame = MainFrame(parent=None, id= wx.NewId(), title=u'新浪微博爬虫', framesize=(500,700)) 
                self.SetIcon(logo.get_icon())
                frame.Center()
                frame.Show(True)
            elif loginValid == "versionError":
                self.MessageBox(u"采集器版本过低!",u"Warning", wx.ICON_ERROR)
            else:
                self.MessageBox(u"登录失败:%s" % loginValid,u"Warning", wx.ICON_ERROR)
        except Exception:
            s=sys.exc_info()
            msg = (u"Login Error %s happened on line %d" % (s[1],s[2].tb_lineno))
            wx.MessageBox(msg)
                  
            
    def loginWinStatus(self,statusFlag):
        if statusFlag:
            self.loginPanel.Enable()  
        else:
            self.loginPanel.Disable()      
     
    def MessageBox(self,message,caption,style):
        msgDialog=wx.MessageDialog(None,message,caption,wx.OK|style)
        msgDialog.ShowModal()
        msgDialog.Destroy()
         
    def Cancel(self,event):
        self.Destroy()    
    
if __name__== '__main__':
    app=wx.App()
    frame = LoginFrame(None, -1,u"新浪微博爬虫软件登录",(500,375))
    frame.CenterOnScreen()
    frame.Show(True)
#     wx.SplashScreen(StartImg.GetBitmap(), wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
#                                 1000, None, -1)
#     wx.Yield()
    app.MainLoop()
      
      
      
      
      
          
