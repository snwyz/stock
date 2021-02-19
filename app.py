import requests
import datetime as dt
import time
import pandas as pd
import numpy as np
import akshare as ak

from flask import Flask
from pandas.io import json

app = Flask(__name__)

# 大盘实时数据


@app.route('/get_stock_df')
def get_stock_df():
    stock_df = ak.stock_zh_index_spot()
    stock_df_filter = stock_df[(stock_df['代码'] == 'sh000001') | (stock_df['代码'] == 'sz399001') | (stock_df['代码'] == 'sz399006')]
    result = []
    for index, row in stock_df_filter.iterrows():
        result.append({
            'symbol': row["代码"],
            'name': row["名称"],
            'current_price': round(row["最新价"], 2),
            'price_change': round(row["涨跌额"], 2),
            'percent_change': round(row["涨跌幅"], 2),
            'turnover': round((row["成交额"]/100000000), 2)
        })
    # return result
    resu = {'code': 200, 'data': result, 'message': '成功'}
    return json.dumps(resu, ensure_ascii=False)
# 北向资金


@app.route('/get_money_current')
def get_money_current():
    realtime_flow_url = 'http://push2.eastmoney.com/api/qt/kamt.rtmin/get?fields1=f1,f3&fields2=f51,f52,f54,f56'
    ret = requests.get(realtime_flow_url)

    if not ret.ok:
        raise Exception('请求实时资金流向失败！')

    data = ret.json()['data']
    _date = dt.datetime(dt.datetime.today().year, *map(int, data['s2nDate'].split('-')))

    df = pd.DataFrame(map(lambda v: v.split(','), data['s2n']), columns=['time', 'hk2sh', 'hk2sz', 's2n'])
    result = []
    for index, row in df.iterrows():
        if row["s2n"] != '-':
            current = {
                'date': row["time"],
                'totalmoney': round(float(row["s2n"])/10000, 2),
                'sh_money': round(float(row["hk2sh"])/10000, 2),
                'sz_money': round(float(row["hk2sz"])/10000, 2),
            }
        result.append({
            'date': row["time"],
            'totalmoney': row["s2n"] if row["s2n"] == '-' else round(float(row["s2n"]) / 10000, 2),
            'sh_money': row["hk2sh"] if row["hk2sh"] == '-' else round(float(row["hk2sh"]) / 10000, 2),
            'sz_money': row["hk2sz"] if row["hk2sz"] == '-' else round(float(row["hk2sz"]) / 10000, 2),
        })
    resu = {'code': 200, 'data': {'list': result, 'current': current}, 'message': '成功'}
    return resu


# 个股资金实时流入前10
@app.route('/get_money_stock')
def get_money_stock():
    get_money_stock = ak.stock_individual_fund_flow_rank(indicator="今日").head(10)

    get_money_stock_message = '个股实时资金流入排行：' + '\n\n'
    for index, row in get_money_stock.iterrows():
        message = row["名称"] + '（' + str(row["涨跌幅"]) + '%）' + '：' \
                  + '净流入-净额:' + str('%.2f' % (row["主力净流入-净额"]/100000000)) + '亿，' + '\n'
        get_money_stock_message = get_money_stock_message + message
    return get_money_stock_message

# 行业资金实时流入前10


@app.route('/get_stock_sector_fund_flow_rank')
def get_stock_sector_fund_flow_rank():
    stock_sector_fund_flow_rank_df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流").head(20)
    print(stock_sector_fund_flow_rank_df)

    stock_sector_fund_flow_rank_df_message = '行业板块实时资金流入排行：' + '\n\n'

    for index, row in stock_sector_fund_flow_rank_df.iterrows():
        message = row["名称"] + '（' + str(row["今日涨跌幅"]) + '%）' + '：' \
                  + '净流入:' + str('%.2f' % (row["今日主力净流入-净额"]/100000000)) + '亿，' \
                  + '（' + "流入最大股：" + str(row["今日主力净流入最大股"]) + '）' + '\n\n'
        stock_sector_fund_flow_rank_df_message = stock_sector_fund_flow_rank_df_message + message
    return get_stock_sector_fund_flow_rank


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
