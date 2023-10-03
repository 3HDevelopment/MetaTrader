## Copy Version ##
## TP & SL input is not correct. loop section needs to be reviewed ##

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
timeframe = mt5.TIMEFRAME_H4
start_date = pd.Timestamp('2023-05-01')
end_date = pd.Timestamp('2023-10-03')

# Request historical data
raw_data = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
df = pd.DataFrame(raw_data)
df['time'] = pd.to_datetime(df['time'], unit='s')
data = df[['time','open','high','low','close']]
position = {'sequence': [], 'time': [], 'type': [], 'Pending':[], 'TP':[], 'SL':[]}
position_list =[]
open_position_list=[]

# Trading Strategy [Moving Average]
# Calculate the 5 SMA - Slow
df['slow'] = df['close'].rolling(5).mean()
data['slow'] = df['slow'] 
# Calculate the 18 EMA - Fast
df['fast'] = df['close'].ewm(span=18).mean()
data['fast'] = df['fast']
# Calculate the SMA 50 - TREND1
df['trend1'] = df['close'].rolling(50).mean() 
data['trend1'] = df['trend1']
# Calculate the SMA 89 - TREND2
df['trend2'] = df['close'].rolling(89).mean()
data['trend2'] = df['trend2']  
# Calculate the EMA 144 - TREND3
df['trend3']  = df['close'].ewm(span=144).mean()
data['trend3'] = df['trend3'] 
# Calculate the EMA 35 - No Trend
df['no trend']  = df['close'].ewm(span=35).mean()
data['no trend'] = df['no trend'] 


## Pending Order ##
## {'sequence':[], 'time': [], 'type': [], 'Pending':[], 'TP':[], 'SL':[],} ##
for i in range(144, len(data)):
    if (data['slow'][i] < data['fast'][i] and all(data['slow'][i] < x > data['fast'][i] \
        for x in [data['trend1'][i], data['trend2'][i], data['trend3'][i], data['no trend'][i]])) \
        or (data['slow'][i] > data['fast'][i] and all(data['fast'][i] < x > data['slow'][i] \
        for x in [data['trend1'][i], data['trend2'][i], data['trend3'][i], data['no trend'][i]])):
        pass
    else:
        if data['close'][i] > data['open'][i]:
            if data['close'][i] < ((data['high'][i]-data['low'][i])*0.55+data['low'][i]):
                position_list.append([df.index[i], data['time'][i], 'buy', data['high'][i], ((data['high'][i]-data['fast'][i])*1.5)+data['high'][i], \
                data['fast'][i]])
            else: 
                pass
        elif data['close'][i] < data['open'][i]:
            if data['close'][i] > ((data['high'][i]-data['low'][i])*0.45+data['low'][i]):
                position_list.append([df.index[i], data['time'][i], 'sell', data['low'][i], data['low'][i]-(data['fast'][i]-data['low'][i]*1.5), \
                data['fast'][i]])
            else:
                pass
    position = pd.DataFrame(position_list, columns=['sequence', 'time', 'type', 'Pending', 'TP', 'SL'])

## Process Order - Open Position ##
i = 1
while i >= 0:
    order_sequence = position['sequence'][i]
    j = order_sequence  # Initialize the inner index
    while j < len(data):
        if position['Pending'][i] > data['low'][j] and position['Pending'][i] < data['high'][j]:
            open_position_list.append([position['sequence'][i], position['time'][i], position['type'][i], position['Pending'][i], position['TP'][i], position['SL'][i],0,0])
            position.drop(position.index[i], inplace=True)  # Remove the row by index from 'position'
            break  # Exit the inner loop after a match is found
        else:
            j += 1  # Increment the inner index
    i += 1  
open_position = pd.DataFrame(open_position_list, columns=['sequence','time', 'type', 'Open', 'TP', 'SL', 'Close', 'PIP'])

## Back Testing ##
i = 1
while i >= 0:
    order_sequence = open_position['sequence'][i]
    j = order_sequence  # Initialize the inner index
    while j < len(data):
        if (open_position['TP'][i] > data['low'][j] and open_position['TP'][i] < data['high'][j]) \
            or (open_position['SL'][i] > data['low'][j] and open_position['SL'][i] < data['high'][j]):
            open_position['Close'][i] = open_position['Open'][i]
            break
        else: j += 1
    i+=1
print(position)
print(open_position)

# Plot 'Open' and 'Close' prices from the 'position' DataFrame


# Show the plot
plt.show()