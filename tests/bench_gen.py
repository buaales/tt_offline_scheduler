"测试集生成模块"

import time

def gen_model(periods, utilization, granuolarity):
    '''
    功能描述：
        生成测试集
    参数描述：
        peroids: 任务周期集合
        utilization: 任务集总体利用率
        granuolarity: 任务调度时间粒度，单位：微秒
    '''