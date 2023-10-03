##UPDATED Aug 29##

from datetime import datetime
from pytz import timezone
import MetaTrader5 as mt5
import pandas as pd
import time


 # Showing Time Zone
tt = timezone("Africa/Kampala")
now = datetime.now(tt).hour
current = now

# Set up
mt5.initialize()
instru = "EURUSD"

# establish connection to the MetaTrader 5 terminal
if not mt5.initialize():
    print("initialize() failed, error code =",mt5.last_error())
    quit()
 
# connect to the trade account specifying a password and a server
if mt5.initialize:
    account_info=mt5.account_info()
    if account_info!=None:
        # display trading account data 'as is'
        print("successfully loged in", account_info)
else:
    print("failed to connect to the trade account, error code =",mt5.last_error())

# Macro Start
while 1 != 24:
    # check the presence of open positions
    def position_total():
        positions_total=mt5.positions_total()
        if positions_total>0:
            print("Total positions=", positions_total)
        else:
            print("Positions not found")

    # get 10 GBPUSD D1 bars from the current day
    rates = mt5.copy_rates_from_pos(instru, mt5.TIMEFRAME_H4, 0, 146)

    # Convert price data to DataFrame
    data_frame = pd.DataFrame(rates)
    data_frame['time'] = pd.to_datetime(data_frame['time'], unit='s')
    data_frame.set_index('time', inplace=True)

    # Calculate the 5 SMA - Slow
    slowf = data_frame['close'].rolling(5).mean()
    slow = slowf.iloc[-1]  
    # Calculate the 18 EMA - Fast
    fastf = data_frame['close'].ewm(span=18).mean()
    fast = fastf.iloc[-1]
    # Calculate the SMA 50 - TREND1
    trend1f = data_frame['close'].rolling(50).mean() 
    trend1 = trend1f.iloc[-1]
    # Calculate the SMA 89 - TREND2
    trend2f = data_frame['close'].rolling(89).mean()
    trend2 = trend2f.iloc[-1]  
    # Calculate the EMA 144 - TREND3
    trend3f = data_frame['close'].ewm(span=144).mean()
    trend3 = trend3f.iloc[-1]  
    # Calculate the EMA 35 - No Trend
    notrendf = data_frame['close'].ewm(span=35).mean()
    notrend = notrendf.iloc[-1]  

    # define high, low and close
    open = data_frame['open'].iloc[-2]
    high = data_frame['high'].iloc[-2]
    close = data_frame['close'].iloc[-2]
    low = data_frame['low'].iloc[-2]
    

    # logic 1
    if (slow < fast and any(slow < x < fast for x in [trend1, trend2, trend3, notrend])) or \
        (slow > fast and any(fast > x > slow for x in [trend1, trend2, trend3, notrend])):
        print("wait 1")
        print(position_total)
        time.sleep(10)
    else:
        while current == now:
            if close > open and slow > fast:
                if close < ((high-low)*0.55+low):
                    # prepare the buy request structure
                    symbol = instru
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info is None:
                        print(symbol, "not found, can not call order_check()")
                                
                # if the symbol is unavailable in MarketWatch, add it
                    if not symbol_info.visible:
                        print(symbol, "is not visible, trying to switch on")
                        if not mt5.symbol_select(symbol,True):
                            print("symbol_select({}}) failed, exit",symbol)
                        
                    lot = 0.01
                    point = mt5.symbol_info(symbol).point
                    price = mt5.symbol_info_tick(symbol).ask
                    deviation = 20
                    request = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": lot,
                    "type": mt5.ORDER_TYPE_BUY_STOP,
                    "price": high,
                    "sl": max(fast, high*0.9995),
                    "tp": min(((high-fast)*1.75)+high, high*1.025),
                    "deviation": deviation,
                    "magic": 234000,
                    "comment": "python script open",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                    }
                
                    # send a trading request
                    result = mt5.order_send(request)
                    # check the execution result
                    print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol,lot,price,deviation));
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        print("2. order_send failed, retcode={}".format(result.retcode))
                    # request the result as a dictionary and display it element by element
                    result_dict=result._asdict()
                    for field in result_dict.keys():
                        print("   {}={}".format(field,result_dict[field]))
                        # if this is a trading request structure, display it element by element as well
                        if field=="request":
                            traderequest_dict=result_dict[field]._asdict()
                            for tradereq_filed in traderequest_dict:
                                print("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))
                    #halt trading
                    current += 1
                    print(current, now)
        
                else:
                    print("buy signal has not been met..")
                    print(position_total)
                    current = now
                    time.sleep(10)

            elif close < open and slow < fast:
                if close > ((high-low)*0.45+low):
                    symbol = instru
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info is None:
                        print(symbol, "not found, can not call order_check()")
                                
                # if the symbol is unavailable in MarketWatch, add it
                    if not symbol_info.visible:
                        print(symbol, "is not visible, trying to switch on")
                        if not mt5.symbol_select(symbol,True):
                            print("symbol_select({}}) failed, exit",symbol)
                        
                    lot = 0.01
                    point = mt5.symbol_info(symbol).point
                    price = mt5.symbol_info_tick(symbol).ask
                    deviation = 20
                    print("sell signal")
                    request = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": lot,
                    "type": mt5.ORDER_TYPE_SELL_STOP,
                    "price": low,
                    "sl": min(fast, low*1.0005),
                    "tp": max(low-(fast-low*1.75), low*0.975),
                    "deviation": deviation,
                    "magic": 234000,
                    "comment": "python script open",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                    }
                
                    # send a trading request
                    result = mt5.order_send(request)
                    # check the execution result
                    print("1. order_send(): by {} {} lots at {} with deviation={} points".format(symbol,lot,price,deviation));
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        print("2. order_send failed, retcode={}".format(result.retcode))
                    # request the result as a dictionary and display it element by element
                    result_dict=result._asdict()
                    for field in result_dict.keys():
                        print("   {}={}".format(field,result_dict[field]))
                        # if this is a trading request structure, display it element by element as well
                        if field=="request":
                            traderequest_dict=result_dict[field]._asdict()
                            for tradereq_filed in traderequest_dict:
                                print("       traderequest: {}={}".format(tradereq_filed,traderequest_dict[tradereq_filed]))
                    #trading halt
                    current += 1
                else:
                    print("sell signal has not been met..")
                    print(position_total)
                    current = now
                    time.sleep(10)
            else: 
                print("first condition has not been met..")
                print(position_total)
                time.sleep(10)
        else:
            print("Order sent. trading paused..")
            print(current, now)
            print(position_total)
            time.sleep(10)

    




