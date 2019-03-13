import json
import sqlite3
import pandas as pd
import Orders

class Clinical_Pathway(object):
    def __init__(self, cp_id, version_sqno, db_config_path="./db_config.json"):
        '''
            初始化临床路径类
        :param db_config_path: 数据库配置地址
        :param cp_id: 需要建立的临床路径id
        :param version_sqno: 需要建立的临床路径版本

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

        # 读取数据库,建立连接
        with open(db_config_path, "r") as f:
            self.db_config = json.loads(f.read())
        self.conn = sqlite3.connect(self.db_config["db_path"] + self.db_config["db_filename"])

        self.__build_cp__()

        self.conn.close()
        return

    def __build_cp__(self):

        # 处理临床路径的基本信息
        cp_info = pd.read_sql_query(
            "select * from CP_INFO where CP_ID = '" + str(self.cp_id) + "' and VERSION_SQNO = '" + str(
                self.version_sqno) + "'", self.conn)
        self.cp_name = cp_info.loc[0]["CP_NAME"]

        # 处理临床路径的阶段信息
        cp_stage = pd.read_sql_query(
            "select * from CP_STAGE where CP_ID = '" + str(self.cp_id) + "' and VERSION_SQNO = '" + str(
                self.version_sqno) + "'", self.conn)
        cp_stage = cp_stage.sort_values("STAGE_SQNO")
        self.stage_nums = len(cp_stage)

        cp_stage_columns_list = cp_stage.columns.values.tolist()
        for each_stage in cp_stage.iterrows():
            each_stage_dict = dict([(k, each_stage[1][k]) for k in cp_stage_columns_list])
            new_stage = Stages(self.cp_id, self.version_sqno, each_stage_dict, self.conn)
            self.stage[each_stage[1]["STAGE_SQNO"] ]= new_stage

        return

    def __str__(self):
        CP_str = ""

        for sqno, stage in self.stage.items():
            CP_str += sqno + " " + stage.get_stage_item_codes() + "\n"

        return CP_str


class Stages(object):
    def __init__(self, cp_id, version_sqno, stage_info, conn):
        '''
            临床路径的阶段类
        :param cp_id: 临床路径的id
        :param version_sqno: 临床路径的版本
        :param stage_info: 临床路径阶段的详细信息, dict格式
        :param conn: 数据库连接

        Stage包含的参数有：
            stage_sqno
            start_day
            end_day
            stage_desc
            stage_name
            stage_item_codes_set: set,该阶段所有药物编号的集合
            stage_orders_detail: 字典,药物code ---> 药物的详细信息
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

        # 获取该阶段的药物codes
        cp_orders = pd.read_sql_query(
            "select * from CP_DETAIL_ORDER where CP_ID = '" + str(self.cp_id) + "' and VERSION_SQNO = '" + str(
                self.version_sqno) + "' and STAGE_SQNO = '" + str(self.stage_sqno) + "'", conn)

        cp_orders_columns_list = cp_orders.columns.values.tolist()
        for each_order in cp_orders.iterrows():

            self.stage_item_codes_set.add(each_order[1]["CLINIC_ITEM_CODE"])

            # 创建药物详情
            each_order_dict = dict([(k, each_order[1][k]) for k in cp_orders_columns_list])
            self.stage_orders_detail[each_order[1]["CLINIC_ITEM_CODE"]] = Orders.Basic_Order_Info(each_order_dict)
        return


    def add_orders(self):
        '''
            添加医嘱进该阶段
        :return: 
        '''

    def delete_orders(self):
        '''
            删除该阶段的医嘱
        :return: 
        '''


    def __str__(self):
        return ",".join(self.stage_item_codes_set)

    def get_stage_item_codes(self):
        return ",".join(self.stage_item_codes_set)


class CP_Variation(object):



if __name__ == "__main__":
    cp = Clinical_Pathway("4,621", "3")
    print(cp)