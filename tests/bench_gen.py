"测试集生成模块"

from msg_scheduler import model as mmodel
from scheduler import model as tmodel
import time

def gen_model(periods: int, utilization: float, granuolarity: int):
    '''
    功能描述：
        生成测试集
    参数描述：
        peroids: 任务周期集合, 单位：毫秒
        utilization: 任务集总体利用率
        granuolarity: 任务调度时间粒度，单位：微秒
    '''
    # Check utilization
    if (utilization < 0) or (utilization > 1):
        print("[Benchmark Gen][ERR]: utilization wrong value")
        return None

    