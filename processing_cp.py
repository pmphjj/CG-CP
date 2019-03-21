# coding: utf-8
from build_CP import Clinical_Pathway,Stages,CP_Variation
from Build_visits import Build_Visist_Order
from Orders import Orders_Dict


class CP_Analyzer(object):
    """
    临床路径变异分析器,对于特定临床路径和历史visit数据的变异分析类
    cp: 输入的临床路径
    visits: 输入的visit集合
    variation:
        "cp":
        "stages":每个stage的变异记录。{stage_num:CP_Variation()}
        "visits": 每个visit的变异记录。{visit_id:{}}
            "day_variation":每一天的变异医嘱代码, {日期:set()}
            "day_stage_map":表示每天属于的阶段,  {日期:(起始阶段,终止阶段)}

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
        self.variation = {"cp": {"visits_count":0}, "stages": stages_v, "visits": visits_v}

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
        #阶段-历史医嘱dict {阶段序号：set(该阶段历史医嘱代码)} 用于必选医嘱没选的检查
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

            #若当天剩余医嘱集day_item_code_set不为空，则将其加入到当天的首个阶段cur_stage_num的变异记录中【需要重点注意】
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
        if len(stat_var["stage"]) > 0:
            self.variation["cp"]["visits_count"] += 1
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

    def generate_recommendation(self,method="statistics"):
        """
        生成临床路径的更新建议，即每个阶段添加的医嘱集合
        :param method: 产生更新的方法。
            "statistics": 默认选择，基于统计值的方法。
        :return: 每个阶段添加的医嘱集合
        """
        if method == "statistics":
            return self.__analyze_by_stat()

        else:
            print("ERROR:No method : {}.".format(method))

    def __analyze_by_stat(self):
        #对于各阶段变异的统计值，过滤出现次数过少的医嘱后，选择排名靠前的医嘱作为推荐医嘱
        recommend_order_dict = dict() #{"stage_num":set(该阶段更新的医嘱代码)}
        for stage_num in self.variation["stages"]:
            var_info = self.variation["stages"][stage_num]
            #取新增变异中，排名前10的变异医嘱：
            sort_newadd_var_order =  sorted(var_info.newadd_variation.items(), key=lambda x: x[1],reverse=True)
            for item in sort_newadd_var_order:
                if item[1] < 3 or sort_newadd_var_order.index(item) >= 10:
                    break
                if stage_num not in recommend_order_dict:
                    recommend_order_dict[stage_num] = dict()
                recommend_order_dict[stage_num][item[0]] = item[1]
        return recommend_order_dict

    def show_var_info(self):
        # count = 0
        print("var visits count:{}".format(self.variation["cp"]["visits_count"]))
        for stage_num in sorted(self.cp.stage, key = lambda x: x[0]):
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


    def show_recommend(self, recommend_order):
        for key in sorted(recommend_order.keys()):
            print("stage:{},    {}".format(key, sorted( [(k,v) for k,v in recommend_order[key].items()], key=lambda x:x[1], reverse=True)))
            recommend_order_name = [(Orders_Dict.orders_dict[x].order_name, recommend_order[key][x]) for x in recommend_order[key]]
            print("stage:{},    {}".format(key, sorted(recommend_order_name, key=lambda x:x[1], reverse=True)))

if __name__ == "__main__":
    input_cp = Clinical_Pathway("4,621",3)
    input_visits = Build_Visist_Order("4,621",3)

    anlyzer = CP_Analyzer(input_cp,input_visits)
    anlyzer.analyze_visits()
    anlyzer.show_var_info()
    # print(len(Orders_Dict.orders_dict))
    # anlyzer.show_var_info_of_visit("2774502")


    print("\n+++++++++++++++++++++ CP Recommend Orders +++++++++++++++++++++++++++++")
    recommend_order = anlyzer.generate_recommendation()
    anlyzer.show_recommend(recommend_order)

    print("\n+++++++++++++++++++++ New Clinical Pathway +++++++++++++++++++++++++++++")
    comp_cp = input_cp
    comp_cp.stage["1"].add_orders("G11-555")
    comp_cp.stage["2"].add_orders("G06-220")
    comp_cp.stage["3"].add_orders("G11-51703")
    comp_cp.stage["4"].add_orders("G11-51703")
    comp_anly = CP_Analyzer(comp_cp,input_visits)
    comp_anly.analyze_visits()
    comp_anly.show_var_info()
    recommend_order = comp_anly.generate_recommendation()
    comp_anly.show_recommend(recommend_order)
