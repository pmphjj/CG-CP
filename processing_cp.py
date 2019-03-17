# coding: utf-8
from build_CP import Clinical_Pathway,Stages,CP_Variation
from Build_visits import Build_Visist_Order
from Orders import Orders_Dict


class CP_Analyzer(object):
    """
    临床路径变异分析器
    """
    def __init__(self,input_cp,input_visits):
        self.cp = input_cp
        self.visits = input_visits
        self.variation = dict()
        self.__init_variation()

    def __init_variation(self):
        #初始化变异统计信息
        stages_v = dict([(x, CP_Variation()) for x in self.cp.stage])
        visits_v = dict()
        for visit_id in self.visits.all_visits_dict:
            visits_v[visit_id] = {"day_variation":dict(),"day_stage_map":dict()}
        self.variation = {"cp": dict(), "stages": stages_v, "visits": visits_v}

    def get_variation_of_visit(self, input_visit):
        """ 获取一个visit的变异情况
            变异情况分为两类：
                    1.必选没选
                    2.不在临床路径阶段内
        :param input_cp: Clinical_Pathway类
        :param input_visit: Visit类
        :return: stat_var, {"day":每天的变异医嘱代码，"day_stage_map":天与阶段的映射表 ,"stage":各阶段的变异情况}
        """
        sort_visit_order_list = sorted(input_visit.day_level_info.items(), key=lambda x: x[0])
        stat_var = {"day":dict(),"day_stage_map":dict(),"stage":dict()}
        cur_stage_num = 1
        max_stage_num = self.cp.stage_nums
        #天-阶段映射列表，列表下标为天序号，值为该天的阶段范围(起始阶段，终止阶段)
        day_stage_map = dict()
        #阶段-历史医嘱dict {阶段序号：set(该阶段历史医嘱代码)}
        stage_order_dict = dict([(x,set()) for x in range(1,max_stage_num+1)])

        #划分阶段 ，暂不考虑路径定义的阶段长度与具体执行日期间的差异
        for day_order in sort_visit_order_list:
            day_time = day_order[0]
            temp_stage_num = cur_stage_num
            #获取当天医嘱的编码集合
            day_item_code_set = set([x["CLINIC_ITEM_CODE"] for x in day_order[1]])
            while len(day_item_code_set) > 0 and temp_stage_num <= max_stage_num:
                temp_stage_code_set = self.cp.get_stage_code(temp_stage_num)
                #当天剩余医嘱与当前阶段有交集，取其差集
                intersec_set = day_item_code_set.intersection(temp_stage_code_set)
                if  len(intersec_set) > 0:
                    stage_order_dict[temp_stage_num] = stage_order_dict[temp_stage_num].union(intersec_set)
                    day_item_code_set = day_item_code_set.difference(temp_stage_code_set)
                else:
                    #无交集，判断与下一阶段是否有交集，若仍无交集，则视其为变异
                    if temp_stage_num == max_stage_num:
                        break
                    temp_next_stage_code_set = self.cp.get_stage_code(temp_stage_num+1)
                    next_intersec_set = day_item_code_set.intersection(temp_next_stage_code_set)
                    if len(next_intersec_set) > 0:
                        stage_order_dict[temp_stage_num+1] = stage_order_dict[temp_stage_num+1].union(next_intersec_set)
                        day_item_code_set = day_item_code_set.difference(temp_next_stage_code_set)
                        temp_stage_num += 1
                    else:
                        break

            #若当天剩余医嘱集day_item_code_set不为空，则将其加入到当天的首个阶段cur_stage_num的变异记录中
            if len(day_item_code_set) > 0:
                stat_var["day"][day_time] = day_item_code_set
                stat_var["stage"][cur_stage_num] = stat_var["stage"].setdefault(cur_stage_num,set()).union(day_item_code_set)

            day_stage_map[day_time] = (cur_stage_num,temp_stage_num)
            cur_stage_num = temp_stage_num
        stat_var["day_stage_map"] = day_stage_map
        #依据天-阶段的对应关系，搜索必选没选的变异医嘱 需要CP类提供一个required_order_dict {阶段序号：set(该阶段必需的医嘱代码)}
        for stage_num in self.cp.required_order_dict:
            required_set = self.cp.required_order_dict[stage_num]
            compared_set = stage_order_dict[stage_num]
            intersec_set = required_set.intersection(compared_set)
            if required_set != intersec_set:
                stat_var["stage"][stage_num] = stat_var["stage"].setdefault(stage_num, set()).union(required_set.difference(intersec_set))

        return stat_var


    def analyze_visits(self):
        self.__init_variation()
        for visit in self.visits.all_visits_dict.values():
            stat_var = self.get_variation_of_visit(visit)
            self.__update_variation_info(stat_var,visit.visit_id)

    def __update_variation_info(self,stat_var,visit_id):
        self.__add_variation_to_visit(stat_var["day"],stat_var["day_stage_map"],visit_id)
        for num in stat_var["stage"]:
            self.__add_variation_to_stage(stat_var["stage"][num],num)

    def __add_variation_to_visit(self, days_var, day_stage_map, visit_id):
        if visit_id not in self.visits.all_visits_dict:
            print("ERROR:input visit_id {} is invalid.".format(visit_id))
            return
        self.variation["visits"][visit_id]["day_variation"] = days_var
        self.variation["visits"][visit_id]["day_stage_map"] = day_stage_map

    def __add_variation_to_stage(self, var_code_set, x):
        """
        向阶段中添加变异
        :param var_code_set: 变异医嘱的编码set集合
        :param x: 临床路径阶段序号
        :return:
        """
        x = str(x)
        if x not in self.cp.stage:
            print("ERROR: input stage number {} is invalid.".format(x))
            return
        for order_code in var_code_set:
            if order_code in self.cp.stage[x].stage_item_codes_set:
                # 必选项未选异常
                self.variation["stages"][x].noselect_variation[order_code] += 1
                self.variation["stages"][x].update_noselect_num()
            else:
                # 新增异常
                self.variation["stages"][x].newadd_variation[order_code] += 1
                self.variation["stages"][x].update_newadd_num()

    def generate_recommendation(self):
        #TODO 生成临床路径的更新建议，即每个阶段添加的医嘱集合,
        pass

    def show_var_info(self):
        # count = 0
        for stage_num in self.cp.stage:
            variation = self.variation["stages"][stage_num]
            print("阶段：{}, 总变异数:{},  新增变异数:{},  必选未选变异数:{}".format(
                stage_num,variation.variation_num,variation.newadd_variation_num,variation.noselect_variation_num))
            print(variation.newadd_variation)
            print(variation.noselect_variation)
        #{"day_variation":dict(),"day_stage_map":dict()}

    def show_var_info_of_visit(self,visit_id):
        if visit_id not in self.visits.all_visits_dict:
            print("ERROR:input visit_id {} is invalid.".format(visit_id))
            return
        print("visit_id:{}".format(visit_id))
        print("每天异常:")
        for item in self.variation["visits"][visit_id]["day_variation"]:
            print("{}:{}".format(item,",".join(self.variation["visits"][visit_id]["day_variation"][item])))
        print("每天阶段:")
        for item in self.variation["visits"][visit_id]["day_stage_map"]:
            value = self.variation["visits"][visit_id]["day_stage_map"][item]
            l = list(range(value[0],value[1]+1))
            print("{}:{}".format(item,",".join([str(x) for x in l])))

if __name__ == "__main__":
    input_cp = Clinical_Pathway("4,621",3)
    input_visits = Build_Visist_Order("4,621",3)

    anlyzer = CP_Analyzer(input_cp,input_visits)
    anlyzer.analyze_visits()
    # anlyzer.show_var_info()
    print(len(Orders_Dict.orders_dict))
    anlyzer.show_var_info_of_visit("2774502")

    #
    # var_list = []
    # for visit in input_visits.all_visits_dict.values():
    #     variation = get_variation_of_visit(input_cp, visit)
    #     var_list.append(variation)
    # stat_var = count_var(var_list)
    # cp = update_var_info_of_cp(input_cp,stat_var)

