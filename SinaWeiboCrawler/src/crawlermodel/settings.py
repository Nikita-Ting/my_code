# encoding:utf-8

'''
created on 2014-4-29
this is setings of crawlermodel
'''


import sys
import os

#Python解释程序路径的绝对路径  
PATH = os.path.dirname(sys.executable)

SOFT_PATH = PATH
TASK_PATH = PATH
#文件保存路径
FILE_PATH_DEFAULT = "file"
STORE_PATH = os.path.join(PATH, 'file')
#login username and password
LOGINNAME=None
LOGINPASSWOR=None

LOGINWEB=None
MAIN_WINDOW = None
MAIN_GENTHREAD = None

CRAWLER_VERSION="1.1.2"

#采集的用户的ID（多个）
SEARCHUID={}

#采集指定微博
WeiboUrl=None

#帮助窗口显示信息
CRAWLER_HELP_DOC = (u'1.新浪微博爬虫软件，只适合采集新浪微博数据\n'
                         '采集方式：用户昵称/ID；采集指定微博消息；批量采集\n\n')
CRAWLER_HELP_DOC += (u'2.用户昵称/ID方式: 在搜索框输入用户昵称或者ID'
                         ' 进行搜索，然后选择用户开始采集\n\n')
CRAWLER_HELP_DOC += (u'3.微博URL方式：该方式可以采集指定微博的转发和评论信息.输入微博地址\n'
                            '(如：http://weibo.com/1000000253/ezC36cq3i6G) '
                            '然后开始采集\n\n')
CRAWLER_HELP_DOC += (u'4.批量采集方式: 该方式采集指定的多个用户信息. '
                            '输入多个用户的数字格式ID，用分号隔开。\n'
                            '也可以文件导入ID.然后开始采集;\n\n')
CRAWLER_HELP_DOC += (u'5.该软件部分代码来自爬萌，想要获取更多微博数据\n'
                            '请访问爬萌网站"http://114.113.145.13/"'
                            ' 想要获取更新的软件版本请访问实验室主页.\n')
#实验室主页
HOME_PAGE = 'http://cins.swpu.edu.cn/'
#开发者信息
DEVELOPERS = ['Nikita<nikita.tingl@gmail.com>']
LICENCE    = '请访问 %s' % HOME_PAGE
COPYRIGHT  = '(C) 2014 Center for Intelligent and Networked Systems'

