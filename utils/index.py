import numpy
import pandas
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from vnpy_ctastrategy.backtesting import load_bar_data
from vnpy.trader.object import OrderData, TradeData, BarData, TickData
from vnpy.trader.constant import (
    Direction,
    Offset,
    Exchange,
    Interval,
    Status,
)
from typing import Callable, List, Dict, Optional, Type
from datetime import datetime, timedelta
import time


# 支持中文
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# print(mpf.available_styles())
mpf_style = mpf.make_mpf_style(
    base_mpf_style='yahoo',
    rc={'font.family': 'SimHei', 'axes.unicode_minus': 'False'},
    marketcolors=mpf.make_marketcolors(up='red', down='green', inherit=True)
)

def get_percent(nowPrice: float, aimPrice: float):
    num = (aimPrice - nowPrice) / nowPrice
    return "{:.1%}".format(num)

def get_ma_price(series: pandas.Series, ma_num: int):
    last_index = series.count() - 1
    if ma_num > last_index:
        last_index = ma_num
    return series[last_index-ma_num: last_index].mean()

def list_include(list, key: str, value):
    for item in list:
        if item[key] == value:
            return True
    return False

def getDataFrame(history_data):
    bar_data_dict_list = []
    for index, bardata in enumerate(history_data):
        bar_dict = {
            "index": index,
            "datetime": bardata.datetime,
            "open_price": bardata.open_price,
            "close_price": bardata.close_price,
            "low_price": bardata.low_price,
            "high_price": bardata.high_price,
            "turnover": bardata.turnover, # 成交额
            "volume": bardata.volume, # 成交额
        }
        bar_data_dict_list.append(bar_dict)
    df = pandas.DataFrame(bar_data_dict_list)
    # df['date'] = df['datetime']
    return df

def getStockDataFrame():
    df1 = pd.read_csv('./assets/tushare_stock_basic.csv', dtype={'symbol': str})
    df2 = pd.read_csv('./assets/tushare_bak_basic.csv', dtype={'symbol': str})
    df1 = df1.drop_duplicates(subset="ts_code")
    df2 = df2.drop_duplicates(subset="ts_code")
    # df['symbol'] = df['ts_code'].apply(lambda str: str.split('.')[0])
    df_stock = pd.merge(df1, df2, on='ts_code', how='inner', suffixes=('','_delete'))
    # 删掉merge时重复的列
    for column in df_stock.columns.tolist():
        if column.find("_delete") != -1:
            df_stock.drop(column, axis=1, inplace=True)

    # 增加指数相关信息
    df_index = pd.read_csv('./assets/tushare_index_basic_20240225180727.csv', dtype={'symbol': str})

    df = pd.concat([df_stock, df_index])

    # 动态计算exchange列
    exchange_map = { 'SH': 'SSE', 'SZ': 'SZSE', 'BJ': 'BSE' }
    new_cols = []
    for index, row in df.iterrows():
        exchange = row['ts_code'].split('.')[1]
        if exchange_map.get(exchange) is not None:
            exchange = exchange_map[exchange]
        new_cols.append(exchange)
    df['exchange'] = new_cols

    # 过滤掉退市股 和 ST
    df = df[df['list_status'] == 'L']
    df = df[~df['name'].str.contains('ST')]

    # 类型: ts_code, trade_date, open, close, pe
    return df

def getStockPlot(df, dotArr, title, axtitle, savePath):

    df['date']=df['datetime']
    df['open']=df['open_price']
    df['high']=df['high_price']
    df['low']=df['low_price']
    df['close']=df['close_price']
    df.set_index('date', inplace=True)

    plots = []
    for dot in dotArr:
        ap = mpf.make_addplot(dot['dotSeries'],  color=dot['color'], scatter=True, markersize=20, marker='o', panel=0)
        plots.append(ap)


    mpf.plot(
        df, type='candle',
        style=mpf_style, ylabel='Price', ylabel_lower='Volume',
        mav=(5, 10 , 30),
        volume=True,
        title=title,
        axtitle=axtitle,
        savefig=savePath,
        addplot=plots,
    )




    # plt.figure(figsize=(24, 12))
    # plt.title(title)
    #
    # fig, (ax1, ax2) = plt.subplots(2,1, sharex="row")
    # ax1.plot(df['datetime'], df['close_price'], label='close_price')
    # ax1.set_xlabel('Date')
    # ax1.set_ylabel('Price')
    #
    # ax2.bar(df['datetime'], df['volume'], label='volume', color='tab:green', alpha=0.3)
    # ax2.set_xticks([])
    # ax2.set_yticks([])

    # plt.legend()
    # plt.tight_layout()
    # plt.scatter(arc_points_df['datetime'], arc_points_df['close_price'], color='red', label='Arc Top')
    # return plt, ax1
    return plt

def makeSingleDotSeries(series:pandas.Series, index):
    res = pandas.Series([numpy.NAN] * len(series))
    res[index] = series[index]
    return res

def plotStock(title, df):
    plt = getStockPlot(title, df)
    plt.show()

# 获取最新的行情数据
def get_latest_bar_data(row):
    nowDate = datetime.now()
    # todo 获取最近30天的数据（貌似不能直接获取最后一条数据），再取最后一天
    start = nowDate - timedelta(30)
    history_data: List[BarData] = load_bar_data(
        symbol=row['symbol'],
        exchange=Exchange[row['exchange']],
        start=start,
        end=nowDate,
        interval=Interval.DAILY,
    )
    if len(history_data) == 0: return None
    return history_data[len(history_data) - 1]


# 计算函数的运行时间
def calculate_function_runtime(func):
    start_time = time.time()  # 记录开始时间
    func()  # 调用函数
    end_time = time.time()  # 记录结束时间

    # 计算运行时间（单位：秒）
    runtime_seconds = end_time - start_time

    # 将秒转换为分钟
    runtime_minutes = runtime_seconds / 60

    print("Function runtime:", runtime_minutes, "minutes")