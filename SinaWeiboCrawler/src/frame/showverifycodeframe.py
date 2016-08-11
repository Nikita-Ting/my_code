# encoding:utf-8

'''
created on 2014-4-29
this is part of crawler
show verifycodeImg
'''



import wx
import sys
from crawlermodel import settings
from sina import settings as sinasettings

class VerifyCodeFrame(wx.Frame):
    
    def __init__(self, parent, filename="pin.png"):
        try:
            wx.Frame.__init__(self, parent, title="请输入验证码")
            self.mainFrame = parent
            panel = wx.Panel(self)
            fgBoxsizer = wx.FlexGridSizer(cols=3, hgap=10, vgap=10)
            # 从文件载入图像
            filename = (filename)
            img1 = wx.Image(filename, wx.BITMAP_TYPE_ANY)
            # 获取原始图片数据
            w = img1.GetWidth()
            h = img1.GetHeight()
            img2 = img1.Scale(w*3, h*3)#缩小图像
            #转换它们为静态位图部件
            staticBitmap2 = wx.StaticBitmap(panel, -1, wx.BitmapFromImage(img2))
            codeText = wx.TextCtrl(panel, -1, "", size=(100, 50),style=wx.TE_PROCESS_ENTER)
            codeText.SetMaxLength(7)
            submitBtn = wx.Button(panel, label=u"提交",size=(60, 50))
            submitBtn.SetToolTipString(u"请输入验证码！")
            # and put them into the sizeri
            fgBoxsizer.Add(staticBitmap2)
            fgBoxsizer.Add(codeText)
            fgBoxsizer.Add(submitBtn)
            panel.SetSizerAndFit(fgBoxsizer)
            self.codeText = codeText
            self.submitBtn = submitBtn
            self.submitBtn.Bind(wx.EVT_BUTTON, self.OnEnterCode, submitBtn)
            self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterCode, codeText)
            self.Bind(wx.EVT_CLOSE, self.OnClose)
            self.Fit()
        except:
            s=sys.exc_info()
            msg = (u"VerifyCodeFrame ERROR %s happened on line %d" % (s[1],s[2].tb_lineno))
            print msg
    
    def OnClose(self, event):
        wx.CallAfter(self.mainFrame.loginWinStatus, True)
        currentThread = settings.MAIN_GENTHREAD
        currentThread.threadLock.acquire()
        currentThread.lockCondition.notify()
        currentThread.threadLock.release()
        self.Destroy()
    
    def OnEnterCode(self, event):
        code = self.codeText.GetValue().strip().encode('UTF-8')
        if len(code) >= 4:
            sinasettings.VERIFY_CODE = code
            self.codeText.SetValue("")
            wx.CallAfter(self.mainFrame.loginWinStatus, True)
            genThread = settings.MAIN_GENTHREAD
            genThread.threadLock.acquire()
            genThread.lockCondition.notify()
            genThread.threadLock.release()
            self.Destroy()
#             return True
        else:
            event.Skip()

 
if __name__ == '__main__':
    app = wx.App()
    frm = VerifyCodeFrame(None, "C:\Python27\file\pin.png")
    frm.Center()
    frm.Show()
    app.MainLoop()

