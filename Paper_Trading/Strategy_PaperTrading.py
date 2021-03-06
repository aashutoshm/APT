## Import Libraries
###############################################################
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import copy
import kiteconnect as kc
import os
import telebot

global chat_id
global bot
bot_token = '823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA'
chat_id = '-383311990'
bot = telebot.TeleBot(token=bot_token)

## Function to Execute Long Entry
###############################################################
def long_entry(data, index, lot_size, sl, tp, name):
    data.Order_Status[index] = 'Entry'
    data.Order_Signal[index] = 'Buy'
    data.Order_Price[index] = data.Close[index]
    # data.Quantity[index] = qty
    data.Target[index] = data.Close[index] + (tp / lot_size)
    data.Stop_Loss[index] = sl
    print('Long Entry @' + str(data.Close[index]))
    bot.send_message(chat_id, name + ': Long Entry @' + str(data.Close[index]))
    return data


# Function to Execute Long Entry
##############################################################
def short_entry(data, index, lot_size, sl, tp, name):
    data.Order_Status[index] = 'Entry'
    data.Order_Signal[index] = 'Sell'
    data.Order_Price[index] = data.Close[index]
    # data.Quantity[index] = qty
    data.Target[index] = data.Close[index] - (tp / lot_size)
    data.Stop_Loss[index] = sl
    print('Short Entry @' + str(data.Close[index]))
    bot.send_message(chat_id, name + ': Short Entry @' + str(data.Close[index]))
    return data


# Function to Execute Long Exit
##############################################################
def long_exit(data, index, stop_loss, name):
    data.Order_Status[index] = 'Exit'
    data.Order_Signal[index] = 'Sell'
    data.Order_Price[index] = stop_loss
    print('Long Exit @' + str(stop_loss))
    bot.send_message(chat_id, name + ': Long Exit @' + str(stop_loss))
    return data


# Function to Execute Long Exit
##############################################################
def short_exit(data, index, stop_loss, name):
    data.Order_Status[index] = 'Exit'
    data.Order_Signal[index] = 'Buy'
    data.Order_Price[index] = stop_loss
    print('Short Exit @' + str(stop_loss))
    bot.send_message(chat_id, name + ': Short Exit @' + str(stop_loss))
    return data


## Pivot Point Calculation
###############################################################
def pivotpoints(data, type='simple'):
    type_str = '_Simple' if type == 'simple' else '_Fibonacci'
    if 'PivotPoint' in data.columns:
        data = data.drop(['Day_High',
                          'Day_Low',
                          'Day_Open',
                          'Day_Close',
                          'PivotPoint'], axis=1)

    data['DatePart'] = [i.date() for i in data['Date']]

    aggregation = {
        'High': {
            'Day_High': 'max'
        },
        'Low': {
            'Day_Low': 'min'
        },
        'Open': {
            'Day_Open': 'first'
        },
        'Close': {
            'Day_Close': 'last'
        }
    }
    data_datelevel = data.groupby('DatePart').agg(aggregation)
    data_datelevel.columns = data_datelevel.columns.droplevel()
    data_datelevel['DatePart'] = data_datelevel.index
    data_datelevel['PivotPoint'] = (data_datelevel['Day_High'] + data_datelevel['Day_Low'] +
                                    data_datelevel['Day_Close']) / 3
    data_datelevel['S1_Pivot' + type_str] = (data_datelevel['PivotPoint'] * 2) - data_datelevel['Day_High'] if \
        type == 'simple' else data_datelevel['PivotPoint'] - \
                              (0.382 * (data_datelevel['Day_High'] -
                                        data_datelevel['Day_Low']))
    data_datelevel['S2_Pivot' + type_str] = data_datelevel['PivotPoint'] - (data_datelevel['Day_High'] -
                                                                            data_datelevel['Day_Low']) if \
        type == 'simple' else data_datelevel['PivotPoint'] - \
                              (0.618 * (data_datelevel['Day_High'] -
                                        data_datelevel['Day_Low']))
    data_datelevel['R1_Pivot' + type_str] = (data_datelevel['PivotPoint'] * 2) - data_datelevel['Day_Low'] if \
        type == 'simple' else data_datelevel['PivotPoint'] + \
                              (0.382 * (data_datelevel['Day_High'] -
                                        data_datelevel['Day_Low']))
    data_datelevel['R2_Pivot' + type_str] = data_datelevel['PivotPoint'] + (data_datelevel['Day_High'] -
                                                                            data_datelevel['Day_Low']) if \
        type == 'simple' else data_datelevel['PivotPoint'] + \
                              (0.618 * (data_datelevel['Day_High'] -
                                        data_datelevel['Day_Low']))
    if type != 'simple':
        data_datelevel['S3_Pivot' + type_str] = data_datelevel['PivotPoint'] - (data_datelevel['Day_High'] -
                                                                                data_datelevel['Day_Low'])
        data_datelevel['R3_Pivot' + type_str] = data_datelevel['PivotPoint'] + (data_datelevel['Day_High'] -
                                                                                data_datelevel['Day_Low'])

    data_datelevel['PivotDate'] = data_datelevel['DatePart'].shift(-1)
    data_datelevel = data_datelevel.drop(['DatePart'], axis=1)
    pivot_data = pd.merge(data, data_datelevel, 'left',
                          left_on='DatePart',
                          right_on='PivotDate')
    pivot_data = pivot_data.drop(['PivotDate'], axis=1)
    return pivot_data

## Gap-Up Strategy Function For Paper Trading
###############################################################
def GapUpStrategy(data, target_profit_1, semi_target, max_stop_loss, lot_size,
                  order_status, order_signal,
                  order_price, entry_high_target, entry_low_target,
                  stop_loss, target, skip_date, name):
    bot_token = '823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA'
    chat_id = '-383311990'
    bot = telebot.TeleBot(token=bot_token)

    if data.Date[0].hour == 9 and data.Date[0].minute == 15:
        # day_flag = 'selected' if ((ads_iteration.Open[i] > entry_high_target) or
        #                          (entry_low_target > ads_iteration.Open[i])) else 'not selected'
        # skip_date = ads_iteration.DatePart[i] if day_flag == 'not selected' else skip_date
        entry_high_target = data.High[0]
        entry_low_target = data.Low[0]

    # Exit from Ongoing Order, if any (Check)
    elif data.Date[0].hour == 15 and data.Date[0].minute == 20:
        if order_status == 'Entry':
            if order_signal == 'Buy':
                data = long_exit(data, 0, data.Close[0], name)
                order_status = data.Order_Status[0]
                order_signal = data.Order_Signal[0]
                order_price = data.Order_Price[0]
                # money = money + order_qty * order_price
                # target_cross = 0
                # order_qty = 0
                print('Order Status: ' + order_status)
                print('Order Signal: ' + order_signal)

            else:
                data = short_exit(data, 0, data.Close[0], name)
                order_status = data.Order_Status[0]
                order_signal = data.Order_Signal[0]
                order_price = data.Order_Price[0]
                # money = money + order_qty * order_price
                # target_cross = 0
                # order_qty = 0
                print('Order Status: ' + order_status)
                print('Order Signal: ' + order_signal)

    elif data.DatePart[0] != skip_date:
        if order_status == 'Exit':
            # Long Entry Action
            if data.Close[0] > entry_high_target:
                # calc_stop_loss = max(entry_low_target,(ads_iteration.Next_Candle_Open[i] - (max_stop_loss / lot_size)))
                calc_stop_loss = data.Close[0] - (max_stop_loss / lot_size)
                data = long_entry(data, 0, lot_size, calc_stop_loss, target_profit_1, name)
                order_status = data.Order_Status[0]
                order_signal = data.Order_Signal[0]
                target = data.Target[0]
                stop_loss = data.Stop_Loss[0]
                order_price = data.Order_Price[0]
                # order_qty = data.Quantity[i]
                # money = money - order_qty * order_price
                # data.Money[i] = money

            # Short Entry Action
            elif data.Close[0] < entry_low_target:
                # calc_stop_loss = min(entry_high_target, (ads_iteration.Next_Candle_Open[i] + (max_stop_loss / lot_size)))
                calc_stop_loss = data.Close[0] + (max_stop_loss / lot_size)
                data = short_entry(data, 0, lot_size, calc_stop_loss, target_profit_1, name)
                order_status = data.Order_Status[0]
                order_signal = data.Order_Signal[0]
                target = data.Target[0]
                stop_loss = data.Stop_Loss[0]
                order_price = data.Order_Price[0]
                # order_qty = data.Quantity[0]
                # money = money + order_qty * order_price

        # Decision Tree For Exiting the Order
        elif order_status == 'Entry':
            # Exiting From Long Position
            if order_signal == 'Buy':

                # Exit Condition
                if data.Low[0] < stop_loss:
                    data = long_exit(data, 0, stop_loss, name)
                    order_status = data.Order_Status[0]
                    order_signal = data.Order_Signal[0]
                    order_price = data.Order_Price[0]
                    # money = money + order_qty * order_price
                    # target_cross = 0
                    # order_qty = 0
                    print('Order Status: ' + order_status)
                    print('Order Signal: ' + order_signal)

                elif data.High[0] > target:
                    # target_cross = target_cross + 1
                    data = long_exit(data, 0, target, name)
                    order_status = data.Order_Status[0]
                    order_signal = data.Order_Signal[0]
                    order_price = data.Order_Price[0]
                    # money = money + order_qty * order_price
                    # target_cross = 0
                    # order_qty = 0
                    print('Order Status: ' + order_status)
                    print('Order Signal: ' + order_signal)
                # Semi Exit
                # if target_cross == 1:
                #     ads_iteration.Quantity[i] = int(order_qty * 0.5)
                #     ads_iteration.Order_Price[i] = target
                #     stop_loss = order_price
                #     order_price = target
                #     order_qty = ads_iteration.Quantity[i]
                #     money = money + order_qty * order_price
                #     target = ((target_profit_2 - target_profit_1) / lot_size) + order_price
                #
                # else:
                #     ads_iteration = long_exit(ads_iteration, i, target)
                #     order_status = ads_iteration.Order_Status[i]
                #     order_signal = ads_iteration.Order_Signal[i]
                #     order_price = ads_iteration.Order_Price[i]
                #     money = money + order_qty * order_price
                #     target_cross = 0
                #     order_qty = 0
                #     print('Order Status: ' + order_status)
                #     print('Order Signal: ' + order_signal)
                elif (data.High[0] - order_price) > (semi_target / lot_size):
                    stop_loss = copy.deepcopy(order_price + ((semi_target / lot_size) * 0.5))

            # Exiting From Short Position
            elif order_signal == 'Sell':
                # Exit Condition
                if data.High[0] > stop_loss:
                    data = short_exit(data, 0, stop_loss, name)
                    order_status = data.Order_Status[0]
                    order_signal = data.Order_Signal[0]
                    order_price = data.Order_Price[0]
                    # money = money - order_qty * order_price
                    # target_cross = 0
                    # order_qty = 0
                    print('Order Status: ' + order_status)
                    print('Order Signal: ' + order_signal)

                # Order Holding Calculation
                elif data.Low[0] < target:
                    # target_cross = target_cross + 1
                    data = short_exit(data, 0, target, name)
                    order_status = data.Order_Status[0]
                    order_signal = data.Order_Signal[0]
                    order_price = data.Order_Price[0]
                    # money = money - order_qty * order_price
                    # target_cross = 0
                    # order_qty = 0
                    print('Order Status: ' + order_status)
                    print('Order Signal: ' + order_signal)
                    # Semi Exit
                    # if target_cross == 1:
                    #     ads_iteration.Quantity[i] = int(order_qty * 0.5)
                    #     ads_iteration.Order_Price[i] = target
                    #     stop_loss = order_price
                    #     order_price = target
                    #     order_qty = ads_iteration.Quantity[i]
                    #     money = money - order_qty * order_price
                    #     target = ((target_profit_2 - target_profit_1) / lot_size) + order_price
                    #
                    # else:
                    #     ads_iteration = short_exit(ads_iteration, i, target)
                    #     order_status = ads_iteration.Order_Status[i]
                    #     order_signal = ads_iteration.Order_Signal[i]
                    #     order_price = ads_iteration.Order_Price[i]
                    #     money = money - order_qty * order_price
                    #     target_cross = 0
                    #     order_qty = 0
                    #     print('Order Status: ' + order_status)
                    #     print('Order Signal: ' + order_signal)

                elif (order_price - data.Low[0]) > (semi_target / lot_size):
                    stop_loss = copy.deepcopy(order_price - ((semi_target / lot_size) * 0.5))

    entry_high_target = max(entry_high_target, data.High[0])
    entry_low_target = min(entry_low_target, data.Low[0])

    result_list = [order_status, order_signal,
                  order_price, entry_high_target, entry_low_target,
                  stop_loss, target, skip_date]
    return data, result_list
