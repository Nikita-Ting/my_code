# encoding:utf-8

'''
created on 2014-4-29
this is config of user part of the login
'''

import os
import ConfigParser
#ConfigParser -- responsible for parsing a list of
#              configuration files, and managing the parsed database.
import re
'''
This module provides regular expression matching operations similar to
those found in Perl.'''
from crawlermodel.logfile import LogFile

logger=LogFile().getLogger('login')

class ConfigUser():   
    
    def __init__(self,rootPath=""):
        self.config=ConfigParser.ConfigParser()
        self.rootPath=rootPath
        self.configPath="file\\configUser.ini"
    
    #写入多个属性   
    def WriteConfig(self,**kwargs):
        try:
            uname=kwargs.get('uname', None).replace(r"\n",'')
            password=kwargs.get('psw', None)
            if self.rootPath !="":
                configFile= os.path.join(self.rootPath, self.configPath)
                #将路径组合后返回
                #如果配置文件路径不存在，则写入
                if not os.path.exists(configFile):
                    f=file(configFile,"w")
                    f.close()
                fileContent=open(configFile).read()
                '''若在windows下用记事本打开过配置文件并修改保存，编码为ＵＮＩＣＯＤＥ或ＵＴＦ－８
                             的文件头会被相应的加上＼xff\xfe或\xef\xbb\xbf，若此时传递给xbf，然后再传递给ConfigParser解析会出错
                             所以在解析之前，先替换掉文件头'''                
                fileContent = re.sub(r"\xfe\xff","", fileContent)
                fileContent = re.sub(r"\xff\xfe","", fileContent)
                fileContent = re.sub(r"\xef\xbb\xbf","", fileContent)
                open(configFile, 'w').write(fileContent)
                self.config.read(configFile)
                if uname !=None:
                    ptype="loginUserName"
                    if not self.config.has_section(ptype):
                        self.config.add_section(ptype)
                    self.config.set(ptype, "uName", uname)
                    #以r+的模式写入配置文件
                    self.config.write(open(configFile,"r+"))
                if password !=None:
                    ptype="loginUserPassword"
                    password=password.replace(r"\n",'')
                    if not self.config.has_section(ptype):
                        self.config.add_section(ptype)
                    self.config.set(ptype, "password", password)
                    self.config.write(open(configFile,"r+"))
            else:
                logger.error("系统路径为空！")
        except Exception,e:
            logger.error("Warn:write user config file has occured an error:%s"%e)
    
    #写入一个属性   
    def WriteUserConfig(self, _type, value):
        try:
            value = value.replace(r'\n', '')
            if self.rootPath != "":
                configFile = os.path.join(self.rootPath, self.configPath)
                if not os.path.exists(configFile):
                    f = file(configFile,"w")
                    f.close()
                content = open(configFile).read()
                #Window下用记事本打开配置文件并修改保存后，编码为UNICODE或UTF-8的文件的文件头
                #会被相应的加上\xff\xfe（\xff\xfe）或\xef\xbb\xbf，然后再传递给ConfigParser解析的时候会出错
                #，因此解析之前，先替换掉
                content = re.sub(r"\xfe\xff","", content)
                content = re.sub(r"\xff\xfe","", content)
                content = re.sub(r"\xef\xbb\xbf","", content)
                open(configFile, 'w').write(content)
                self.config.read(configFile)
                if not self.config.has_section(_type):   
                    self.config.add_section(_type)
                if value != "":
                    self.config.set(_type, "path", value)
                    #r+模式写入配置文件
                    self.config.write(open(configFile, "r+"))
            else:
                logger.error("SYS rootPath is empty.")
        except Exception, e:
            logger.error("Warn:write user config file has occur an error.%s" % e)    
        
    def GetConfig(self,ptype,option):
        #ptype存储字典名称，option :该存储字典字段名称
        configValue=""
        try:
            if self.rootPath!="":
                configFile= os.path.join(self.rootPath, self.configPath)
                if os.path.exists(configFile):
                    fileContent = open(configFile).read()
                    '''若在windows下用记事本打开过配置文件并修改保存，编码为ＵＮＩＣＯＤＥ或ＵＴＦ－８
                                    的文件头会被相应的加上＼xff\xfe或\xef\xbb\xbf，若此时传递给xbf，然后再传递给ConfigParser解析会出错
                                    所以在解析之前，先替换掉文件头''' 
                    fileContent = re.sub(r"\xfe\xff","", fileContent)
                    fileContent = re.sub(r"\xff\xfe","", fileContent)
                    fileContent = re.sub(r"\xef\xbb\xbf","", fileContent)
                    open(configFile, 'w').write(fileContent)
                    self.config.read(configFile)
                    if self.config.has_section(ptype):
                        configValue = self.config.get(ptype, option)
                        #configValue :该存储字典字段值
            else:
                logger.error("系统路径为空！")
                return None
        except Exception, e:
            logger.error("Warn:read user config file has occured an error.%s" % e)
            return None
        configValue = configValue.replace(r'\n', '')
        return configValue
        
        
        
        
if __name__ == '__main__':
    config = ConfigUser("C:\Python27")
    un = config.GetConfig("loginUser", "uName")
    print "uName:",un
          
         
        
        
        
        
        
        
        