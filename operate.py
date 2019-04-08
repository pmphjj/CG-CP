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
    :return: 返回一个dict的结果，stage_num --> list[tuple( (医嘱code频繁项), 频繁项出现次数)), tuple( (医嘱code频繁项), 频繁项出现次数))]
    1 -->  [(('G11-555',), 20), (('U76-100',), 11), (('G11-555', 'U76-100'), 10), (('G11-503',), 9)]
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

def selected_recomend_orders(cp, input_visits, cp1_analyzer, stage_frequent):
    """
        根据频繁模式挖掘的候选项，选出每一个阶段的最佳医嘱集合
    :param cp: 
    :param input_visits: 
    :param stage_frequent: 
    :return: 返回最佳方案，最佳方案
            stage_num ---> ['G06-220', 'G11-503', 'G11-555', 'U76-100', 'U76-K01']
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
            # print("阶段：{}，增加的异常为{}，改变的异常数为{}".format(stage, items, change_variation))

            if change_variation > best_score:
                best_score = change_variation
                best_item = items

            # 删除新增的医嘱
            for item in items:
                new_cp.stage[str(stage)].delete_orders(item)

        # print("阶段BEST：{}，增加的异常为{}，改变的异常数为{}\n".format(stage, best_item, best_score))
        best[stage].extend(best_item)


    # 更新每一个阶段的最优方案进临床路径
    for stage, items in best.items():
        print(stage, [ (item, Orders_Dict.orders_dict[item].order_name) for item in items] )
        for item in items:
            new_cp.stage[str(stage)].add_orders(item)

    # comp_anly = CP_Analyzer(new_cp, input_visits)
    # comp_anly.analyze_visits()
    # compare_CP(cp1_analyzer, comp_anly)

    return best

def calculate_stage_variation_(stage_list, cp, day_orders):
    """
        获取某一天对应阶段的3中变异情况，新增变异，必选项未选变异以及剂量变异
    :param stage_list: 该天对应的阶段list，变异加入该天对应的第一个阶段
    :param cp: 模板的临床路径类
    :param day_orders: 这一天的用药情况，输入的是一个 list[], 里面存放的是每一个医嘱的详细信息dict格式, 样例如下
            用量字段是AMOUNT
            {'ITEM_CODE': 'G06-201', 'ORDER_NO': '14787268', 'CLINIC_ITEM_CODE': 'G06-201', 'STOP_ORDER_DOCTOR_NAME': '郭丽婧', 'INPUT_ORDER_DOCTOR_EMID': 'A02305', 'INPATIENT_ID': '181015232', 'PLAN_DAYS': '0', 'ORDER_INPUT_TIME': '07/20/2018 11:11:26', 'VISIT_ID': '2509961', 'ORDER_NAME': '普食', 'ORDER_CLASS': '膳食', 'STOP_ORDER_DOCTOR_ID': '0771', 'ORDER_PLAN_STOP_TIME': '', 'DURATION_UNITS': '', 'COMPOUND_MARK': 'N', 'PERFORM_DEPT': 'G', 'DATE': '07/20/2018', 'PATIENT_ID': '10405624', 'FORM_NO': '', 'ORDER_START_TIME': '07/20/2018 11:12:26', 'BILL_STATUS': 'D', 'INSURANCE_TYPE': '1', 'CONFIRM_ORDER_DOCTOR_EMID': 'A02305', 'STOP_ORDER_DOCTOR_EMID': '', 'ACTUAL_DAYS': '', 'ROUTE': '', 'ORDER_GROUP_NO': '0', 'AMOUNT': '1', 'FREQ_CODE': '', 'DURATION': '', 'ORDER_STATUS': 'E', 'INPUT_ORDER_DOCTOR_ID': '0771', 'ORDER_STOP_TIME': '07/23/2018 12:01:35', 'FORM_TYPE': '3', 'ORDER_DEPT': '12100', 'BILLING_ATTR': '0', 'OUTOFHOSPITAL_FLAG': '1', 'ORDER_SIG_STATUS': '', 'CONFIRM_ORDER_DOCTOR_NAME': '郭丽婧', 'VISIT_TYPE': 'I', 'INPUT_ORDER_DOCTOR_NAME': '郭丽婧', 'REPEAT_INDICATOR': '1', 'CONFIRM_ORDER_DOCTOR_ID': '0771', 'ORDER_CONFIRM_TIME': '07/20/2018 11:12:26', 'AMOUNT_UNIT': '项', 'INSTRUCTION': '', 'EXECUTION_CLASS': '', 'SERIAL_NO_LATEST_TIME': '0001/1/1'}
    :return: 
        返回一个class, 包含的参数有stage_num, newadd_variation, noselect_variation, dosage_variation
        后面3个参数都是set()
    """

    # 空类可以表示为一个结构体
    class Stage_variation():
        pass

    stage_variation = Stage_variation()
    stage_variation.stage_num = min(stage_list)
    stage_variation.newadd_variation = set()
    stage_variation.noselect_variation = set()
    stage_variation.dosage_variation = set()

    # 获取stage_list中所有阶段中临床路径定义的医嘱, 并且单独抽取出必选项医嘱
    cp_orders = dict()
    required_orders = set()     # 必选医嘱
    for stage_no in stage_list:
        stage_orders = cp.stage[stage_no].stage_orders_detail   #字典,该阶段包含的医嘱code ---> 医嘱的详细信息(Basic_Order_Info类)

        # 此处未考虑对于不同阶段的同一种医嘱，使用剂量不同的情况
        for key, value in stage_orders.items():
            if key in cp_orders:
                pass    # 若考虑剂量，可以将剂量小的覆盖
            else:
                cp_orders[key] = value

            # 若属于必选医嘱，则将其code加入required_orders
            # TODO

    # 变异该天所用的医嘱，判断是否是新增变异还是剂量符合要求
    day_order_code_set = set()  # 该天使用医嘱的code集合，用于判断必选项未选
    for order in day_orders:
        order_code = order.CLINIC_ITEM_CODE
        day_order_code_set.add(order_code)

        # 该code不在cp_orders里面，则属于新增变异
        if order_code not in cp_orders:
            stage_variation.newadd_variation.add(order_code)
        # 在cp_orders里面则判断是否属于剂量变异
        else:
            # 比较剂量, 注意需要考虑有些临床路径定义的医嘱内AMOUNT字段为空
            cp_order_detail = cp_orders[order_code]

            # cp中定义的剂量为空
            if not cp_order_detail.order_amount:
                continue
            else:
                # 实际使用剂量大于cp中定义的剂量, 则将其加入dosage_variation异常
                if cp_order_detail.order_amount < order.AMOUNT:
                    stage_variation.dosage_variation.add(order_code)

    # 对于必选项未选，则加入异常
    for order in required_orders:
        if order not in day_order_code_set:
            stage_variation.noselect_variation.add(order)

    return stage_variation








