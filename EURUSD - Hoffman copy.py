## Final Version ##
## Trading Algorithm needs to be reviewed ##

from datetime import datetime
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

 # Showing Time Zone
tt = timezone("Africa/Kampala")
now = datetime.now(tt).hour
symbol = "EURUSD"
timeframe = mt5.TIMEFRAME_H1
start_date = pd.Timestamp('2022-12-10')
end_date = pd.Timestamp('2023-10-04')

# Request historical data
raw_data = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
df = pd.DataFrame(raw_data)
df['time'] = pd.to_datetime(df['time'], unit='s')
data = df[['time','open','high','low','close']]
position = {'sequence': [], 'time': [], 'type': [], 'order':[], 'TP':[], 'SL':[], 'close':[], 'PIP':[]}
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
    or (data['slow'][i] > data['fast'][i] and any(data['fast'][i] > x > data['slow'][i] \
    for x in [data['trend1'][i], data['trend2'][i], data['trend3'][i], data['no trend'][i]]) == True):
        pass
    else:
        if data['close'][i] > data['open'][i] and data['slow'][i] > data['fast'][i]:
            if data['close'][i] < ((data['high'][i]-data['low'][i])*0.55+data['low'][i]):
                position_list.append([df.index[i], data['time'][i], 'buy', 'pending', data['high'][i], \
                                      min(((data['high'][i]-data['fast'][i])*1.75)+data['high'][i], data['high'][i]*1.025), max(data['fast'][i], data['high'][i]*0.9995),0,0])
            else: 
                pass
        elif data['close'][i] < data['open'][i] and data['slow'][i] < data['fast'][i]:
            if data['close'][i] > ((data['high'][i]-data['low'][i])*0.45+data['low'][i]):
                position_list.append([df.index[i], data['time'][i], 'sell', 'pending', data['low'][i], \
                                      max(data['low'][i]-((data['fast'][i]-data['low'][i])*1.75), data['low'][i]*0.975), min(data['fast'][i], data['low'][i]*1.0005),0,0])
            else:
                pass
    position = pd.DataFrame(position_list, columns=['sequence', 'time', 'type', 'order', 'price', 'TP', 'SL', 'close', 'PIP'])

## Process Order - Open Position ##
for i in range(0, len(position)):
        sq = position['sequence'][i]
        if position['order'][i] == 'closed':
            continue
        if position['order'][i] == 'pending':
            for j in range(sq, len(data)-1):
                if position['price'][i] > data['low'][j+1] and position['price'][i] < data['high'][j+1]:
                    position.loc[i, 'order'] = 'open'
                else:
                    pass
        if position['order'][i] == 'open':
            for j in range(sq, len(data)-1):
                if position['SL'][i] > data['low'][j+1] and position['SL'][i] < data['high'][j+1]:
                    position.loc[i, 'order'] = 'closed'
                    position.loc[i, 'close'] = position['SL'][i]
                elif position['TP'][i] > data['low'][j+1] and position['TP'][i] < data['high'][j+1]:
                    position.loc[i, 'order'] = 'closed'
                    position.loc[i, 'close']= position['TP'][i]

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
print(position)
print('maximum =', Maximum_profit, 'minimum =', Maximum_loss, 'Total S/L =', Total_SL)

# Plot 'Open' and 'Close' prices from the 'position' DataFrame

# Plot the price chart
plt.figure(figsize=(20, 12))
plt.plot(df['time'], df['close'], label='Price', color='black')
plt.plot(df['time'], df['slow'], label='slow', color='red')
plt.plot(df['time'], df['fast'], label='fast', color='red')
plt.plot(df['time'], df['trend1'], label='trend3', color='grey')
plt.plot(df['time'], df['trend2'], label='trend3', color='grey')
plt.plot(df['time'], df['trend3'], label='trend3', color='grey')
plt.plot(df['time'], df['no trend'], label='no trend', color='grey')

plt.xlabel('Time')
plt.ylabel('Price')
plt.title('EURUSD Price Chart with Strategy Signals')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)

# Show the plot
plt.show()

# Excel 
excel_filename = "XAUUSD_4H_with_Hoffman x1.5.xlsx"
position.to_excel(excel_filename)