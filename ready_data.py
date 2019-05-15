import pandas as pd
import sqlite3
import re

# 连接sqlite3数据库
conn = sqlite3.connect("../data/FGGS.db")

# 数据库中数据获取
cp_info = pd.read_sql_query("select * from CP_INFO;", conn)
cp_info.to_csv("data/cp_info.csv", sep="\t", index=False, encoding="utf-8")

cp_stage = pd.read_sql_query("select * from cp_stage", conn)
cp_stage.to_csv("data/cp_stage.csv", sep="\t", index=False, encoding="utf-8")

cp_detail_order = pd.read_sql_query("select * from cp_detail_order;", conn)
cp_detail_order.to_csv("data/cp_detail_order.csv", sep="\t", index=False, encoding="utf-8")

cp_detail_info = pd.read_sql_query("select * from cp_detail_info;", conn)
cp_detail_info.to_csv("data/cp_detail_info.csv", sep="\t", index=False, encoding="utf-8")

orders = pd.read_sql_query("select * from orders;", conn)
orders.to_csv("data/orders.csv", sep="\t", index=False, encoding="utf-8")

