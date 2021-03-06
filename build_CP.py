import json
import sqlite3
import pandas as pd
import Orders
from collections import defaultdict

class Clinical_Pathway(object):

    def __init__(self, cp_id, version_sqno, cp_info_path, cp_stage_path, cp_detail_order_path, cp_detail_info_path):
        '''
            初始化临床路径类
        :param db_config_path: 数据库配置地址
        :param cp_id: 需要建立的临床路径id,  string
        :param version_sqno: 需要建立的临床路径版本, string

            临床路径有如下参数：
            cp_id
            version_sqno
            cp_name
            stage_nums: 阶段数目
            stage: dict()，STAGE_SQNO ---> STAGE类
        '''

        self.cp_id = cp_id
        self.version_sqno = version_sqno

        self.cp_name = ""
        self.stage_nums = 0

        self.stage = dict()
        self.required_order_dict = dict()

        # 读取数据库,建立连接
        # with open(db_config_path, "r") as f:
        #     self.db_config = json.loads(f.read())
        # self.conn = sqlite3.connect(self.db_config["db_path"] + self.db_config["db_filename"])

        # 读取并筛选csv文件中的数据
        cp_info = pd.read_csv(cp_info_path, sep="\t")
        cp_stage = pd.read_csv(cp_stage_path, sep="\t")
        cp_detail_order = pd.read_csv(cp_detail_order_path, sep="\t")
        cp_detail_info = pd.read_csv(cp_detail_info_path, sep="\t")

        self.cp_info = cp_info[(cp_info.CP_ID.astype(str) == self.cp_id) & (cp_info.VERSION_SQNO.astype(str) == self.version_sqno)].reset_index(drop=True)
        self.cp_stage = cp_stage[(cp_stage.CP_ID.astype(str) == self.cp_id) & (cp_stage.VERSION_SQNO.astype(str) == self.version_sqno)].reset_index(drop=True)
        self.cp_detail_order = cp_detail_order[(cp_detail_order.CP_ID.astype(str) == self.cp_id) & (cp_detail_order.VERSION_SQNO.astype(str) == self.version_sqno)].reset_index(drop=True)
        self.cp_detail_info = cp_detail_info[(cp_detail_info.CP_ID.astype(str) == self.cp_id) & (cp_detail_info.VERSION_SQNO.astype(str) == self.version_sqno)].reset_index(drop=True)

        self.__build_cp__()
        self.show_info()

        # self.conn.close()

        return

    def __build_cp__(self):

        # 处理临床路径的基本信息
        # cp_info = pd.read_sql_query(
        #     "select * from CP_INFO where CP_ID = '" + str(self.cp_id) + "' and VERSION_SQNO = '" + str(
        #         self.version_sqno) + "'", self.conn)
        self.cp_name = self.cp_info.loc[0]["CP_NAME"]

        # 处理临床路径的阶段信息
        # cp_stage = pd.read_sql_query(
        #     "select * from CP_STAGE where CP_ID = '" + str(self.cp_id) + "' and VERSION_SQNO = '" + str(
        #         self.version_sqno) + "'", self.conn)
        cp_stage = self.cp_stage.sort_values("STAGE_SQNO")
        self.stage_nums = len(cp_stage)

        cp_stage_columns_list = cp_stage.columns.values.tolist()
        for each_stage in cp_stage.iterrows():
            each_stage_dict = dict([(k, each_stage[1][k]) for k in cp_stage_columns_list])
            new_stage = Stages(self.cp_id, self.version_sqno, self.cp_detail_order, self.cp_detail_info, each_stage_dict)
            self.stage[str(each_stage[1]["STAGE_SQNO"]) ]= new_stage

        return

    def __str__(self):
        CP_str = ""

        for sqno, stage in self.stage.items():
            CP_str += str(sqno) + " " + str(stage.get_stage_item_codes()) + "\n"

        return CP_str

    def show_info(self):
        #展示类的基本信息
        print("cp_id:"+self.cp_id)
        print("cp_name:"+self.cp_name)
        print("stage_nums:"+str(self.stage_nums))
        print(self.__str__())

    def get_stage_code(self,x):
        """
        获取第x阶段的医嘱编码集合
        :param x:
        :return:
        """
        x = str(x)
        if x not in self.stage:
            print("ERROR: input stage number {} is invalid.".format(x))
            return
        return self.stage[x].stage_item_codes_set

class Stages(object):
    def __init__(self, cp_id, version_sqno, cp_detail_order, cp_detail_info, stage_info):
        '''
            临床路径的阶段类
        :param cp_id: 临床路径的id
        :param version_sqno: 临床路径的版本
        :param cp_detail_order: 
        :param cp_detail_info:
        :param stage_info: 临床路径阶段的详细信息, dict格式
        :param conn: 数据库连接

        Stage包含的参数有：
            stage_sqno
            start_day
            end_day
            stage_desc
            stage_name
            stage_item_codes_set: set,该阶段所有医嘱编号的集合
            stage_orders_detail: 字典,该阶段包含的医嘱code ---> 医嘱的详细信息
            stage_required_codes_set: set, 该阶段所有必选医嘱编号的集合
            stage_required_detail: 字典,该阶段包含的必选医嘱code ---> 医嘱的详细信息
            
        '''

        self.cp_id = cp_id
        self.version_sqno = version_sqno

        self.stage_sqno = stage_info["STAGE_SQNO"]
        self.start_day = stage_info["START_DAY"]
        self.end_day = stage_info["END_DAY"]
        self.stage_desc = stage_info["STAGE_DESC"]
        self.stage_name = stage_info["STAGE_NAME"]

        self.stage_item_codes_set = set()
        self.stage_orders_detail = dict()
        self.stage_required_codes_set = set()
        self.stage_required_detail = dict()

        # 该阶段的医嘱详细信息表
        # cp_orders = pd.read_sql_query(
        #     "select * from CP_DETAIL_ORDER where CP_ID = '" + str(self.cp_id) + "' and VERSION_SQNO = '" + str(
        #         self.version_sqno) + "' and STAGE_SQNO = '" + str(self.stage_sqno) + "'", conn)
        cp_orders = cp_detail_order[cp_detail_order.STAGE_SQNO == self.stage_sqno].reset_index(drop=True)

        # 该阶段的路径内容记录，主要用于判断医嘱是否必选
        # cp_detail_info = pd.read_sql_query("select * from CP_DETAIL_INFO where CP_ID = '" + str(self.cp_id) + "' and VERSION_SQNO = '" + str(
        #         self.version_sqno) + "' and STAGE_SQNO = '" + str(self.stage_sqno) + "'", conn).rename(columns={"ITEM_SQNO": "ORDER_SQNO"})

        cp_detail_info = cp_detail_info[cp_detail_info.STAGE_SQNO == self.stage_sqno].rename(columns={"ITEM_SQNO": "ORDER_SQNO"}).reset_index(drop=True)


        # 获取必选医嘱的codes集合
        cp_info = cp_orders.merge(cp_detail_info, how="left", on=["CP_ID", "VERSION_SQNO", "STAGE_SQNO", "ORDER_SQNO"])

        cp_require_order = cp_info[ cp_info.REQUIRED.astype(str) == "1"]
        self.stage_required_codes_set = set(cp_require_order.CLINIC_ITEM_CODE)

        cp_orders_columns_list = cp_orders.columns.values.tolist()  # 获取字段名称
        for each_order in cp_info.iterrows():

            self.stage_item_codes_set.add(each_order[1]["CLINIC_ITEM_CODE"])

            # 创建医嘱详情
            each_order_dict = dict([(k, each_order[1][k]) for k in cp_orders_columns_list])
            order_detail = Orders.Basic_Order_Info(each_order_dict)
            self.stage_orders_detail[each_order[1]["CLINIC_ITEM_CODE"]] = order_detail

            # 若医嘱在必选医嘱集中，则将其加入必选医嘱的详情dict
            if each_order[1]["CLINIC_ITEM_CODE"] in self.stage_required_codes_set:
                self.stage_required_detail[each_order[1]["CLINIC_ITEM_CODE"]] = order_detail

            # 将医嘱放入医嘱字典
            Orders.Orders_Dict.add_orders(each_order_dict)

        return

    def add_orders(self, order_code, order_amount=None, order_class=None):
        '''
            添加医嘱进该阶段
        :return: 
        '''

        if order_code in self.stage_item_codes_set:
            print("ERROR: Order has already existed in stage")
        else:
            self.stage_item_codes_set.add(order_code)

            # 将该医嘱放入对应阶段, 若存在对应医嘱，则修改
            order_name = Orders.Orders_Dict.get_orders(order_code).order_name
            order_info = dict({"CLINIC_ITEM_CODE": order_code, "AMOUNT": order_amount, "ORDER_CLASS":order_class, "ORDER_NAME":order_name })
            self.stage_orders_detail[order_code] = Orders.Basic_Order_Info(order_info)

        return

    def delete_orders(self, order_code):
        '''
            删除该阶段的医嘱
        :return: 
        '''

        if order_code not in self.stage_item_codes_set:
            print("ERROR: Order code is not in stage")
        else:
            self.stage_item_codes_set.remove(order_code)
            self.stage_orders_detail.pop(order_code)
        return


    def __str__(self):
        return ",".join(self.stage_item_codes_set)

    def get_stage_item_codes(self):
        return ",".join(self.stage_item_codes_set)

class CP_Variation(object):

    def __init__(self):
        '''
            异常类，定义两个异常，分别是新增异常以及必选项未选异常，存储的都是医嘱code的集合
        '''

        self.variation_num = 0
        self.newadd_variation_num = 0
        self.noselect_variation_num = 0
        self.dosage_variation_num = 0
        self.planday_variation_num = 0
        self.freq_variation_num = 0

        self.newadd_variation = defaultdict(int)
        self.noselect_variation = defaultdict(int)
        self.dosage_variation = defaultdict(int)
        self.planday_variation = defaultdict(int)
        self.freq_variation = defaultdict(int)

    def update_variation_num(self, num):
        self.variation_num += num

    def update_newadd_num(self, num=1):
        self.newadd_variation_num += num

    def update_noselect_num(self, num=1):
        self.noselect_variation_num += num

    def update_dosage_num(self, num=1):
        self.dosage_variation_num += num

    def update_planday_num(self, num=1):
        self.planday_variation_num += num

    def update_freq_num(self, num=1):
        self.freq_variation_num += num

if __name__ == "__main__":
    cp = Clinical_Pathway("4,621", "3", "data/cp_info.csv", "data/cp_stage.csv", "data/cp_detail_order.csv", "data/cp_detail_info.csv")

    print(cp.get_stage_code(2))