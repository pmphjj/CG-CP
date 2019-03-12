# coding: utf-8


class ClinicalPathway:
    #临床路径类
    def __init__(self):
        self.cp_id = -1
        self.version_sqno = -1
        self.cp_name = ""
        self.stage_nums = 0 #阶段数目
        self.stage = {} #阶段sqno ---> Stages类
        self.score = 0.0


class Stages:
    #临床路径阶段类
    def __init__(self):
        self.stage_sqno = -1
        self.start_day = -1
        self.end_day = -1
        self.stage_desc = ""
        self.stage_name = ""
        self.stage_item_codes_set = set()#该阶段所有药物编号(CLINICAL_ITEM_CODES)的集合;
        self.stage_orders_detail = dict()#对应的映射为【药物编号(CLINICAL_ITEM_CODES) ---> 药物医嘱类Detail_Order】 全局的dict？
        self.score = 0.0

class Order:
    #医嘱父类
    def __init__(self):
        self.order_sqno = -1
        self.order_class = ""
        self.clinic_item_code = -1
        self.perform_dept = ""
        self.order_name = ""

class DetailOrder(Order):
    #医嘱子类，带具体执行时间等详细信息
    def __init__(self):
        super(DetailOrder,self).__init__()
        self.order_confirm_time = ""

class Visit():
    def __init__(self):
        self.visit_id = ""
        self.orders_list = []
        self.stage_2_day_dict = {}
        self.day_2_stage_list = []

def get_item_code(order):
    #TODO
    pass
def get_stage_from_count(stage_count):
    #TODO
    pass

def partition_orders(input_cp,input_visit):
    item_code_2_stage_dict = {}
    #生成医嘱代码与出现阶段的映射关系 {医嘱代码：set(出现阶段)}
    for stage_index in input_cp.stage:
        for item_code in input_cp.stage[stage_index].stage_item_codes_set:
            if item_code not in item_code_2_stage_dict:
                item_code_2_stage_dict[item_code] = set()
                item_code_2_stage_dict[item_code].add(stage_index)
            else:
                item_code_2_stage_dict[item_code].add(stage_index)

    cur_stage = 0
    for day_order in input_visit.orders_list:
        stage_count = {}
        for order in day_order:
            item_code = get_item_code(order)
            if item_code in item_code_2_stage_dict:
                for stage_index in item_code_2_stage_dict[item_code]:
                    if stage_index < cur_stage or stage_index > cur_stage+1:
                        continue
                    if stage_index not in stage_count:
                        stage_count[stage_index] = 1
                    else:
                        stage_count[stage_index] += 1
        cur_order_stage = get_stage_from_count(stage_count)
        #TODO 先确认一天是否可以划分为多个阶段



    return input_visit

if __name__ == "__main__":
    input_cp = ClinicalPathway()
    input_visit = Visit()
    input_visit = partition_orders(input_cp,input_visit)
