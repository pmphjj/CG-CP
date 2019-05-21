# coding: utf-8

from build_CP import Clinical_Pathway, Stages, CP_Variation
from Build_visits import Build_Visist_Order
import operate
from processing_cp import CP_Analyzer
import copy


def process(cp_id, version_sqno, cp_info_path, cp_stage_path, cp_detail_order_path, cp_detail_info_path, orders_path):
    '''
        临床路径分析类，根据病人的历史数据，给出临床路径的修改建议
    :param cp_id: 要分析的临床路径的id
    :param version_sqno: 要分析临床路径的版本
    :param cp_info_path: 临床路径的基本信息文件路径; 该文件是一个csv格式，以\t作为分割符，来源于临床路径的CP_INFO表,包含的字段有：
        CP_ID,VERSION_SQNO,RELEASE_STATUS,CP_NAME,ADMIT_HINT,ADMIT_RULE,REFERENCE_COST,REFERENCE_DAYS,DEPT_ID,DEPT_NAME,RELEASE_TIME,RELEASER_ID,RELEASER_NAME,CREATE_TIME,CREATOR_ID,CREATOR_NAME
    
    :param cp_stage_path: 临床路径的阶段信息文件路径;该文件是一个csv格式，以\t作为分割符，来源于临床路径的CP_STAGE表，包含的字段有：
        CP_ID,VERSION_SQNO,STAGE_SQNO,START_DAY,END_DAY,STAGE_DESC,STAGE_NAME
    
    :param cp_detail_order_path: 临床路径各阶段的医嘱详细信息文件路径；该文件是一个csv格式，以\t作为分割符，来源于临床路径的CP_DETAIL_ORDER表，包含的字段有：
        CP_ID,VERSION_SQNO,STAGE_SQNO,ORDER_SQNO,ORDER_CLASS,CLINIC_ITEM_CODE,PERFORM_DEPT,ORDER_NAME,REPEAT_INDICATOR,ORDER_GROUP_NO,PACKAGE,AMOUNT,AMOUNT_UNIT,ROUTE,FREQ_CODE,DRUG_TAKE_WITH_MEALS,PLAN_DAYS,SPECIMEN
        
    :param cp_detail_info_path: 临床路径的其他信息文件路径；该文件是一个csv格式，以\t作为分割符，来源于临床路径的CP_DETAIL_INFO表，包含的字段有：
        CP_ID,VERSION_SQNO,STAGE_SQNO,ITEM_CLASS,ITEM_SQNO,INSTRUCTION,REQUIRED,CHECKED
    
    :param orders_path: 进入临床路径的所有患者历史医嘱信息文件路径；该文件是一个csv格式，以\t作为分割符，来源于医嘱的历史数据表，包含的字段有：
        ORDER_NO,ITEM_CODE,CLINIC_ITEM_CODE,COMPOUND_MARK,PATIENT_ID,INPATIENT_ID,VISIT_ID,VISIT_TYPE,INSURANCE_TYPE,FORM_NO,FORM_TYPE,ORDER_GROUP_NO,REPEAT_INDICATOR,ORDER_CLASS,EXECUTION_CLASS,ORDER_NAME,INSTRUCTION,AMOUNT,FREQ_CODE,AMOUNT_UNIT,ROUTE,DURATION,DURATION_UNITS,INPUT_ORDER_DOCTOR_ID,INPUT_ORDER_DOCTOR_NAME,ORDER_INPUT_TIME,CONFIRM_ORDER_DOCTOR_ID,CONFIRM_ORDER_DOCTOR_NAME,ORDER_CONFIRM_TIME,ORDER_START_TIME,PLAN_DAYS,STOP_ORDER_DOCTOR_ID,STOP_ORDER_DOCTOR_NAME,ORDER_STOP_TIME,BILLING_ATTR,SERIAL_NO_LATEST_TIME,ORDER_STATUS,PERFORM_DEPT,ACTUAL_DAYS,ORDER_DEPT,OUTOFHOSPITAL_FLAG,BILL_STATUS,INPUT_ORDER_DOCTOR_EMID,CONFIRM_ORDER_DOCTOR_EMID,STOP_ORDER_DOCTOR_EMID,ORDER_PLAN_STOP_TIME,ORDER_SIG_STATUS
    :return: 
    '''

    # 根据文件路径，读取csv文件中的历史数据，创建临床路径类以及所有患者的Visit类
    input_cp = Clinical_Pathway(cp_id, version_sqno, cp_info_path, cp_stage_path, cp_detail_order_path, cp_detail_info_path)
    input_visits = Build_Visist_Order(cp_id, version_sqno, orders_path)

    # 创建临床路径分析的类，传入CP类和Visit类
    anlyzer = CP_Analyzer(input_cp, input_visits)
    anlyzer.show_var_info() # 展示历史数据临床路径的变异情况

    new_variation = anlyzer.get_newCP_variation(input_cp)   # 根据传入的临床路径input_cp，按照初始化analyzer的映射关系，获取新路径的变异情况
    anlyzer.show_var_info(new_variation)    # 展示新路径的变异情况

    print("\n+++++++++++++++++++++ Frequent Update CP +++++++++++++++++++++++++++++")
    # 获取推荐的医嘱集
    threshold = 0.05  # 变异项出现的频率，只处理频率超过该值的变异项，太小则会特别慢
    most_count = 3  # 对每一阶段，最多推荐新增医嘱数目

    # 两种方式
    recommend_order = anlyzer.generate_recommendation("fpgrowth", threshold=threshold, most_count=most_count)   # 根据频繁模式挖掘获取推荐修改
    # recommend_order = anlyzer.generate_recommendation()   # 基于统计

    print("\n推荐更新:")
    anlyzer.show_recommend(recommend_order)

    # 将推荐的医嘱集加入临床路径并比较异常变化情况
    operate.add_orders_and_show(input_cp, anlyzer, recommend_order)
    print("\n+++++++++++++++++++++ Frequent Update CP +++++++++++++++++++++++++++++")



    # 一项一项的添加医嘱并查看变异变化
    print("\n+++++++++++++++++++++ New Clinical Pathway +++++++++++++++++++++++++++++")
    comp_cp = copy.deepcopy(input_cp)
    comp_cp.stage["1"].add_orders("G11-555")    # 往第一阶段添加医嘱G11-555
    comp_cp.stage["1"].add_orders("G06-220")

    operate.compare_CP(anlyzer.get_newCP_variation(input_cp), anlyzer.get_newCP_variation(comp_cp),
               sorted(anlyzer.cp.stage.keys(), key=lambda x: x[0]))


if __name__ == "__main__":

    process("4,621", "3", "data/cp_info.csv", "data/cp_stage.csv", "data/cp_detail_order.csv", "data/cp_detail_info.csv", "data/orders.csv")

