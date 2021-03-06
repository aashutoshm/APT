# Import dependencies
import pandas as pd
import os
import time
import sys
import telebot

os.chdir('D:/APT/APT/Paper_Trading')
from datetime import datetime
import Strategy_PaperTrading as strategy

## Initial Inputs
###############################################################
def start(name, lot_size):
    bot_token = '823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA'
    chat_id = '-383311990'
    bot = telebot.TeleBot(token=bot_token)
    message = "Stock selected for today: " + str(name)
    bot.send_message(chat_id, message)

    print("Master Script started", flush=True)
    # max_one_stock_price = 1300
    target_profit_1 = lot_size*2
    semi_target = lot_size
    max_stop_loss = lot_size

    order_status = 'Exit'
    order_signal = ''
    order_price = 0.0
    entry_high_target = 0.0
    entry_low_target = 10000.0
    stop_loss = 0.0
    target = 0.0
    skip_date = datetime.strptime('2019-01-01', '%Y-%m-%d')
    result_list = [order_status, order_signal,
                      order_price, entry_high_target, entry_low_target,
                      stop_loss, target, skip_date]
    Trade_Dataset = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Year', 'DatePart',
                                          'Order_Status', 'Order_Signal', 'Order_Price', 'Target', 'Stop_Loss',
                                          'Hour', 'Minute'])
    count = 0
    while True:
        # Get data after every 5 mins
        if (datetime.now().minute % 5 == 0) and (datetime.now().second >= 3) and count == 0:
            try:
                data = pd.read_csv('D:/APT/APT/Paper_Trading/ohlc_data_' + name + '.csv')
            except:
                time.sleep(1)
                continue
            data.columns = ['Date', 'Open', 'High', 'Low', 'Close']

            # Date Column Handling
            data['Date'] = [datetime.strptime(i, '%Y-%m-%d %H:%M:%S') for i in data['Date']]
            data['Year'] = [i.year for i in data['Date']]
            data['DatePart'] = [i.date() for i in data['Date']]

            # Include Pointer Columns
            data['Order_Status'] = ''
            data['Order_Signal'] = ''
            data['Order_Price'] = 0.0
            data['Target'] = 0.0
            data['Stop_Loss'] = 0.0
            data['Hour'] = [j.hour for j in data['Date']]
            data['Minute'] = [j.minute for j in data['Date']]
            print('Data Preparation Completed')

            # Implement Strategy
            data, result_list = strategy.GapUpStrategy(data,
                                                       target_profit_1,
                                                       semi_target,
                                                       max_stop_loss,
                                                       lot_size,
                                                       result_list[0],
                                                       result_list[1],
                                                       result_list[2],
                                                       result_list[3],
                                                       result_list[4],
                                                       result_list[5],
                                                       result_list[6],
                                                       result_list[7],
                                                       name)
            if data.Order_Signal[0] != "":
                Trade_Dataset = Trade_Dataset.append(data)
                Trade_Dataset.to_csv('PaperTrading_Output' + name + '.csv', index=False)
            time.sleep(250)
            count = 1

        else:
            count = 0

if __name__ == '__main__':
    os.chdir("D:\APT\APT\Paper_Trading")
    name = sys.argv[1]
    lot_size = int(sys.argv[2])
    start(name, lot_size)