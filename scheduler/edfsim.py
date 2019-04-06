from queue import PriorityQueue, Empty
import collections
import math

from matplotlib import pylab as plt

# not used
# ExeTraceStruct = collections.namedtuple('ExeTraceStruct',['tid','sid','timestamp'])

class Task(object):
    def __init__(self,**kv):
        self.C = 0
        self.D = 0
        self.T = 0
        self.offset = 0

        # vlink id
        self.vlid = 0
        # task id
        self.tid = 0

        '''
        a task may has more than one sid, indexed from 1 to n
        if a task has no supper tasks, the sid shall be set to 0
        '''
        self.sid  = 0

        for k,v in kv.items():
            if hasattr(self,k):
                setattr(self,k,v)
            else:
                raise Exception("No property has name %s in class Task" % k )

def lcm(ipt_a, ipt_b):
    # calc the gcd first
    a = ipt_a
    b = ipt_b
    while b != 0:
        c = a % b
        a = b
        b = c
    # then calc the lcm
    result = int(ipt_a * ipt_b / a)
    return result
'''
TCB structure definition
'''
class TaskControlBlock(object):
    def __init__(self, task):
        self.id = task.tid
        self.T  = task.T
        #warning the D parameter is relative to the offset parameter
        self.D  = task.D
        self.C  = task.C
        self.offset = task.offset

        self.exeTime = 0
        self.deadlineInstance = task.D
        self.pnum = 0

    def __lt__(self, other):
        return self.deadlineInstance <= other.deadlineInstance
'''
return none if the demandcheck passed
or return a task set contaning tasks which exceeds the available CPU bandwidth
'''
def demandCheck(freeTaskList:list, smtTaskList:list):
    _overloadTaskSet = set()
    _phiSet = set()
    _deltaSet = set()
    _lambda = 0

    # calc the lcm(T1,T2,...,Tn)
    _hyp = 1
    for _task in freeTaskList + smtTaskList:
        _hyp = lcm(_hyp,_task.T)
    # print("hyperiode is %d" % _hyp)
    # get the max phi
    _max_phi = 0
    for _task in freeTaskList + smtTaskList:
        if _task.offset>_max_phi:
            _max_phi = _task.offset
    # print("max phi is %d" % _max_phi)

    _lambda = _max_phi + 2*_hyp
    # print("lambda is %d" % _lambda)
    # calc the _deltaSet and the _phiSet
    for _task in freeTaskList + smtTaskList:
        _j = 0
        _jobDeadline = 0
        _tmp = _task.offset+_j*_task.T

        while(_tmp<=_lambda):
            _phiSet.add(_tmp)
            # calc d_ij for j-th job of i-th task in task set
            _jobDeadline = _tmp + _task.D
            if(_jobDeadline<=_lambda):
                _deltaSet.add(_jobDeadline)

            _j = _j+1
            # calc the a_ij for j-th job of i-th task in task set
            _tmp = _task.offset+_j*_task.T

    max_func = lambda x: x if x>0 else 0
    for t1 in _phiSet:
        for t2 in _deltaSet:
            if(t2>t1):
                _smtLoadSum = 0
                # calc the task load of smt tasks
                # the feasibility of smt tasks is pre-checked by smt solver
                for _task in  smtTaskList:
                    _tmpLeft  = math.floor( float(t2-_task.offset-_task.D)/float(_task.T) )
                    _tmpRight = math.ceil( float(t1-_task.offset)/float(_task.T) )
                    _smtLoadSum = _smtLoadSum + _task.C* max_func( ( _tmpLeft - _tmpRight + 1 ) )

                # calc the task load of free tasks, then check the feasibility
                _freeLoadSum = 0
                for _task in freeTaskList:
                    _load = 0
                    _tmpLeft  = math.floor( float(t2-_task.offset-_task.D)/float(_task.T) )
                    _tmpRight = math.ceil( float(t1-_task.offset)/float(_task.T) )
                    _load = _task.C* max_func( ( _tmpLeft - _tmpRight + 1 ) )
                    if((_freeLoadSum + _smtLoadSum + _load) <=t2-t1 ):
                        _freeLoadSum = _freeLoadSum + _load
                    else:
                        # demand overload
                        _overloadTaskSet.add(_task)
                #print("t1:%3d t2:%d smtloadsum:%3d freeloadsum:%3d demand:%3d" % (t1,t2,_smtLoadSum,_freeLoadSum,t2-t1))

    return _overloadTaskSet

class EDFSim(object):
    def __init__(self, freeTaskList:list, smtTaskList:list):
        self.readyQueue = PriorityQueue()
        self.tcbSet = set()
        self.waitSet = set()
        self.exeTaskTraceList = []
        self.hyperPeriod = 0

        self.__calcHyperPeriod(freeTaskList,smtTaskList)
        self.__makeTCBSet(freeTaskList, smtTaskList)

    def __makeTCBSet(self, freeTaskList:list, smtTaskList:list):
        for _task in freeTaskList + smtTaskList:
            self.tcbSet.add(TaskControlBlock(_task))

    def __calcHyperPeriod(self,freeTaskList:list, smtTaskList:list):
        _hyp = 1
        for _task in freeTaskList + smtTaskList:
            _hyp = lcm(_hyp,_task.T)
        self.hyperPeriod = _hyp

    def __checkSatisfaction(self):
        utilization = 0.0
        for tcb in self.tcbSet:
             utilization += float(tcb.C)/float(tcb.T)

        print("CPU utilization is %f" % utilization)
        return False if(utilization>1.0) else True

    def __recordExeTrace(self,time, _tcb, traceList):
        # (task_id,sid, timestamp)
        _id = 0 if _tcb==None else _tcb.id
        traceList.append((_id,0,time))
        #print("task %d is running at time %d for one macrotick" % (_id, time))

    def __extractTaskTrace(self, exeTraceList):
        _start_id = 0
        _start_time = 0
        _time_duration = 0

        if  exeTraceList:
            _start_id = 0
            _start_time = exeTraceList[0][2]
            for _i,_trace in enumerate(exeTraceList):
                if _trace[0]==exeTraceList[_start_id][0]:
                    _time_duration += 1
                else:
                    # tupple (task_id, sid, start_time, time duration)
                    self.exeTaskTraceList.append((exeTraceList[_start_id][0],exeTraceList[_start_id][1],_start_time,_time_duration))
                    _start_id = _i
                    _start_time = _trace[2]
                    _time_duration = 1
            # add the last trace
            self.exeTaskTraceList.append((exeTraceList[_start_id][0],exeTraceList[_start_id][1],_start_time,_time_duration))
    '''
    return the execution trace list
    a trace is encapsulated by a tupple, that is (task_id, sid, start_time, time_duration)
    '''
    def getExeTaskTraceList(self):
        return self.exeTaskTraceList
    '''
    run the EDFSim, raises exception if tasks are not schedulable
    be sure the CPU utilization checking and demand cheking before run the function
    '''
    def run(self):
        if not (self.__checkSatisfaction()):
            raise Exception("utilization overflow!!")
        '''
        a temp list to record elements removed from a set,
        in case of a 'Set changed size during iteration' error
        '''
        _tmpTCBList = []
        _exeTraceList = []
        print("the hyper-period is %d" % self.hyperPeriod)

        for time in range(self.hyperPeriod):
            for tcb in self.tcbSet:
                # activate a task
                if(tcb.pnum * tcb.T == time):
                    tcb.pnum += 1
                    tcb.exeTime = 0
                    tcb.deadlineInstance = time + tcb.D + tcb.offset
                    self.waitSet.add(tcb)
                    _tmpTCBList.append(tcb)

            # remove the activated elements from tcbSet
            for _x in _tmpTCBList:
                self.tcbSet.remove(_x)
            _tmpTCBList.clear()

            # release tasks from wait set
            for tcb in self.waitSet:
                if(tcb.offset==time % tcb.T):
                    # release the task
                    self.readyQueue.put(tcb)
                    _tmpTCBList.append(tcb)

            # remove the released elements from waitSet
            for _x in _tmpTCBList:
                self.waitSet.remove(_x)
            _tmpTCBList.clear()

            # run tasks, remove it from the ready queue
            try:
                tcb = self.readyQueue.get(block=False)
            except Empty:
                tcb = None

            self.__recordExeTrace(time,tcb,_exeTraceList)

            if not (tcb==None):
                # time elapses for 1 macrotick
                tcb.exeTime += 1
                # the _task is finished
                if(tcb.exeTime == tcb.C):
                    tcb.exeTime = 0
                    self.tcbSet.add(tcb)
                elif(time==tcb.deadlineInstance):
                    # task overtime
                    raise Exception("task_%d overtime at %d deadline:%d exetime:%d" % (tcb.id,time,tcb.D,tcb.exeTime))
                else:
                    # continue executing
                    self.readyQueue.put(tcb)

        # extract and generate the task trace from the runtime log '_exeTraceList'
        self.__extractTaskTrace(_exeTraceList)


def testEDFSim(freeTaskList: list, smtTaskList: list):
    '''
    freeTaskList = [
        Task(tid=1,T=100,C=20,D=100,offset=0),
        Task(tid=2,T=100,C=10,D=90,offset=0),
        Task(tid=3,T=100,C=12,D=100,offset=0),
        Task(tid=4,T=250,C=60,D=200,offset=0),
    ]
    smtTaskList  = [
        Task(tid=5,T=300,C=10,D=260,offset=250),
        Task(tid=6,T=250,C=40,D=50,offset=10),
        Task(tid=7,T=300,C=7,D=107,offset=100),
    ]
    '''
    '''
    freeTaskList = [
        Task(tid=1,T=100,C=40,D=100,offset=0),
    ]
    smtTaskList  = [
        #Task(tid=5,T=200,C=20,D=20,offset=10),
        Task(tid=6,T=100,C=40,D=70,offset=30),
        Task(tid=7,T=100,C=10,D=10,offset=80),
    ]
    '''

    '''
    freeTaskList = [
        Task(tid=1,T=100,C=90,D=100,offset=0),
    ]
    smtTaskList  = [
        Task(tid=5,T=100,C=10,D=20,offset=10),
    ]
    '''
    
    result = demandCheck(freeTaskList,smtTaskList)

    if(len(result)!=0):
        print("-----------------------------------------------")
        print("demand overload !")
        for x in result:
            print("task %d overload" % x.tid)
        return

    sim = EDFSim(freeTaskList,smtTaskList)

    sim.run()
    logs = sim.getExeTaskTraceList()
    print("-----------------------------------------------")
    #for _trace in logs:
    #    print("task %2d sid %2d runs at time %3d for %3d MA" % (_trace[0],_trace[1],_trace[2],_trace[3]) )
    print("total trace number is %d" % len(logs))

    # draw the task trace
    x_time = []
    y_task = []

    last = 0
    for _trace in logs:
        x_time.append(_trace[2])
        y_task .append(last)
        x_time.append(_trace[2])
        y_task.append(_trace[0])
        last = _trace[0]
    x_time.append(logs[-1][2]+logs[-1][3])
    y_task.append(logs[-1][0])

    plt.figure()
    plt.xlabel('global time')
    plt.ylabel('task id')
    plt.plot(x_time,y_task)

    # draw the reference line
    hyp = logs[-1][2]+logs[-1][3]
    # idle task is identified with 0
    taskIDList = [x.tid for x in freeTaskList+smtTaskList ]
    taskIDList.append(0)
    for task_id in taskIDList:
        plt.plot([0,hyp],[task_id,task_id],'--',linewidth=0.5)

    plt.show()

if __name__=="__main__":
    testEDFSim()


