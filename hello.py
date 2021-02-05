import requests
import datetime as dt
import time
import pandas as pd
import numpy as np
import schedule
import hmac
import hashlib
import base64
import akshare as ak
# from apscheduler.schedulers.blocking import BlockingScheduler
# 大盘实时数据
# 小熊api https://api.doctorxiong.club/v1/stock/board

def getSign():
    timestamp = str(round(time.time() * 1000))
    # app_secret = 'SEC7ba3d34a066710739ea97a088ba30e0ae7cf6e3e82721451d54e3024fe501564'  # 测试群
    app_secret = 'SECcf2a5f2524eea3527be0163eb36de8e1cfb2ecc6248890faa2c311ed32f456bb'    # 正式群

    app_secret_enc = app_secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, app_secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(app_secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    return base64.b64encode(hmac_code).decode('utf-8')



def getBoard():
    get_board_url = 'https://api.doctorxiong.club/v1/stock/board?token=W9hJ3pzvKU'
    get_hot_stock_url = 'https://api.doctorxiong.club/v1/stock/hot?token=W9hJ3pzvKU'

    board = requests.get(get_board_url)
    hot_stock = requests.get(get_hot_stock_url)

    board_list = board.json()['data']
    hot_stock_list = hot_stock.json()['data']

    board_message = '大盘实时数据：' + '\n'
    for board_item in board_list:
        board_item['changePercent'] = board_item['changePercent'] + '%'
        board_item['turnover'] = str('%.2f' % (int(board_item['turnover']) / 10000)) + '亿'
        message = board_item['name'] + '（' + board_item['changePercent'] + '）' + '：' \
                  + board_item['price'] + '，' + "成交金额：" + board_item['turnover'] + '\n'
        board_message = board_message + message

    hot_stock_message = '个股成交量排行：' + '\n'
    for hot_stock_item in hot_stock_list:
        hot_stock_item['changePercent'] = hot_stock_item['changePercent'] + '%'
        hot_stock_item['turnover'] = str('%.2f' % (int(hot_stock_item['turnover']) / 10000)) + '亿'
        message = hot_stock_item['name'] + '（' + hot_stock_item['changePercent'] + '）' + '：' \
                  + hot_stock_item['price'] + '，' + "成交金额：" + hot_stock_item['turnover'] + '\n'
        hot_stock_message = hot_stock_message + message
        content = board_message + '\n' + hot_stock_message
    postToDing(content)

# 北向资金
def get_realtime_money_flow():

    current_time = time.strftime("%-H:%M", time.localtime())

    realtime_flow_url = 'http://push2.eastmoney.com/api/qt/kamt.rtmin/get?fields1=f1,f3&fields2=f51,f52,f54,f56'
    ret = requests.get(realtime_flow_url)

    if not ret.ok:
        raise Exception('请求实时资金流向失败！')

    data = ret.json()['data']

    _date = dt.datetime(dt.datetime.today().year, *map(int, data['s2nDate'].split('-')))

    df = pd.DataFrame(map(lambda v: v.split(','), data['s2n']), columns=['time', 'hk2sh', 'hk2sz', 's2n']).\
        set_index('time').replace('-', np.nan).dropna().astype(float)

    nouth_message = '北向资金实时流入：' + '\n' + '总流入：' + str('%.2f' % (df.loc[current_time, 's2n'] / 10000)) + '亿，' + '流向沪市：' \
                    + str('%.2f' % (df.loc[current_time, 'hk2sh'] / 10000)) + '亿，' + '\n' + '流向深市：' + str('%.2f' % (df.loc[current_time, 'hk2sz'] / 10000)) + '亿'
    postToDing(nouth_message)


# 个股资金实时流入前10
def get_stock_individual_fund_flow_rank():
    stock_individual_fund_flow_rank_df = ak.stock_individual_fund_flow_rank(indicator="今日").head(10)

    stock_individual_fund_flow_rank_message = '个股实时资金流入排行：' + '\n'
    for index, row in stock_individual_fund_flow_rank_df.iterrows():
        message = row["名称"] + '（' + str(row["涨跌幅"]) + '%）' + '：' \
                  + '净流入-净额:' + str('%.2f' % (row["主力净流入-净额"]/100000000)) + '亿，' + "净流入-净占比：" \
                  + str(row["主力净流入-净占比"]) + '%' + "超大单-净占比" + str(row["超大单净流入-净占比"]) + '%' \
                  + "大单-净占比" + str(row["大单净流入-净占比"]) + '%' \
                  + "中单-净占比" + str(row["中单净流入-净占比"]) + "小单-净占比" + str(row["小单净流入-净占比"]) + '\n'
        stock_individual_fund_flow_rank_message = stock_individual_fund_flow_rank_message + message

    postToDing(stock_individual_fund_flow_rank_message)

# 行业资金实时流入前10
def get_stock_sector_fund_flow_rank():
    stock_sector_fund_flow_rank_df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流").head(20)

    print(stock_sector_fund_flow_rank_df)
    stock_sector_fund_flow_rank_df_message = '行业板块实时资金流入排行：' + '\n'
    for index, row in stock_sector_fund_flow_rank_df.iterrows():
        message = row["名称"] + '（' + str(row["今日涨跌幅"]) + '%）' + '：' \
                  + '净流入:' + str('%.2f' % (row["今日主力净流入-净额"]/100000000)) + '亿，' + "净流入-占比：" \
                  + str(row["今日主力净流入-净占比"]) + '%' + "超大单-净占比" + str(row["今日超大单净流入-净占比"]) + '%' + "大单-净占比" + str(row["今日大单净流入-净占比"]) + '%' \
                  + "中单-净占比" + str(row["今日中单净流入-净占比"]) + "小单-净占比" + str(row["今日小单净流入-净占比"]) \
                  + '\n' + '（' + "流入最大股：" + str(row["今日主力净流入最大股"]) + '）' + '\n\n'
        stock_sector_fund_flow_rank_df_message = stock_sector_fund_flow_rank_df_message + message

    postToDing(stock_sector_fund_flow_rank_df_message)

# 发送到钉钉
def postToDing(content):

    sign = getSign()

    json_data = {
        "msgtype": "text",
        "text": {
            "content": content,  # 发送内容
        },
        "at": {
            "atMobiles": [
            ],
            "isAtAll": False  # 是否要@某位用户
        }
    }
    # ding_url = 'https://oapi.dingtalk.com/robot/send?access_token=a6b488dc3f9881d3344f902a38fc78eeb74467b10dabbd0a16273eb3cb13fa97' + \
    #             '&timestamp=' + str(round(time.time() * 1000))+'&sign=' + sign  # 测试群

    ding_url = 'https://oapi.dingtalk.com/robot/send?access_token=399aab2aeca9a235a1667a76eb2d202957685b3a47eaa6c3c0e089ba44860492' + \
               '&timestamp=' + str(round(time.time() * 1000)) + '&sign=' + sign   # 正式群
    requests.post(url=ding_url, json=json_data)
    print('信息发送成功。')

schedule.every(5).minutes.do(get_realtime_money_flow)    # 每隔1分钟执行一次任务
schedule.every(30).minutes.do(getBoard)    # 每隔5分钟执行一次任务
schedule.every(8).minutes.do(get_stock_individual_fund_flow_rank)    # 每隔3分钟执行一次任务
schedule.every(15).minutes.do(get_stock_sector_fund_flow_rank)    # 每隔1分钟执行一次任务

while True: 
    schedule.run_pending()  # run_pending运行所有可以运行的任务
