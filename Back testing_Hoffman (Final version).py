## Final Version ##
## Trading Algorithm needs to be reviewed ##

from datetime import datetime, timedelta
from pytz import timezone
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# Set up
if mt5.initialize():
    account_info=mt5.account_info()
    if account_info!=None:
        # display trading account data 'as is'
        print("successfully loged in", account_info)
else:
    print("failed to connect to the trade account, error code =",mt5.last_error())

tt = timezone("Africa/Kampala")
now = datetime.now(tt).hour
symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_H4
testing_timeframe = mt5.TIMEFRAME_M15
start_date = pd.Timestamp('2023-01-23 04:00:00') ## First, confirm the start time of 4H and 1H before run testing ##
end_date = pd.Timestamp('2023-10-08 04:00:00')

# Request historical data
raw_data = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
testing_raw_data = mt5.copy_rates_range(symbol, testing_timeframe, start_date, end_date)
df = pd.DataFrame(raw_data)
testing_df = pd.DataFrame(testing_raw_data)
df['time'] = pd.to_datetime(df['time'], unit='s')
testing_df['time'] = pd.to_datetime(testing_df['time'], unit='s')
data = df[['time','open','high','low','close']]
testing_data = testing_df[['time','open','high','low','close']]
position = {'sequence': [], 'time': [], 'type': [], 'order':[], 'TP':[], 'SL':[], 'close':[], 'PIP':[], 'OT': [], 'OT S':[], 'CT': [], 'AC_PIP':[]}
position_list =[]
open_position_list=[]

# Trading Strategy [Hoffman] 
# Calculate the 5 SMA - Slow
data = data.copy()
df['slow'] = df['close'].rolling(5).mean()
data.loc[:, 'slow'] = df['slow'] 
# Calculate the 18 EMA - Fast
df['fast'] = df['close'].ewm(span=18).mean()
data.loc[:,'fast'] = df['fast']
# Calculate the SMA 50 - TREND1
df['trend1'] = df['close'].rolling(50).mean() 
data.loc[:,'trend1'] = df['trend1']
# Calculate the SMA 89 - TREND2
df['trend2'] = df['close'].rolling(89).mean()
data.loc[:,'trend2'] = df['trend2']  
# Calculate the EMA 144 - TREND3
df['trend3']  = df['close'].ewm(span=144).mean()
data.loc[:,'trend3'] = df['trend3'] 
# Calculate the EMA 35 - No Trend
df['no trend']  = df['close'].ewm(span=35).mean()
data.loc[:,'no trend'] = df['no trend'] 

## Pending Order ##
for i in range(144, len(data)):
    if (data['slow'][i] < data['fast'][i] and any(data['slow'][i] < x < data['fast'][i] \
    for x in [data['trend1'][i], data['trend2'][i], data['trend3'][i], data['no trend'][i]]) == True) \
    or (data['slow'][i] > data['fast'][i] and any(data['slow'][i] > x > data['fast'][i] \
    for x in [data['trend1'][i], data['trend2'][i], data['trend3'][i], data['no trend'][i]]) == True):
        pass
    else:
        if data['slow'][i] > data['fast'][i]: ## and max(data['close'][i], data['open'][i]) < ((data['high'][i]-data['low'][i])*0.45+data['low'][i]): ##
            if data['close'][i] < ((data['high'][i]-data['low'][i])*0.55+data['low'][i]):
                position_list.append([df.index[i], data['time'][i], 'buy', 'pending', data['high'][i], \
                                      min(max(((data['high'][i]-data['fast'][i])*2),((data['fast'][i]-data['high'][i])*2))+data['high'][i], data['high'][i]*1.05), max(data['fast'][i], data['high'][i]*0.99975),0,0,0,0,0,0])
            else: 
                pass
        elif data['slow'][i] < data['fast'][i]: ## and min(data['close'][i], data['open'][i]) > ((data['high'][i]-data['low'][i])*0.55+data['low'][i]): ##
            if data['close'][i] > ((data['high'][i]-data['low'][i])*0.45+data['low'][i]):
                position_list.append([df.index[i], data['time'][i], 'sell', 'pending', data['low'][i], \
                                      max(data['low'][i]-max(((data['fast'][i]-data['low'][i])*2),((data['low'][i]-data['fast'][i])*2)), data['low'][i]*0.95), min(data['fast'][i], data['low'][i]*1.00025),0,0,0,0,0,0])
            else:
                pass
    position = pd.DataFrame(position_list, columns=['sequence', 'time', 'type', 'order', 'price', 'TP', 'SL', 'close', 'PIP', 'OT', 'OTS', 'CT', 'AC_PIP'])

for i in range(len(position)):
    matching_indices = testing_data.index[testing_data['time'] == position.loc[i, 'time']]

    if len(matching_indices) > 0:
        position.loc[i, 'OTS'] = matching_indices[0] + 16 ## + 4 for H1 ##
    else:
    # Find the earliest time on the same date in testing_data
        same_date = position.loc[i, 'time'].replace(hour=0, minute=0, second=0, microsecond=0)
        matching_indices = testing_data.index[testing_data['time'].apply(lambda x: x.date() == same_date.date())]
    
        if len(matching_indices) > 0:
            position.loc[i, 'OTS'] = matching_indices[0] + 12 ## + 4 FOR H1 ##
        else:
            position.loc[i, 'OTS'] = -1 

## Process Order - Open Position ##
for i in range(0, len(position)):
    sq = position['OTS'][i]
    if position['order'][i] == 'pending':
        for j in range(sq, len(testing_data)-1): 
            if position['type'][i] == 'buy':
                if position['price'][i] < testing_data['high'][j]: ## j +1 deleted ##
                    position.loc[i, 'order'] = 'open'
                    position.loc[i, 'OT'] = testing_data['time'][j]
                    position.loc[i, 'OTS'] = j
                    break
            elif position['type'][i] == 'sell':
                if position['price'][i] > testing_data['low'][j]: ## j +1 deleted ##
                    position.loc[i, 'order'] = 'open'
                    position.loc[i, 'OT'] = testing_data['time'][j]
                    position.loc[i, 'OTS'] = j
                    break

for i in range(0, len(position)):
    ots = position['OTS'][i]
    if position['order'][i] == 'open':
        for j in range(ots, len(testing_data)-1):
            if position['type'][i] == 'buy':
                if position['SL'][i] > testing_data['low'][j+1]: ## j +1 deleted ##
                    position.loc[i, 'order'] = 'closed'
                    position.loc[i, 'close'] = position['SL'][i]
                    position.loc[i, 'CT'] = testing_data['time'][j+1]
                    break    
                elif position['TP'][i] < testing_data['high'][j+1]: ## j +1 deleted ##
                    position.loc[i, 'order'] = 'closed'
                    position.loc[i, 'close']= position['TP'][i]
                    position.loc[i, 'CT'] = testing_data['time'][j+1]
                    break
            elif position['type'][i] == 'sell':
                if position['SL'][i] < testing_data['high'][j+1]: ## j +1 deleted ##
                    position.loc[i, 'order'] = 'closed'
                    position.loc[i, 'close'] = position['SL'][i]
                    position.loc[i, 'CT'] = testing_data['time'][j+1]
                    break
                elif position['TP'][i] > testing_data['low'][j+1]: ## j +1 deleted ##
                    position.loc[i, 'order'] = 'closed'
                    position.loc[i, 'close']= position['TP'][i]
                    position.loc[i, 'CT'] = testing_data['time'][j+1]
                    break

for i in range(0,len(position)):
    if position['order'][i] == 'closed':
        if position['type'][i] == 'sell':
            position['PIP'][i] = (position['close'][i] - position['price'][i]) * -1 
        elif position['type'][i] == 'buy':
            position['PIP'][i] = position['close'][i] - position['price'][i]

## Result ##
Maximum_profit = position['PIP'].max()
Maximum_loss = position['PIP'].min()
Total_SL = position['PIP'].sum()
print('maximum =', Maximum_profit, 'minimum =', Maximum_loss, 'Total S/L =', Total_SL)

## Accumulate P/L ##
ac_pip = 0
for i in range(0, len(position)):
    position.loc[i, 'AC_PIP'] = position['PIP'][i] + ac_pip
    ac_pip = position['AC_PIP'][i]

# Plot the price chart
"""
plt.figure(figsize=(20, 12))
plt.plot(df['time'], df['close'], label='Price', color='black')
plt.plot(df['time'], df['slow'], label='slow', color='red')
plt.plot(df['time'], df['fast'], label='fast', color='red')
plt.plot(df['time'], df['trend1'], label='trend3', color='grey')
plt.plot(df['time'], df['trend2'], label='trend3', color='grey')
plt.plot(df['time'], df['trend3'], label='trend3', color='grey')
plt.plot(df['time'], df['no trend'], label='no trend', color='grey')
"""

plt.figure(figsize=(20, 12))
plt.plot(position['time'],position['AC_PIP'], label='PL', color='black')

plt.xlabel('Time')
plt.ylabel('Price')
plt.title('EURUSD Price Chart with Strategy Signals')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)

# Show the plot
plt.show()

# Excel 
excel_filename = "test_4H.xlsx"
data.to_excel(excel_filename)
excel_filename = "test_1H.xlsx"
testing_data.to_excel(excel_filename)
excel_filename = "test_result.xlsx"
position.to_excel(excel_filename)
