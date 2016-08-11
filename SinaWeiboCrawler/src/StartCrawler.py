# encoding:utf-8

'''
created on 2014-5-20
this is start model of sina-crawler
'''
import wx
from frame import loginframe

def main():
    app=wx.App()
    frame = loginframe.LoginFrame(None, -1,u"新浪微博爬虫软件登录",(500,375))
    frame.CenterOnScreen()
    frame.Show(True)
    app.MainLoop()
    
if __name__== '__main__':
    main()
