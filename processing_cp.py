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
        self.stage_orders_detail = dict()#对应的映射为【药物编号(CLINICAL_ITEM_CODES) ---> 药物医嘱类Detail_Order】
        self.score = 0.0

class Order:
    def __init__(self):
        self.order_sqno = -1
        self.order_class = ""
        self.clinic_item_code = -1
        self.perform_dept = ""
        self.order_name = ""

class DetailOrder(Order):

    def __init__(self):
        super(DetailOrder,self).__init__()
        self.order_confirm_time = ""

class Visit():
    def __init__(self):
        self.visit_id = ""
        self.orders_list = []
        self.stage_2_day_dict = {}
        self.day_2_stage_list = []

def partition_orders(input_cp,input_visit):
    stage = 0
    for day_order in input_visit.orders_list:
        #TODO
        pass

    return input_visit

if __name__ == "__main__":
    input_cp = ClinicalPathway()
    input_visit = Visit()
    input_visit = partition_orders(input_cp,input_visit)
