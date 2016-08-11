# encoding:utf-8

'''
created on 2014-4-29
this is setings of sina
'''
import os
import sys

VERIFY_INPUT_FLAG=1
#手动输入验证码标识

VERIFY_CODE = ""#验证码

#Python解释程序路径的绝对路径  
PATH = os.path.dirname(sys.executable)

SOFT_PATH = PATH
TASK_PATH = PATH
#文件保存路径
FILE_PATH_DEFAULT = "file"
STORE_PATH = os.path.join(PATH, 'file')

PAGE_LIMIT = 10

COMWEIBO_COOKIE = 'weibo.com.cookie.dat'
CNWEIBO_COOKIE  = 'weibo.cn.cookie.dat'

#定义采集内容
CrawlerContent=['cwlFollows','cwlFans','cwlWeibos','cwlComment','cwlForward']

#两种用户数据格式：指定用户信息（信息更详细）；关注或者粉丝用户信息；
#两种信息格式：爬取用户的所有微博信息格式；指定某条微博的评论与转发信息
#关注或粉丝用户
'''博主ID/用户ID/用户名或主页/昵称/性别/头像地址/达人标识/新浪认证/新浪会员/所在地
/关注数/粉丝数/微博数/简介/最新微博/关注来自(设备)'''
F_KEY = ['userid','uid','uname','nickname', 'sex','Imgurl', 'daren', 'verify', 'vip', 'addr','n_follows', 
    'n_fans', 'n_weibos', 'intro', 'latestweibo','p_from', 
]


#用户详细信息
'''用户ID/用户名/昵称/性别/头像地址/达人标识/新浪认证/新浪会员/所在地
/关注数/粉丝数/微博数/简介/注册时间/生日/验证信息/Email/QQ/MSN/学校/公司/标签'''
USER_KEY = ['uid','uname', 'nickname', 'sex','daren', 
            'verified', 'vip','locat', 'n_follows', 'n_fans', 'n_weibos','intro', 
            'creatTime','birth', 'verifInfo',
            'email', 'QQ', 'MSN', 'school', 'company', 'tags']

'''
用户ID/用户名/昵称/消息ID/消息内容/用户头像?/消息来源/转发消息ID/图片信息/音频信息
/视频信息/转发数/评论数/发布时间/@用户'''
WEIBO_KEY = [
    'uid', 'uname','nickname' ,'msg_id','msg', 'msgurl','Imgurl', 'msgfrom', 
    'forwId','picUrl','audioUrl','vedioUrl','n_forward','n_comment','publtime','crawltime','aiteUser'
]


'''微博ID/微博博主ID/转发消息Id（评论ID跟消息ID相同）/评论或转发用户ID/用户名/
用户昵称/用户头像/达人/认证/会员/消息内容/转发消息url（评论消息没有）/时间/微博转发/原用户ID/原微博ID'''
ReorCom_KEY = [
    'msgid','ouid','mid','uid','uname', 'nickname','Imgurl', 'daren', 
'verify', 'vip','msg', 'msgurl',  'date', 'isforward','rouid','omid'
      
]


REPOST_KEY = [
    'uid', 'nickname', 'daren', 'verified', 'vip', 
    'msg', 'msg_url', 'msg_id', 'msg_time', 
    'forward_uid', 'forward_nickname', 'forward_msg_url', 'forward_msg_id'     
]

COMMENT_KEY = [
    'uid', 'nickname', 'daren', 'verified', 'vip', 
    'msg', 'msg_url', 'msg_id', 'msg_time', 
    'forward_uid', 'forward_nickname', 'forward_msg_url', 'forward_msg_id'     
]

'''USER_KEY = [
    'uid','uname', 'nickname', 'sex', 'Imgurl', 'daren', 'verified', 'vip','locat','birth', 'blog', 'domain', 'intro', 
    'email', 'QQ', 'MSN', 'university', 'company', 'tag', 'n_follows', 
    'n_fans', 'n_weibos', 'daren_level', 'daren_score', 'daren_interests', 
    'medal', 'cur_level', 'active_days', 'next_level_days',
    'trust_level', 'trust_score'
]'''


