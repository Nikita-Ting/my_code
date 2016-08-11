# workers.py - Worker objects who become members of a worker pool
# Copyright (c) 2008 Andrey Petrov
#
# This module is part of workerpool and is released under
# the MIT license: http://www.opensource.org/licenses/mit-license.php


'''
created on 2014-5-7
part of src come from the Pameng
'''


from threading import Thread
from jobs import Job,SimpleJob
from exceptions import TerminationNotice


__all__=['Worker', 'EquippedWorker']

class Worker(Thread):
    
    def __init__(self,jobs):
        self.jobs=jobs
        Thread.__init__(self)
        
    def run(self):
        #Get jobs from the queue and perform them as they arrive
        while 1:
            job=self.jobs.get()
            try:
                job.run()
                self.jobs.task_done()
            except TerminationNotice():
                self.jobs.task_done()
                break
            
class EquippedWorker(Worker):
    
    def __init__(self,jobs,toolboxFactory):
        self.toolBox=toolboxFactory()
        Worker.__init__(self.jobs)
        
    def run(self):
        #
        while 1:
            job=self.jobs.get()
            try:
                job.run(toolbox=self.toolBox)
                self.jobs.task_done()
            except TerminationNotice():
                self.jobs.task_done()
                break
        
        
        
        
        
        
        
        
        
        
        
        
            