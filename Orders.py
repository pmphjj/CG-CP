from collections import defaultdict

class Orders_Dict(object):
    orders_dict = dict()    # order_code ---> Basic_Order_Info

    @staticmethod
    def add_orders(order_info):
        '''
            向字典中添加医嘱
        :param order_info: 是一个dict格式的
        :return: 
        '''

        if order_info["CLINIC_ITEM_CODE"] in Orders_Dict.orders_dict:
            return
        else:
            Orders_Dict.orders_dict[order_info["CLINIC_ITEM_CODE"]] = Basic_Order_Info(order_info)

    @staticmethod
    def get_orders(order_code):
        '''
            获取某一阶段的某一个医嘱
        :param order_code: 
        :param stage_sqno: 
        :return: 
        '''

        if order_code in Orders_Dict.orders_dict:
            return Orders_Dict.orders_dict[order_code]
        else:
            print("Order not in Order_Dict")
            return None


class Basic_Order_Info(object):
    def __init__(self, order):
        '''
            医嘱类，包含医嘱的基本信息
        :param order:医嘱的具体信息, 是一个dict格式
        
            (新增该医嘱是否是必选项，药物剂量等)

            包含的参数有：
            order_class
            clinic_item_code
            order_name
        '''

        self.order = order
        self.order_class = order["ORDER_CLASS"]
        self.clinic_item_code = order["CLINIC_ITEM_CODE"]
        self.order_name = order["ORDER_NAME"]
        self.order_amount = order["AMOUNT"]
        self.order_freq = order["FREQ_CODE"] if "FREQ_CODE" in order else None
        self.order_plan_days = order["PLAN_DAYS"] if "PLAN_DAYS" in order else None
        self.order_required = order["REQUIRED"] if "REQUIRED" in order else None

        return

    def __str__(self):
        return self.order

