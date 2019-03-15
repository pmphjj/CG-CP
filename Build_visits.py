import json
import sqlite3
import pandas as pd
import datetime
import Orders


class Build_Visist_Order(object):

    def __init__(self, cp_id, version_sqno, db_config_path="./db_config.json", order_table_name="orders"):
        '''
            构造某临床路径的所有visit记录
        :param cp_id: 
        :param version_sqno: 
        :param db_config_path: 
        :param order_table_name: 
        '''

        self.cp_id = cp_id
        self.version_sqno = version_sqno
        self.order_table_name = order_table_name

        self.all_visits_dict = dict()    # all_visits_dict存放的是visit的集合，visit_id ---> Visit类

        # 读取数据库,建立连接
        with open(db_config_path, "r") as f:
            self.db_config = json.loads(f.read())
        self.conn = sqlite3.connect(self.db_config["db_path"] + self.db_config["db_filename"])
        self.__build_visits_info__()
        self.show_info()
        self.conn.close()

    def __build_visits_info__(self):
        '''
            获取该版本临临床路径的所有医嘱详情, 默认orders表中的医嘱是该临床路径版本下的所有医嘱
        :return: 
        '''

        self.all_visits = pd.read_sql_query(
            "select * from " + self.order_table_name, self.conn)

        for each_tuple in self.all_visits.groupby("VISIT_ID"):
            visit_id = each_tuple[0]
            each_visit = each_tuple[1]  #dataframe

            new_visit = Visit(visit_id, each_visit)

            if visit_id not in self.all_visits_dict:
                self.all_visits_dict[visit_id] = new_visit
            else:
                print("ERROR: Exists visit")

    def show_info(self):
        #展示类的基本信息
        print("cp_id:"+self.cp_id)
        print("version_sqno:"+str(self.version_sqno))
        print("order_table_name:"+self.order_table_name)
        print("visits amount:"+str(len(self.all_visits_dict)))


class Visit(object):

    def __init__(self,visit_id, visit_info):
        '''
        :param visit_info: Dataframe的格式
        '''

        self.visit_id = visit_id
        self.visit_info = visit_info.sort_values("ORDER_CONFIRM_TIME")

        self.day_level_info = dict()    # date ---> list[], 该list存放当前所有的医嘱信息，一个医嘱信息是一个dict()

        # 将ORDER_CONFIRM_TIME模糊为天级别，%m/%d/%Y
        self.visit_info["DATE"] = self.visit_info["ORDER_CONFIRM_TIME"].map(
            lambda x: datetime.datetime.strptime(x, '%m/%d/%Y %H:%M:%S').strftime("%m/%d/%Y"))

        # 按照DATE分组，每组是一个list，存放改天的所有医嘱
        for day_info in self.visit_info.groupby("DATE"):
            date = day_info[0]
            day_orders = day_info[1]    #DataFrame

            day_list = []
            order_columns = day_orders.columns.values.tolist()

            # 将这一天中的每一个医嘱变为dict,并存入day_list中
            for order in day_orders.iterrows():

                # 将一个医嘱信息变为dict
                order_dict = dict([(k,order[1][k]) for k in order_columns])
                day_list.append(order_dict)

                # 将医嘱信息添加进入医嘱字典
                #TODO 此处有bug
                # Orders.Orders_Dict.add_orders(order_dict)

            self.day_level_info[date] = day_list














