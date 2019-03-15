# coding: utf-8
from build_CP import Clinical_Pathway,Stages
from Build_visits import Build_Visist_Order


class CP_Analyzer(object):
    """
    临床路径变异分析器
    """
    def __init__(self,input_cp):
        self.cp = input_cp

    def get_variation_of_visit(self, input_visit):
        """ 获取一个visit的变异情况
        :param input_cp: Clinical_Pathway类
        :param input_visit: Visit类
        :return: 变异情况
            分为两类：
                1.必选没选
                2.不在临床路径阶段内

        """
        sort_visit_order_list = sorted(input_visit.day_level_info.items(), key=lambda x: x[0])
        cur_stage_num = 1
        max_stage_num = self.cp.stage_nums
        #天-阶段映射列表，列表下标为天序号，值为该天的阶段范围(起始阶段，终止阶段)
        day_stage_map = []
        #阶段-历史医嘱dict {阶段序号：set(该阶段历史医嘱代码)}
        stage_order_dict = dict([(x,set()) for x in range(max_stage_num)])
        #划分阶段 ，暂不考虑路径定义的阶段长度与具体执行日期间的差异
        for day_order in sort_visit_order_list:
            temp_stage_num = cur_stage_num
            #获取当天医嘱的编码集合
            day_item_code_set = set([x["CLINIC_ITEM_CODE"] for x in day_order[1]])
            while len(day_item_code_set) > 0 and temp_stage_num < max_stage_num:
                temp_stage_code_set = self.cp.get_stage_code(temp_stage_num)
                #当天剩余医嘱与当前阶段有交集，取其差集
                intersec_set = day_item_code_set.intersection(temp_stage_code_set)
                if  len(intersec_set) > 0:
                    stage_order_dict[temp_stage_num] = stage_order_dict[temp_stage_num].union(intersec_set)
                    day_item_code_set = day_item_code_set.difference(temp_stage_code_set)
                else:
                    #无交集，判断与下一阶段是否有交集，若仍无交集，则视其为变异
                    if temp_stage_num == max_stage_num-1:
                        break
                    temp_next_stage_code_set = self.cp.get_stage_code(temp_stage_num+1)
                    next_intersec_set = day_item_code_set.intersection(temp_next_stage_code_set)
                    if len(next_intersec_set) > 0:
                        stage_order_dict[temp_stage_num+1] = stage_order_dict[temp_stage_num+1].union(next_intersec_set)
                        day_item_code_set = day_item_code_set.difference(temp_next_stage_code_set)
                        temp_stage_num += 1
                    else:
                        break

            #若当天剩余医嘱集day_item_code_set不为空，则将其加入到当天的首个阶段的变异记录中
            if len(day_item_code_set) > 0:
                self.cp.add_variation_to_stage(day_item_code_set,cur_stage_num)
            day_stage_map.append((cur_stage_num,temp_stage_num))
            cur_stage_num = temp_stage_num

        #依据天-阶段的对应关系，搜索必选没选的变异医嘱 需要CP类提供一个required_order_dict {阶段序号：set(该阶段必需的医嘱代码)}
        for stage_num in self.cp.required_order_dict:
            required_set = self.cp.required_order_dict[stage_num]
            compared_set = stage_order_dict[stage_num]
            intersec_set = required_set.intersection(compared_set)
            if required_set != intersec_set:
                self.cp.add_variation_to_stage(required_set.difference(intersec_set),stage_num)


    def analyze_visits(self,input_visits):
        for visit in input_visits.all_visits_dict.values():
            self.get_variation_of_visit(visit)

    def show_var_info(self):
        # count = 0
        for stage_num in self.cp.stage:
            variation = self.cp.stage[stage_num].stage_variation
            print("阶段：{}, 总变异数:{},  新增变异数:{},  必选未选变异数:{}".format(
                stage_num,variation.variation_num,variation.newadd_variation_num,variation.noselect_variation_num))
            print(variation.newadd_variation)
            print(variation.noselect_variation)

    def update_var_info_of_cp(input_cp,stat_var):
        #TODO 更新临床路径中记录的变异统计信息
        pass

if __name__ == "__main__":
    input_cp = Clinical_Pathway("4,621",3)
    input_visits = Build_Visist_Order("4,621",3)

    anlyzer = CP_Analyzer(input_cp)
    anlyzer.analyze_visits(input_visits)
    anlyzer.show_var_info()

    #
    # var_list = []
    # for visit in input_visits.all_visits_dict.values():
    #     variation = get_variation_of_visit(input_cp, visit)
    #     var_list.append(variation)
    # stat_var = count_var(var_list)
    # cp = update_var_info_of_cp(input_cp,stat_var)

