# coding: utf-8
from build_CP import Clinical_Pathway,Stages
from Build_visits import Build_Visist_Order



def get_variation_of_visit(input_cp, input_visit):
    """ 获取一个visit的变异情况
    :param input_cp: Clinical_Pathway类
    :param input_visit: Visit类
    :return: 变异情况
        分为两类：
            1.必选没选
            2.不在临床路径阶段内

    """
    sort_visit_order_list = sorted(input_visit.day_level_info.items(), key=lambda x: x[0])
    day_stage_map = []
    #划分阶段 ，暂不考虑路径定义的阶段长度与具体执行日期间的差异
    cur_stage_num = 0
    max_stage_num = input_cp.stage_nums
    for day_order in sort_visit_order_list:
        temp_stage_num = cur_stage_num
        #获取当天医嘱的编码集合
        day_item_code_set = set([x["CLINIC_ITEM_CODE"] for x in day_order[1]])
        while len(day_item_code_set) > 0 and temp_stage_num < max_stage_num:
            temp_stage_code_set = input_cp.get_stage_code(temp_stage_num)
            #当天剩余医嘱与当前阶段有交集，取其差集
            if  day_item_code_set.isdisjoint(temp_stage_code_set) == True:
                day_item_code_set = day_item_code_set.difference(temp_stage_code_set)
            else:
                #无交集，判断与下一阶段是否有交集，若仍无交集，则视其为变异
                if temp_stage_num == max_stage_num-1:
                    break
                temp_next_stage_code_set = input_cp.get_stage_code(temp_stage_num+1)
                if day_item_code_set.isdisjoint(temp_next_stage_code_set) == True:
                    day_item_code_set = day_item_code_set.difference(temp_next_stage_code_set)
                    temp_stage_num += 1
                else:
                    break

        #若当天剩余医嘱集day_item_code_set不为空，则将其加入到当天的首个阶段的变异记录中
        if len(day_item_code_set) > 0:
            input_cp.add_variation_to_stage(day_item_code_set,cur_stage_num)
        day_stage_map.append((cur_stage_num,temp_stage_num))
        cur_stage_num = temp_stage_num




def count_var(var_list):
    #TODO 统计所有visit的变异情况
    pass

def update_var_info_of_cp(input_cp,stat_var):
    #TODO 更新临床路径中记录的变异统计信息
    pass

if __name__ == "__main__":
    input_cp = Clinical_Pathway()
    input_visits = Build_Visist_Order()

    var_list = []
    for visit in input_visits.all_visits_dict.values():
        variation = get_variation_of_visit(input_cp, visit)
        var_list.append(variation)
    stat_var = count_var(var_list)
    cp = update_var_info_of_cp(input_cp,stat_var)

