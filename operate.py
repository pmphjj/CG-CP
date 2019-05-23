import pyfpgrowth
from processing_cp import CP_Analyzer
from Orders import Orders_Dict
import copy
from collections import defaultdict

def compare_CP(cp1_variation, cp2_variation, stage_num_list):
    '''
        比较两个临床路径变异情况
    :param cp1_variation: CP_Analyzer类中的variation结构，{"cp": {"visits_count":0}, "stages": stages_v, "visits": visits_v} 
    :param cp2_vatiation: 同上
    :return: 
    '''
    print("CP1的变异来访次数:{}, CP2的变异来访次数:{}".format(cp1_variation["cp"]["visits_count"], cp2_variation["cp"]["visits_count"]))
    for stage_num in stage_num_list:
        variation1 = cp1_variation["stages"][stage_num]
        variation2 = cp2_variation["stages"][stage_num]
        print("CP1阶段：{}, 总变异数:{},  新增变异数:{},  必选未选变异数:{}, 剂量变异数:{}".format(
            stage_num, variation1.variation_num, variation1.newadd_variation_num, variation1.noselect_variation_num, variation1.dosage_variation_num))

        print("CP2阶段：{}, 总变异数:{},  新增变异数:{},  必选未选变异数:{}, 剂量变异数:{}".format(
            stage_num, variation2.variation_num, variation2.newadd_variation_num, variation2.noselect_variation_num, variation2.dosage_variation_num))

        print("阶段：{}, 总变异数变化:{},  新增变异数变化:{},  必选未选变异数变化:{}, 剂量变异数变化:{}".format(
            stage_num, variation1.variation_num-variation2.variation_num, variation1.newadd_variation_num-variation2.newadd_variation_num, variation1.noselect_variation_num-variation2.noselect_variation_num,
            variation1.dosage_variation_num-variation2.dosage_variation_num))

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

def get_all_stage_frequent_pattern(visits_variation, supported=0.5, most_count=5):
    """
        获取每一个阶段的频繁模式
    :param visits_variation: dict{
                "1" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage1
                "2" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage2
                "3" --> [ [Visit1_variation_orders_sequence], [Visit2_variation_orders_sequence], ... , ], # Stage3
                ...
            }
    :param 支持度; num(异常子项) / num(异常项)
    :param 子项最多医嘱数; 新增的医嘱项最多包含医嘱的数目，默认为5个
    :return: 返回一个dict的结果，stage_num --> list[tuple( (医嘱code频繁项), 频繁项出现次数)), tuple( (医嘱code频繁项), 频繁项出现次数))]
    1 -->  [(('G11-555',), 20), (('U76-100',), 11), (('G11-555', 'U76-100'), 10), (('G11-503',), 9)]
    """

    frequent_patterns = dict()

    for stage, items in visits_variation.items():
        frequent_patterns[stage] = fp_growth(items, supported)

    for key, value in frequent_patterns.items():
        index = 0
        while index < len(value):
            if len(value[index][0]) > most_count:
                value.pop(index)
            else:
                index += 1
    return frequent_patterns

def evaluation(cp1_variation, cp2_variation, stage):
    """
        评价cp2_analyzer相比于cp1_analyzer的异常减少数
    :param cp1_analyzer: 
    :param cp2_analyzer: 
    :param stage: 
    :return: 
    """
    # variation1 = cp1_analyzer.variation["stages"][str(stage)]
    # variation2 = cp2_analyzer.variation["stages"][str(stage)]

    variation1 = cp1_variation["stages"][str(stage)]
    variation2 = cp2_variation["stages"][str(stage)]

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

    old_variation = cp1_analyzer.get_newCP_variation(cp)

    for index in range(cp.stage_nums):
        stage = index + 1
        best_score = 0
        best_item = []
        for items, num in stage_frequent[stage]:
            for item in items:
                new_cp.stage[str(stage)].add_orders(item)

            # comp_anly = CP_Analyzer(new_cp, input_visits)
            # comp_anly.analyze_visits()

            new_variation = cp1_analyzer.get_newCP_variation(new_cp)

            # change_variation =  evaluation(cp1_analyzer.variation, new_variaiont, stage)
            change_variation = evaluation(old_variation, new_variation, stage)
            print("阶段：{}，增加的医嘱为{}，改变的异常数为{}".format(stage, [(item, Orders_Dict.get_orders(item).order_name) for item in items], change_variation))

            if change_variation > best_score:
                best_score = change_variation
                best_item = items

            # 删除新增的医嘱
            for item in items:
                new_cp.stage[str(stage)].delete_orders(item)

        print("阶段BEST：{}，增加的医嘱为{}，改变的异常数为{}\n".format(stage, [(item, Orders_Dict.get_orders(item).order_name) for item in best_item], best_score))
        best[stage].extend(best_item)


    # 更新每一个阶段的最优方案进临床路径
    for stage, items in best.items():
        # print(stage, [ (item, Orders_Dict.orders_dict[item].order_name) for item in items] )
        for item in items:
            new_cp.stage[str(stage)].add_orders(item)

    # comp_anly = CP_Analyzer(new_cp, input_visits)
    # comp_anly.analyze_visits()
    # compare_CP(cp1_analyzer, comp_anly)

    return best

def calculate_stage_variation(stage_list, cp, day_orders):
    """
        获取某一天对应阶段的5种变异情况，新增变异、必选项未选变异、剂量变异、天数变异、频率变异
        新增变异： 出现定义中没有出现的医嘱
        必选项未选变异： 该天对应的所有阶段的必选医嘱没有选择
        剂量变异：   医嘱的规定剂量与临床路径中的定义不同
        天数变异：   医嘱的规定天数与临床路径中的定义不同
        频率变异：   医嘱的规定频率与临床路径中的定义不同
        
    :param stage_list: 该天对应的阶段list，变异加入该天对应的第一个阶段 [start, end]
    :param cp: 模板的临床路径类
    :param day_orders: 这一天的用药情况，输入的是一个 list[], 里面存放的是每一个医嘱的详细信息dict格式, 样例如下
            用量字段是AMOUNT
            {'ITEM_CODE': 'G06-201', 'ORDER_NO': '14787268', 'CLINIC_ITEM_CODE': 'G06-201', 'STOP_ORDER_DOCTOR_NAME': '郭丽婧', 'INPUT_ORDER_DOCTOR_EMID': 'A02305', 'INPATIENT_ID': '181015232', 'PLAN_DAYS': '0', 'ORDER_INPUT_TIME': '07/20/2018 11:11:26', 'VISIT_ID': '2509961', 'ORDER_NAME': '普食', 'ORDER_CLASS': '膳食', 'STOP_ORDER_DOCTOR_ID': '0771', 'ORDER_PLAN_STOP_TIME': '', 'DURATION_UNITS': '', 'COMPOUND_MARK': 'N', 'PERFORM_DEPT': 'G', 'DATE': '07/20/2018', 'PATIENT_ID': '10405624', 'FORM_NO': '', 'ORDER_START_TIME': '07/20/2018 11:12:26', 'BILL_STATUS': 'D', 'INSURANCE_TYPE': '1', 'CONFIRM_ORDER_DOCTOR_EMID': 'A02305', 'STOP_ORDER_DOCTOR_EMID': '', 'ACTUAL_DAYS': '', 'ROUTE': '', 'ORDER_GROUP_NO': '0', 'AMOUNT': '1', 'FREQ_CODE': '', 'DURATION': '', 'ORDER_STATUS': 'E', 'INPUT_ORDER_DOCTOR_ID': '0771', 'ORDER_STOP_TIME': '07/23/2018 12:01:35', 'FORM_TYPE': '3', 'ORDER_DEPT': '12100', 'BILLING_ATTR': '0', 'OUTOFHOSPITAL_FLAG': '1', 'ORDER_SIG_STATUS': '', 'CONFIRM_ORDER_DOCTOR_NAME': '郭丽婧', 'VISIT_TYPE': 'I', 'INPUT_ORDER_DOCTOR_NAME': '郭丽婧', 'REPEAT_INDICATOR': '1', 'CONFIRM_ORDER_DOCTOR_ID': '0771', 'ORDER_CONFIRM_TIME': '07/20/2018 11:12:26', 'AMOUNT_UNIT': '项', 'INSTRUCTION': '', 'EXECUTION_CLASS': '', 'SERIAL_NO_LATEST_TIME': '0001/1/1'}
    :return: 
        返回一个class, 包含的参数有stage_num, newadd_variation, noselect_variation, dosage_variation, planday_variation, freq_variation
        后面5个参数都是dict: 变异医嘱的code --> 该医嘱变异的次数
    """

    start = stage_list[0]
    end = stage_list[1]
    stage_list = []
    for day in range(start, end + 1):
        stage_list.append(str(day))

    # 表示为一个结构体
    # 该结构体有4个变量，分别是stage_num, newadd_variation, noselect_variation, dosage_variation, planday_variation, freq_variation
    class Stage_variation():
        def __init__(self):
            self.stage_num = None
            self.variation_num = 0
            self.newadd_variation = defaultdict(int)
            self.noselect_variation = defaultdict(int)
            self.dosage_variation = defaultdict(int)
            self.planday_variation = defaultdict(int)
            self.freq_variation = defaultdict(int)

    stage_variation = Stage_variation()
    stage_variation.stage_num = min(stage_list)
    # stage_variation.newadd_variation = set()
    # stage_variation.noselect_variation = set()
    # stage_variation.dosage_variation = set()

    # 获取stage_list中所有阶段中临床路径定义的医嘱, 并且单独抽取出必选项医嘱
    cp_orders = dict()
    required_orders = set()     # 必选医嘱，则将其code加入required_orders【此处考虑的是这一天对应阶段的所有必选医嘱】
    for stage_no in stage_list:
        stage_orders = cp.stage[stage_no].stage_orders_detail   #字典, 该阶段包含的医嘱code ---> 医嘱的详细信息(Basic_Order_Info类)
        required_orders = required_orders | cp.stage[stage_no].stage_required_codes_set

        # 此处未考虑对于不同阶段的同一种医嘱，使用剂量，频率，天数不同的情况
        for key, value in stage_orders.items():
            if key in cp_orders:
                pass    # 若考虑剂量，可以将剂量小的覆盖
            else:
                cp_orders[key] = value

    # 统计变异【新增变异、剂量变异、天数变异、频率变异】
    day_order_code_set = set()  # 该天使用医嘱的code集合，用于判断必选项未选
    for order in day_orders:
        order_code = order["CLINIC_ITEM_CODE"]
        day_order_code_set.add(order_code)

        # 是否存在【剂量变异、天数变异、频率变异】的标识，一种实际医嘱可能存在多种变异类型，在统计中只计算一次
        variation_flag = False

        # 该code不在规定医嘱集里面，则属于新增变异
        if order_code not in cp_orders:
            stage_variation.newadd_variation[order_code] += 1
            stage_variation.variation_num += 1

        # 在规定医嘱集里面则判断是否属于【剂量变异、天数变异、频率变异】
        else:
            cp_order_detail = cp_orders[order_code]

            # 比较剂量, 注意需要考虑有些临床路径定义的医嘱内AMOUNT字段为空
            try:
                if int(cp_order_detail.order_amount) < int(order["AMOUNT"].replace(",", "")):
                    stage_variation.dosage_variation[order_code] += 1
                    variation_flag = True
            except:
                pass

            # 比较天数变异, 若实际医嘱的计划天数大于规定医嘱的计划天数，则判断为变异
            try:
                if int(cp_order_detail.order_plan_days) < int(order["PLAN_DAYS"].replace(",", "")):
                    stage_variation.planday_variation[order_code] += 1
                    variation_flag = True
            except:
                pass

            # 比较频率变异，若频率不同则判断为变异
            try:
                if str(cp_order_detail.order_freq) != str(order["FREQ_CODE"]) and str(cp_order_detail) != "None" and str(cp_order_detail) != "nan" and str(order["FREQ_CODE"]) != "None" and str(order["FREQ_CODE"]) != "nan":

                    print(str(cp_order_detail.order_freq), str(order["FREQ_CODE"]))
                    stage_variation.freq_variation[order_code] += 1
                    variation_flag = True
            except:
                pass

        if variation_flag:
            stage_variation.variation_num += 1

    # 统计必选项未选变异
    for order in required_orders:
        if order not in day_order_code_set:
            stage_variation.noselect_variation[order] += 1
            stage_variation.variation_num += 1

    return stage_variation

def add_orders_and_show(input_cp, old_cp_analyzer, recommend_orders):
    """
        将推荐的医嘱集加入临床路径并比较
    :param input_cp: 原始临床路径类
    :param old_cp_analyzer: 原始临床路径的分析类
    :param recommend_orders: 经过分析得到的推荐医嘱
    :return: 
    """
    comp_cp = copy.deepcopy(input_cp)

    for stage_num, orders in recommend_orders.items():
        for order in orders:
            comp_cp.stage[str(stage_num)].add_orders(order)

    # comp_anly = CP_Analyzer(comp_cp, input_visits)
    # comp_anly.analyze_visits()
    # comp_anly.show_var_info()

    print("\n新临床路径与旧路径变异情况比较：")
    compare_CP(old_cp_analyzer.get_newCP_variation(input_cp), old_cp_analyzer.get_newCP_variation(comp_cp), sorted(old_cp_analyzer.cp.stage.keys(), key=lambda x:x[0]))

def get_order_var_info(order, cp_orders):
    """
    基于临床路径规定医嘱集，计算输入医嘱的变异情况
    :param order: 输入的医嘱
    :param cp_orders: 临床路径规定医嘱集
    :return: 输入医嘱的变异情况 dict
    {
    "newadd_variation": 新增变异,
    "dosage_variation": 剂量变异,
    "planday_variation": 天数变异,
    "freq_variation": 频率变异,
    }

    """
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