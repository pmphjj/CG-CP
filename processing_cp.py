# coding: utf-8
from build_CP import Clinical_Pathway,Stages,CP_Variation
from Build_visits import Build_Visist_Order
from Orders import Orders_Dict
import operate

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
    def __init__(self, input_cp, input_visits):
        self.cp = input_cp
        self.visits = input_visits
        self.variation = dict()
        self.visits_info = dict()   # dict: visit_id ---> {"day_stage_map":dict(),"day_level_info":dict()}
        self.__init_variation()

    def __init_variation(self):
        '''
            初始化变异统计信息
            self.visits_info 的结构为 dict: visit_id ---> {"day_stage_map":dict(),"day_level_info":dict()}
            self.variation 的结构为  {"cp": {"visits_count":0}, "stages": stages_v, "visits": visits_v}
                其中 stages_v = dict: stage_sqno ---> CP_Variation
                visits = dict: visit_id ---> {"day_variation":dict()【date--->Stage_variation()】, "day_stage_map":dict()【date ---> (start_stage, end_stage)】}
        :return: 
        '''

        for visit in self.visits.all_visits_dict.values():
            stat_var = self.get_visit_info(visit)

            # 往 self.visits_info 加入内容
            self.visits_info[visit.visit_id] = stat_var

        # 获取异常情况
        self.variation = self.get_newCP_variation(self.cp)

    def get_visit_info(self, input_visit):
        '''
            获取每天的基本信息以及与阶段的映射情况
            stat_var = {"day": dict(), "day_stage_map": dict(), "stage": dict([(x, CP_Variation()) for x in self.cp.stage]), "day_level_info": dict()}
        :param input_visit: 
        :return: 
        '''
        sort_visit_order_list = sorted(input_visit.day_level_info.items(), key=lambda x: x[0])
        stat_var = {"day": dict(), "day_stage_map": dict(), "stage": dict([(x, CP_Variation()) for x in self.cp.stage]),
                    "day_level_info": dict()}
        cur_stage_num = 1
        max_stage_num = self.cp.stage_nums
        # 天-阶段映射列表，列表下标为天序号，值为该天的阶段范围(起始阶段，终止阶段)
        day_stage_map = dict()
        # 阶段-历史医嘱dict {阶段序号：set(该阶段历史医嘱代码)} 用于必选医嘱没选的检查
        stage_order_dict = dict([(x, set()) for x in range(1, max_stage_num + 1)])

        # 划分阶段 ，暂不考虑路径定义的阶段长度与具体执行日期间的差异
        for day_order in sort_visit_order_list:

            day_time = day_order[0]

            # 获取day_level_info的信息，dict--- day_time: [orders_detail]; BY:Wayne
            stat_var["day_level_info"][day_time] = day_order[1]

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

        stat_var["day_stage_map"] = day_stage_map

        return stat_var

    '''
    def get_stage_by_split_visit(self, input_visit):
        """
        获取输入的visit的天与阶段的映射表
        :param input_visit: Visit类
        :return: 天与阶段的映射表{ "天序号":[起始阶段，终止阶段]}
        """
        sort_visit_order_list = sorted(input_visit.day_level_info.items(), key=lambda x: x[0])
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
   
    def get_variation_of_visit(self, input_visit):

        """ 获取一个visit的变异情况
            变异情况分为两类：
                    1.必选没选
                    2.不在临床路径阶段内
        :param input_cp: Clinical_Pathway类
        :param input_visit: Visit类
        :return: stat_var, {"day":每天的变异医嘱代码，"day_stage_map":天与阶段的映射表 ,"stage":各阶段的变异情况, "day_level_info":各阶段的医嘱详情【dict格式】}
        """

        sort_visit_order_list = sorted(input_visit.day_level_info.items(), key=lambda x: x[0])
        stat_var = {"day":dict(),"day_stage_map":dict(),"stage":dict(),"day_level_info":dict()}
        cur_stage_num = 1
        max_stage_num = self.cp.stage_nums
        #天-阶段映射列表，列表下标为天序号，值为该天的阶段范围(起始阶段，终止阶段)
        day_stage_map = dict()
        #阶段-历史医嘱dict {阶段序号：set(该阶段历史医嘱代码)} 用于必选医嘱没选的检查
        stage_order_dict = dict([(x,set()) for x in range(1,max_stage_num+1)])

        #划分阶段 ，暂不考虑路径定义的阶段长度与具体执行日期间的差异
        for day_order in sort_visit_order_list:

            day_time = day_order[0]

            # 获取day_level_info的信息，dict--- day_time: [orders_detail]; BY:Wayne
            stat_var["day_level_info"][day_time] = day_order[1]

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
    '''

    def analyze_visits(self):
        self.__init_variation()
        for visit in self.visits.all_visits_dict.values():
            # stat_var = self.get_variation_of_visit(visit)
            # self.__update_variation_info(stat_var,visit.visit_id)

            stat_var = self.get_visit_info(visit)

            # 往 self.visits_info 加入内容
            self.visits_info[visit.visit_id] = stat_var

        # 获取异常情况
        self.variation = self.get_newCP_variation(self.cp)

    def get_newCP_variation(self, new_cp):
        """
            输入临床路径，输出根据初始化时的映射得到的异常情况
            返回的是一个new_variation的字典，格式与self.variation一样
            {"cp": {"visits_count":0}, "stages": stages_v, "visits": visits_v}
        :param new_cp: 
        :return: 
        """
        stages_v = dict([(x, CP_Variation()) for x in self.cp.stage])
        visits_v = dict()
        for visit_id in self.visits.all_visits_dict:
            visits_v[visit_id] = {"day_variation":dict(),"day_stage_map":dict()}
        new_variation = {"cp": {"visits_count":0}, "stages": stages_v, "visits": visits_v}

        for visit_id, info in self.visits_info.items():
            #info(dict): visit_id ---> {"day":dict(),"day_stage_map":dict(),"stage":dict(),"day_level_info":dict()}

            new_variation["visits"][visit_id]["day_stage_map"] = info["day_stage_map"]

            date_list = sorted(info["day_stage_map"].keys())
            has_Variation = False   # 判断该次Visit是否有变异
            for date in date_list:

                # 该结构体有4个变量，分别是stage_num, newadd_variation, noselect_variation, dosage_variation
                day_variation = operate.calculate_stage_variation(info["day_stage_map"][date], new_cp, info["day_level_info"][date])

                # 更新new_variation的内容，"stages"和"visits"
                new_variation["visits"][visit_id]["day_variation"][date] = day_variation

                # 更新日期对应第一个阶段的总异常
                new_variation["stages"][day_variation.stage_num].update_variation_num(day_variation.variation_num)

                # if day_variation.stage_num == "3":
                #     print(day_variation.variation_num)
                #     print(day_variation.newadd_variation)
                #     print(day_variation.noselect_variation)
                #     print(day_variation.planday_variation)
                #     print(day_variation.freq_variation)
                #     print(day_variation.dosage_variation)
                #     print()


                # 更新新增变异
                if len(day_variation.newadd_variation)!=0:
                    has_Variation = True
                    for order_code, nums in day_variation.newadd_variation.items():
                        new_variation["stages"][day_variation.stage_num].newadd_variation[order_code] += nums
                        new_variation["stages"][day_variation.stage_num].update_newadd_num(nums)

                # 更新必选项未选变异
                if len(day_variation.noselect_variation)!=0:
                    has_Variation = True
                    for order_code in day_variation.noselect_variation:
                        new_variation["stages"][day_variation.stage_num].noselect_variation[order_code] += nums
                        new_variation["stages"][day_variation.stage_num].update_noselect_num(nums)

                # 更新剂量变异
                if len(day_variation.dosage_variation) != 0:
                    has_Variation = True
                    for order_code in day_variation.dosage_variation:
                        new_variation["stages"][day_variation.stage_num].dosage_variation[order_code] += nums
                        new_variation["stages"][day_variation.stage_num].update_dosage_num(nums)

                # 更新天数变异
                if len(day_variation.planday_variation) != 0:
                    has_Variation = True
                    for order_code in day_variation.planday_variation:
                        new_variation["stages"][day_variation.stage_num].planday_variation[order_code] += nums
                        new_variation["stages"][day_variation.stage_num].update_planday_num(nums)

                # 更新频率变异
                if len(day_variation.freq_variation) != 0:
                    has_Variation = True
                    for order_code in day_variation.freq_variation:
                        new_variation["stages"][day_variation.stage_num].freq_variation[order_code] += nums
                        new_variation["stages"][day_variation.stage_num].update_freq_num(nums)

            # 更新new_variation的cp，visits_count
            if has_Variation:
                new_variation["cp"]["visits_count"] += 1

        return new_variation

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

    def generate_recommendation(self, method="statistics", threshold=0.05, most_count=2):
        """
        生成临床路径的更新建议，即每个阶段添加的医嘱集合
        :param method: 产生更新的方法。
            "statistics": 默认选择，基于统计值的方法。
        :return: 每个阶段添加的医嘱集合
            dict()格式
            stage_num ---> ['G06-220', 'G11-503', 'G11-555', 'U76-100', 'U76-K01']
        """
        if method == "statistics":
            return self.__analyze_by_stat()
        elif method == "fpgrowth":
            return self.__analyze_by_fpgrowth(threshold=threshold, most_count=most_count)
        else:
            print("ERROR:No method : {}.".format(method))

    def __analyze_by_stat(self):
        '''
        :return: 对于各阶段变异的统计值，过滤出现次数过少的医嘱后，选择排名靠前的医嘱作为推荐医嘱
            dict()格式
            stage_num ---> ['G06-220', 'G11-503', 'G11-555', 'U76-100', 'U76-K01']
        '''
        recommend_order_dict = dict()       #{"stage_num":set(该阶段更新的医嘱代码)}
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

            # 新增 BY:Wayne, 修改返回格式
            if stage_num in recommend_order_dict:
                recommend_order_dict[stage_num] = recommend_order_dict[stage_num].keys()

        return recommend_order_dict

    def __analyze_by_fpgrowth(self, threshold=0.05, most_count=2):
        """
            使用频繁模式挖掘算法，得到推荐的医嘱集合
        :return: 返回的格式为:
            dict()格式
            stage_num ---> ['G06-220', 'G11-503', 'G11-555', 'U76-100', 'U76-K01']
        """

        visit_variation = self.get_each_stage_visits_variation()
        stage_frequent = operate.get_all_stage_frequent_pattern(visit_variation, threshold, most_count)

        recommend_order_dict = operate.selected_recomend_orders(self.cp, self.visits, self, stage_frequent)

        return recommend_order_dict

    def show_var_info(self, all_variation=""):
        # count = 0

        if all_variation == "":
            all_variation = self.variation

        print("var visits count:{}".format(all_variation["cp"]["visits_count"]))
        for stage_num in sorted(self.cp.stage, key = lambda x: x[0]):
            variation = all_variation["stages"][stage_num]
            print("阶段：{}, 总变异数:{},  新增变异数:{},  必选未选变异数:{},  剂量变异数:{}, 天数变异数：{}, 频率变异数:{}".format(
                stage_num, variation.variation_num,variation.newadd_variation_num, variation.noselect_variation_num, variation.dosage_variation_num,
                variation.planday_variation_num, variation.freq_variation_num))

            print("新增变异：", [(k,v) for k,v in variation.newadd_variation.items()] )
            print("必选未选变异：", [(k,v) for k,v in variation.noselect_variation.items()])
            print("剂量变异：", [(k,v) for k,v in variation.dosage_variation.items()])
            print("天数变异：", [(k, v) for k, v in variation.planday_variation.items()])
            print("频率变异：", [(k, v) for k, v in variation.freq_variation.items()])

            print("")

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
        recommend_str = ""
        for key in sorted(recommend_order.keys()):
            order_list = list(recommend_order[key])
            print("stage:{},    {}".format(key, order_list))
            recommend_str += "stage:{},    {}".format(key, order_list) + "\n"

            recommend_order_name = [(Orders_Dict.orders_dict[order_list[x]].order_name, order_list[x]) for x in range(len(order_list))]
            print("stage:{},    {}".format(key, sorted(recommend_order_name, key=lambda x:x[1], reverse=True)))
            recommend_str += "stage:{},    {}".format(key, sorted(recommend_order_name, key=lambda x:x[1], reverse=True)) + "\n"

        return recommend_str
    def get_each_stage_visits_variation(self):
        """
            处理self.variation["visits"]的所有visits
            每一个visits的结构为 {"day_variation":dict(),"day_stage_map":dict()}
            获取该分析器中每一个阶段内不同visit的变异情况，返回类型如下：
            dict{
                "1" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage1
                "2" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage2
                "3" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage3
                ...
            }
            
        :return: 
        BY： Wayne
        """

        visits_variation = dict([ (stage_num+1, []) for stage_num in range(self.cp.stage_nums) ])

        # for visit_id in ["2726954", "3216993"]:
        for visit_id in self.visits.all_visits_dict.keys():
            temp_variation = dict([ (stage_num+1, set()) for stage_num in range(self.cp.stage_nums) ])
            visit_item = self.variation['visits'][visit_id]

            # 将【新增变异、必选项未选变异、剂量变异、天数变异、频率变异】同等考虑处理
            # day_item 是operate.py文件中的 Stage_Variation类， 包含变量stage_num, newadd_variation, noselect_variation, dosage_variation, planday_variation, freq_variation
            for date, day_item in visit_item["day_variation"].items():
                stage = int(day_item.stage_num)
                temp_variation[stage] = (temp_variation[stage].union(day_item.newadd_variation) )
                temp_variation[stage] = (temp_variation[stage].union(day_item.noselect_variation))
                temp_variation[stage] = (temp_variation[stage].union(day_item.dosage_variation))
                temp_variation[stage] = (temp_variation[stage].union(day_item.planday_variation))
                temp_variation[stage] = (temp_variation[stage].union(day_item.freq_variation))

                # print(stage, temp_variation[stage] , "\n")

            for stage, stage_items in temp_variation.items():
                visits_variation[stage].append(list(stage_items))
        return visits_variation

if __name__ == "__main__":
    input_cp = Clinical_Pathway("4,621", "3", "data/cp_info.csv", "data/cp_stage.csv", "data/cp_detail_order.csv", "data/cp_detail_info.csv")
    input_visits = Build_Visist_Order("4,621", "3", "data/orders.csv")

    anlyzer = CP_Analyzer(input_cp,input_visits)
    anlyzer.show_var_info()

    new_variation = anlyzer.get_newCP_variation(input_cp)
    anlyzer.show_var_info(new_variation)

    print("\n+++++++++++++++++++++ Frequent Update CP +++++++++++++++++++++++++++++")
    # 获取推荐的医嘱集
    threshold = 0.05    # 变异项出现的频率
    most_count = 4      # 对每一阶段，最多推荐新增医嘱数目
    recommend_order = anlyzer.generate_recommendation("fpgrowth", threshold=threshold, most_count=most_count)
    # recommend_order = anlyzer.generate_recommendation()
    print("\n推荐更新:")
    anlyzer.show_recommend(recommend_order)

    # 将推荐的医嘱集加入临床路径并比较
    operate.add_orders_and_show(input_cp, anlyzer, recommend_order)

    print("\n+++++++++++++++++++++ Frequent Update CP +++++++++++++++++++++++++++++")

    # print("\n+++++++++++++++++++++ Frequent Update CP +++++++++++++++++++++++++++++")
    # # 找到每一个visit每一个阶段的变异，以及每一个阶段的频繁项集
    # visit_variation = anlyzer.get_each_stage_visits_variation()
    # stage_frequent = operate.get_all_stage_frequent_pattern(visit_variation,0.05)
    #
    # # 找到每一个阶段最佳新增医嘱
    # operate.selected_recomend_orders(input_cp, input_visits, anlyzer, stage_frequent)
    #
    # print("+++++++++++++++++++++ Frequent Update CP +++++++++++++++++++++++++++++\n")

    # comp_cp = input_cp
    # comp_cp.stage["3"].add_orders("G11-555")
    # comp_anly = CP_Analyzer(comp_cp, input_visits)
    # comp_anly.analyze_visits()
    # operate.evaluation(anlyzer, comp_anly, 3)
    # comp_anly.show_var_info()


    # 添加新的医嘱，创建新的临床路径
    # print("\n+++++++++++++++++++++ CP Recommend Orders +++++++++++++++++++++++++++++")
    # recommend_order = anlyzer.generate_recommendation()
    # anlyzer.show_recommend(recommend_order)
    #
    # print("\n+++++++++++++++++++++ New Clinical Pathway +++++++++++++++++++++++++++++")
    # comp_cp = input_cp
    # comp_cp.stage["1"].add_orders("G11-555")
    # comp_cp.stage["1"].add_orders("G06-220")
    # comp_cp.stage["1"].add_orders("U76-100")
    # comp_cp.stage["2"].add_orders("F04-013")
    # comp_cp.stage["3"].add_orders("G11-51703")
    # comp_cp.stage["4"].add_orders("G11-51703")
    # comp_anly = CP_Analyzer(comp_cp,input_visits)
    # comp_anly.analyze_visits()
    # comp_anly.show_var_info()
    # recommend_order = comp_anly.generate_recommendation()
    # comp_anly.show_recommend(recommend_order)
