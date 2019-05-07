# coding: utf-8
from build_CP import Clinical_Pathway,Stages,CP_Variation
from Build_visits import Build_Visist_Order

class VISIT_Analyzer(object):
    """
        实时visit分析器：对于特定临床路径和动态visit数据的实时变异分析类
        cp: 输入的临床路径
        day_level_info: visit中的day_level_info字段值，date ---> list[]
        day_stage_map: 每天属于的阶段区间 {date:[start_stage,end_stage]}
        """
    def __init__(self,input_cp,visit_day_level_info):
        self.cp = input_cp
        self.day_level_info = visit_day_level_info
        self.day_stage_map = self.split_visit_stage()


    def add_order(self,date,order):
        """
        向visit中添加新的医嘱，并返回该医嘱的变异情况
        :param date: 医嘱日期
        :param order: 医嘱 dict类型
        :return:order的变异情况
        """
        if date not in self.day_level_info:
            self.day_level_info[date] = []
        self.day_level_info[date].append(order)
        self.day_stage_map = self.split_visit_stage()
        if date not in self.day_stage_map:
            print("{}.{} ERROR: date not in day_stage_map!".format(date,order["CLINIC_ITEM_CODE"]))
            return None
        stage_list = self.day_stage_map[date]
        if stage_list is None or len(stage_list) == 0:
            print("{}.{} ERROR: invalid stage_list!".format(date,order["CLINIC_ITEM_CODE"]))
            return None
        stage_list = [str(x) for x in range(stage_list[0],stage_list[-1]+1)]
        cp_orders = dict()
        for stage_no in stage_list:
            stage_orders = self.cp.stage[stage_no].stage_orders_detail  # 字典: 该阶段包含的医嘱code ---> 医嘱的详细信息(Basic_Order_Info类)

            # 此处未考虑对于不同阶段的同一种医嘱，使用剂量，频率，天数不同的情况
            for key, value in stage_orders.items():
                if key in cp_orders:
                    pass  # 若考虑剂量，可以将剂量小的覆盖
                else:
                    cp_orders[key] = value
        day_variation = self.get_order_var_info(order, cp_orders)
        if len(day_variation) == 0:
            print("{}.{}({}):No variation.".format(date,order["CLINIC_ITEM_CODE"],order["ORDER_NAME"]))
        else:
            print("{}.{}({}):  {}".format(date,order["CLINIC_ITEM_CODE"],order["ORDER_NAME"],day_variation))
        return day_variation


    def delete_order(self, date, order):
        """
        删除医嘱，更新阶段划分表
        :param date:医嘱发生日期（精确到天）
        :param order:医嘱 dict()
        :return:
        """
        if date not in self.day_level_info:
            print ("{}.{} date not in visit!".format(date,order["CLINIC_ITEM_CODE"]))
            return False
        if order not in self.day_level_info[date]:
            print("{}.{} order not in the order list of the date!".format(date,order["CLINIC_ITEM_CODE"]))
            return False
        self.day_level_info[date].remove(order)
        if len(self.day_level_info[date]) == 0:
            self.day_level_info.pop(date)
        self.day_stage_map = self.split_visit_stage()
        print("{}.{} Successfully delete.".format(date,order["CLINIC_ITEM_CODE"]))
        return True

    def get_order_var_info(self, order, cp_orders):
        order_code = order["CLINIC_ITEM_CODE"]
        #记录order的变异情况
        order_variation = dict()

        # 该code不在规定医嘱集里面，则属于新增变异
        if order_code not in cp_orders:
            order_variation["newadd_variation"]=True

        # 在规定医嘱集里面则判断是否属于【剂量变异、天数变异、频率变异】
        else:
            cp_order_detail = cp_orders[order_code]

            # 比较剂量, 注意需要考虑有些临床路径定义的医嘱内AMOUNT字段为空
            if not cp_order_detail.order_amount:
                pass
            else:
                # 实际使用剂量大于cp中定义的剂量, 则将其加入dosage_variation异常
                if cp_order_detail.order_amount < order["AMOUNT"]:
                    order_variation["dosage_variation"] = dict()
                    order_variation["dosage_variation"]["order"] = cp_order_detail.order_amount
                    order_variation["dosage_variation"]["cp"] = order["AMOUNT"]

            # 比较天数变异, 若实际医嘱的计划天数大于规定医嘱的计划天数，则判断为变异
            if not cp_order_detail.order_plan_days:
                pass
            else:
                if cp_order_detail.order_plan_days < order["PLAN_DAYS"]:
                    order_variation["planday_variation"] = dict()
                    order_variation["planday_variation"]["order"] = cp_order_detail.order_plan_days
                    order_variation["planday_variation"]["cp"] = order["PLAN_DAYS"]

            # 比较频率变异，若频率不同则判断为变异
            if not cp_order_detail.order_freq:
                pass
            else:
                if cp_order_detail.order_freq != order["FREQ_CODE"]:
                    order_variation["freq_variation"] = dict()
                    order_variation["freq_variation"]["order"] = cp_order_detail.order_freq
                    order_variation["freq_variation"]["cp"] = order["FREQ_CODE"]

        return order_variation

    def split_visit_stage(self, type = "new"):
        if type == "old":
            return self.__get_stage_by_split_visit_oldway()
        if type == "new":
            return self.__get_stage_by_split_visit()

    #注：应用旧版的阶段划分方法
    def __get_stage_by_split_visit_oldway(self):
        sort_visit_order_list = sorted(self.day_level_info.items(), key=lambda x: x[0])

        cur_stage_num = 1
        max_stage_num = self.cp.stage_nums
        # 天-阶段映射列表，列表下标为天序号，值为该天的阶段范围(起始阶段，终止阶段)
        day_stage_map = dict()
        # 阶段-历史医嘱dict {阶段序号：set(该阶段历史医嘱代码)} 用于必选医嘱没选的检查
        stage_order_dict = dict([(x, set()) for x in range(1, max_stage_num + 1)])

        # 划分阶段 ，暂不考虑路径定义的阶段长度与具体执行日期间的差异
        for day_order in sort_visit_order_list:

            day_time = day_order[0]
            temp_stage_num = cur_stage_num
            # 获取当天医嘱的编码集合
            day_item_code_set = set([x["CLINIC_ITEM_CODE"] for x in day_order[1]])
            while len(day_item_code_set) > 0 and temp_stage_num <= max_stage_num:
                temp_stage_code_set = self.cp.get_stage_code(temp_stage_num)

                # 当天剩余医嘱与当前阶段有交集，取其差集
                intersec_set = day_item_code_set.intersection(temp_stage_code_set)
                if len(intersec_set) > 0:
                    stage_order_dict[temp_stage_num] = stage_order_dict[temp_stage_num].union(intersec_set)
                    day_item_code_set = day_item_code_set.difference(temp_stage_code_set)
                else:
                    # 无交集，判断与下一阶段是否有交集，若仍无交集，则视其为变异
                    if temp_stage_num == max_stage_num:
                        break
                    temp_next_stage_code_set = self.cp.get_stage_code(temp_stage_num + 1)
                    next_intersec_set = day_item_code_set.intersection(temp_next_stage_code_set)
                    if len(next_intersec_set) > 0:
                        stage_order_dict[temp_stage_num + 1] = stage_order_dict[temp_stage_num + 1].union(
                            next_intersec_set)
                        day_item_code_set = day_item_code_set.difference(temp_next_stage_code_set)
                        temp_stage_num += 1
                    else:
                        break

            day_stage_map[day_time] = (cur_stage_num, temp_stage_num)
            cur_stage_num = temp_stage_num

        return day_stage_map
    #注：应用新版的阶段划分方法
    def __get_stage_by_split_visit(self):
        """
        获取输入的visit的天与阶段的映射表
        :return: 天与阶段的映射表{ "天序号":[起始阶段，终止阶段]}
        """
        sort_visit_order_list = sorted(self.day_level_info.items(), key=lambda x: x[0])
        cur_stage_num = 1
        max_stage_num = self.cp.stage_nums
        # 天-阶段映射列表，列表下标为天序号，值为该天的阶段范围(起始阶段，终止阶段)
        day_stage_map = dict()

        # 划分阶段 ，暂不考虑路径定义的阶段长度与具体执行日期间的差异
        for day_order in sort_visit_order_list:
            day_time = day_order[0]
            temp_stage_num = cur_stage_num
            # 获取当天医嘱的编码集合
            day_item_code_set = set([x["CLINIC_ITEM_CODE"] for x in day_order[1]])
            while len(day_item_code_set) > 0 and temp_stage_num <= max_stage_num:
                temp_stage_code_set = self.cp.get_stage_code(temp_stage_num)
                # 取当天剩余医嘱与当前阶段的交集
                intersec_set = day_item_code_set.intersection(temp_stage_code_set)
                # 若当天剩余医嘱与当前阶段有交集，取其差集
                if len(intersec_set) > 0:
                    day_item_code_set = day_item_code_set.difference(intersec_set)
                else:
                    # 无交集，且当前阶段已达最大阶段，则退出，temp_stage_num为终止阶段
                    if temp_stage_num == max_stage_num:
                        break
                    # 判断与下一阶段是否有交集，若仍无交集，则视其为变异
                    temp_next_stage_code_set = self.cp.get_stage_code(temp_stage_num + 1)
                    next_intersec_set = day_item_code_set.intersection(temp_next_stage_code_set)
                    if len(next_intersec_set) > 0:
                        #将需要判断与下一阶段相交集的部分是否是当前阶段的变异:下一天包含当前阶段的医嘱多余next_intersec_set中的医嘱
                        next_index = sort_visit_order_list.index(day_order)+1
                        if next_index < len(sort_visit_order_list) :
                            next_day_order_set = set([x["CLINIC_ITEM_CODE"] for x in sort_visit_order_list[next_index][1]])
                            next_day_order_set = next_day_order_set.difference(temp_next_stage_code_set)
                            next_day_order_set = next_day_order_set.intersection(temp_stage_code_set)
                            if len(next_intersec_set) >= len(next_day_order_set):
                                day_item_code_set = day_item_code_set.difference(temp_next_stage_code_set)
                                temp_stage_num += 1
                            else:
                                day_item_code_set = day_item_code_set.difference(next_intersec_set)

                        else:
                            day_item_code_set = day_item_code_set.difference(temp_next_stage_code_set)
                            temp_stage_num += 1
                    else:
                        #剩余医嘱与下一阶段无交集，则视其为变异，退出，temp_stage_num为终止阶段
                        break

            day_stage_map[day_time] = (cur_stage_num, temp_stage_num)
            cur_stage_num = temp_stage_num

        return day_stage_map

if __name__ == "__main__":
    cp = Clinical_Pathway("4,621", "3")
    all_visits = Build_Visist_Order("4,621",3)
    visit_day_level_info = all_visits.all_visits_dict["3467225"].day_level_info
    print(len(visit_day_level_info))

    visit_analyzer = VISIT_Analyzer(cp,dict())
    for date in sorted(visit_day_level_info.keys()):
        dayOrders_list = visit_day_level_info[date]
        print()
        for order in dayOrders_list:
            visit_analyzer.add_order(date,order)
        visit_analyzer.delete_order(date,dayOrders_list[-1])