

'''
created on 2014-5-6
this part Generic jobs used with the worker pool
part of src come from the Pameng
'''


from exceptions import TerminationNotice



__all__ = ['Job', 'SuicideJob', 'SimpleJob']

class Job(object):
    def __init__(self):
        pass
    
    def run(self):
        pass
    
class SuicideJob(Job):
    #A worker receiving this job will commit suicide.
    def run(self,**kw):
        raise TerminationNotice()
    
class SimpleJob(Job):
    
    def __init__(self,result,method,args=[]):
        self.result=result
        self.method=method
        self.args=args
        
    def run(self):
        if isinstance(self.args,list) or isinstance(self.args, tuple):
            runMethod=self.method(*self.args)
        elif isinstance(self.args,dict): 
            runMethod=self.method(**self.args)
        self.MethodReturn(runMethod)
        
    def MethodReturn(self,method):
        self.result.put(method)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

    