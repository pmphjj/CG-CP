# coding: utf-8


import pandas as pd 
import sqlite3
import re

# 连接sqlite3数据库
conn = sqlite3.connect("data/FGGS.db")

# 数据库中数据获取
orders_df = pd.read_sql_query("select * from orders;", conn)
cp_detail_order = pd.read_sql_query("select * from cp_detail_order;", conn)
cp_variation_info = pd.read_sql_query("select * from cp_variation_info;", conn)


# 定制某一版本的临床路径详情
cp_detail_order[cp_detail_order["VERSION_SQNO"] == "3"].sort_values(by=["ORDER_SQNO", "STAGE_SQNO"])
print (orders_df[orders_df["PATIENT_ID"] == "10346701"])



#查看医嘱的时间
orders_time = orders_df[["ORDER_CONFIRM_TIME", "ORDER_START_TIME"]]


p_all_orders = orders_df[orders_df["PATIENT_ID"] == "10423365"][["ITEM_CODE","CLINIC_ITEM_CODE","PATIENT_ID", "INPATIENT_ID","ORDER_CONFIRM_TIME", "ORDER_START_TIME" ]].sort_values(by="ORDER_CONFIRM_TIME")



# 某一个病人的路径变异情况
cp_variation_info[cp_variation_info["PATIENT_ID"] == "10423365"].sort_values("VARIATION_TIME")


# 查看病人所有的药物code，在临床路径设置的code中没有出现的
p_clinic_code_set =  set(orders_df[orders_df["PATIENT_ID"] == "10423365"].CLINIC_ITEM_CODE)
cp_v3_clinic_code_set = set(cp_detail_order[cp_detail_order["VERSION_SQNO"] == "3"].CLINIC_ITEM_CODE)
variation_codes =  list(filter(lambda x: x not in cp_v3_clinic_code_set, p_clinic_code_set))


# 医嘱数据中所有病人的id，以及变异数据中所有病人的id
all_orders_p = set(orders_df.PATIENT_ID)
all_p_variation = set(cp_variation_info.PATIENT_ID)


# In[80]:


# 没有发生变异的病人
list(filter(lambda x: x not in all_p_variation, all_orders_p))



# 关闭数据库连接
conn.close()

