import pyfpgrowth
from processing_cp import CP_Analyzer
from Orders import Orders_Dict
import copy

def compare_CP(cp1_analyzer, cp2_analyzer):
    '''
        比较两个临床路径变异情况
    :param cp1_analyzer: 
    :param cp2_analyzer: 
    :return: 
    '''
    print("CP1的变异来访次数:{}, CP2的变异来访次数:{}".format(cp1_analyzer.variation["cp"]["visits_count"], cp2_analyzer.variation["cp"]["visits_count"]))
    for stage_num in sorted(cp1_analyzer.cp.stage, key=lambda x: x[0]):
        variation1 = cp1_analyzer.variation["stages"][stage_num]
        variation2 = cp2_analyzer.variation["stages"][stage_num]
        print("CP1阶段：{}, 总变异数:{},  新增变异数:{},  必选未选变异数:{}".format(
            stage_num, variation1.variation_num, variation1.newadd_variation_num, variation1.noselect_variation_num))

        print("CP2阶段：{}, 总变异数:{},  新增变异数:{},  必选未选变异数:{}".format(
            stage_num, variation2.variation_num, variation2.newadd_variation_num, variation2.noselect_variation_num))

        print("阶段：{}, 总变异数变化:{},  新增变异数变化:{},  必选未选变异数变化:{}".format(
            stage_num, variation1.variation_num-variation2.variation_num, variation1.newadd_variation_num-variation2.newadd_variation_num, variation1.noselect_variation_num-variation2.noselect_variation_num))

        print("")

def fp_growth(items, supported=0.5):
    """
        FP—Growth的频繁模式挖掘
    :param items: 格式为 list[ list[],list[], ... ,]
    :param supported:支持度 , 默认为0.5
    :return: 
    """

    supported_num = int( len(items) * supported )
    patterns = pyfpgrowth.find_frequent_patterns(items, supported_num)

    return sorted(patterns.items(), key=lambda x: x[1], reverse = True)

def get_all_stage_frequent_pattern(visits_variation, supported=0.5):
    """
        获取每一个阶段的频繁模式
    :param visits_variation: dict{
                "1" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage1
                "2" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage2
                "3" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage3
                ...
            }
    :return: 
    """

    frequent_patterns = dict()

    for stage, items in visits_variation.items():
        frequent_patterns[stage] = fp_growth(items, supported)

    return frequent_patterns

def evaluation(cp1_analyzer, cp2_analyzer, stage):
    """
        评价cp2_analyzer相比于cp1_analyzer的异常减少数
    :param cp1_analyzer: 
    :param cp2_analyzer: 
    :param stage: 
    :return: 
    """
    variation1 = cp1_analyzer.variation["stages"][str(stage)]
    variation2 = cp2_analyzer.variation["stages"][str(stage)]

    return variation1.variation_num - variation2.variation_num


def update_CP(cp, input_visits, cp1_analyzer, stage_frequent):
    """
        修改一个临床路径，使其每一个阶段的变异数最佳
    :param cp: 
    :param input_visits: 
    :param stage_frequent: 
    :return: 
    """

    new_cp = copy.deepcopy(cp)
    best = dict([(stage+1, []) for stage in range(new_cp.stage_nums) ])

    for index in range(cp.stage_nums):
        stage = index + 1
        best_score = 0
        best_item = []
        for items, num in stage_frequent[stage]:
            for item in items:
                new_cp.stage[str(stage)].add_orders(item)

            comp_anly = CP_Analyzer(new_cp, input_visits)
            comp_anly.analyze_visits()

            change_variation =  evaluation(cp1_analyzer, comp_anly, stage)
            print("阶段：{}，增加的异常为{}，改变的异常数为{}".format(stage, items, change_variation))

            if change_variation > best_score:
                best_score = change_variation
                best_item = items

            # 删除新增的医嘱
            for item in items:
                new_cp.stage[str(stage)].delete_orders(item)

        print("阶段BEST：{}，增加的异常为{}，改变的异常数为{}\n".format(stage, best_item, best_score))
        best[stage].extend(best_item)


    # 更新每一个阶段的最优方案进临床路径
    for stage, items in best.items():
        print(stage, [ (item, Orders_Dict.orders_dict[item].order_name) for item in items] )
        for item in items:
            new_cp.stage[str(stage)].add_orders(item)
    comp_anly = CP_Analyzer(new_cp, input_visits)
    comp_anly.analyze_visits()
    compare_CP(cp1_analyzer, comp_anly)