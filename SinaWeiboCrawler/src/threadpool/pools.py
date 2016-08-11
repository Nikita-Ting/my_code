# encoding:utf-8
'''Module for distributing jobs to a pool of worker threads.'''




from Queue import Queue#队列
if not hasattr(Queue, 'task_done'):
    from WrapperQueue import Queue
from works import Worker
from jobs import SimpleJob, SuicideJob


__all__=['WorkerPool', 'DefaultWorkerFactory']


def DefaultWorkerFactory(jobQueue):
    return Worker(jobQueue)       
        
class WorkerPool(Queue):
    
    def __init__(self,size=1,maxjobs=0,workerFactory=DefaultWorkerFactory):
        if not callable(workerFactory):
            raise TypeError("workerFactory must be callable")
        self.workerFactory=workerFactory#新建worker
        self._size=0#活动的worker数
        
        Queue.__init__(self, maxjobs)
        self._jobs=self
        
        for i in xrange(size):
            self.grow()
        
    def grow(self):
        worker=self.workerFactory(self)
        worker.start()
        self._size +=1
        
    def shrink(self):
        "Get rid of one worker from the pool. Raises IndexError if empty."
        if self._size <= 0:
            raise IndexError("pool is already empty")
        self._size -= 1
        self.put(SuicideJob())

    def shutdown(self):
        print "Retire the workers."
        for i in xrange(self.size()):
            self.put(SuicideJob())

    def size(self):
        "Approximate number of active workers (could be more if a shrinking is in progress)."
        return self._size

    def map(self, fn, *seq):
        "Perform a map operation distributed among the workers. Will block until done."
        results = Queue()
        args = zip(*seq)
        for seq in args:
            job = SimpleJob(results, fn, seq)
            self.put(job)

        # Aggregate results
        result = []
        for i in xrange(len(args)):
            result.append(results.get())
        return result

    def wait(self):
        self.join()     
        
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
         