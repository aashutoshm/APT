# Import dependencies
import logging
from kiteconnect import KiteTicker
from kiteconnect import KiteConnect
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import datetime
import configparser
import time
import re

print("Starting Trading Engine...")
config = configparser.ConfigParser()
config_path = 'E:/Stuffs/APT/APT/Paper Trading/config.ini'
config.read(config_path)
path = 'E:/Stuffs/APT'
os.chdir(path)

api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']
username = config['USER']['USERNAME']
password = config['USER']['PASSWORD']
pin = config['USER']['PIN']
homepage = 'https://kite.zerodha.com/'

driver = webdriver.Chrome()
page = driver.get(homepage)

print("Authenticating...")
# Logging in using Username and Password
user_id_box = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[2]/input')
password_box = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[3]/input')
log_in_button = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[4]/button')
user_id_box.send_keys(username)
password_box.send_keys(password)
log_in_button.click()
time.sleep(5)

# Logging in using Pin
pin_box = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[2]/div/input')
continue_box = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[3]/button')
pin_box.send_keys(pin)
continue_box.click()
time.sleep(5)

# Redirecting to Kiteconnect
kite = KiteConnect(api_key=api_key)
url = kite.login_url()
page = driver.get(url)
current_url = driver.current_url
request_token = re.search(('request_token=(.*)'), current_url).group(1)[:32]
KRT = kite.generate_session(request_token, api_secret)
kite.set_access_token(KRT['access_token'])
print("Connection Successful")

tokens = [897537]
# tick_data = pd.DataFrame(columns=['token', 'time', 'ltp'])

# Initialise
kws = KiteTicker(api_key, KRT['access_token'])
tick_df = pd.DataFrame(columns=['Token', 'Timestamp', 'LTP'], index=pd.to_datetime([]))
last_saved_time = 15
# tick_df = tick_df.append({'Token': 0, 'Timestamp': 0, 'LTP': 0}, ignore_index=True)


def on_ticks(ws, ticks):
    # Callback to receive ticks.
    global tick_df
    global last_saved_time
    while True:
        print(ticks)
        tick_df = tick_df.append({'Token': ticks[0]['instrument_token'], 'Timestamp': ticks[0]['timestamp'], 'LTP': ticks[0]['last_price']}, ignore_index=True)

        if (datetime.datetime.now().minute % 2 == 0) and (datetime.datetime.now().minute != last_saved_time):
            print(len(tick_df))
            # set timestamp as index
            tick_df = tick_df.set_index(['Timestamp'])
            tick_df['Timestamp'] = pd.to_datetime(tick_df.index, unit='s')

            # convert to OHLC format
            data_ohlc = tick_df['LTP'].resample('5Min').ohlc()

            # save the dataframe to csv
            data_ohlc.to_csv('ohlc_data.csv')
            print("Printed at " + str(datetime.datetime.now()))

            # save the last minute
            last_saved_time = datetime.datetime.now().minute

            # initialize the dataframe
            tick_df = pd.DataFrame(columns=['Token', 'Timestamp', 'LTP'], index=pd.to_datetime([]))
            print(len(data_ohlc))
            data_ohlc = pd.DataFrame()
        time.sleep(5)

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens
    ws.subscribe(tokens)
    # Set TITAN to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, tokens)

# Callback when current connection is closed.
def on_close(ws, code, reason):
    logging.info("Connection closed: {code} - {reason}".format(code=code, reason=reason))


# Callback when connection closed with error.
def on_error(ws, code, reason):
    logging.info("Connection error: {code} - {reason}".format(code=code, reason=reason))


# Callback when reconnect is on progress
def on_reconnect(ws, attempts_count):
    logging.info("Reconnecting: {}".format(attempts_count))


# Callback when all reconnect failed (exhausted max retries)
def on_noreconnect(ws):
    logging.info("Reconnect failed.")


# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_close = on_close
kws.on_error = on_error
kws.on_connect = on_connect
kws.on_reconnect = on_reconnect
kws.on_noreconnect = on_noreconnect

# count = 0
# while True:
#     count += 1
#     if count % 2 == 0:
#         if kws.is_connected():
#             print("### Set mode to LTP for all tokens")
#             kws.set_mode(kws.MODE_LTP, tokens)
#     else:
#         if kws.is_connected():
#             print("### Set mode to quote for all tokens")
#             kws.set_mode(kws.MODE_QUOTE, tokens)

#     time.sleep(5)

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect(threaded=True)



# LTP
# tick = [{'tradable': True, 'mode': 'ltp', 'instrument_token': 897537, 'last_price': 1101.2}]

# FULL
# ticks = [{'tradable': True, 'mode': 'full', 'instrument_token': 897537, 'last_price': 1085.6, 'last_quantity': 14, 'average_price': 1089.2, 'volume': 1030686, 'buy_quantity': 863713, 'sell_quantity': 269903, 'ohlc': {'open': 1110.0, 'high': 1110.05, 'low': 1079.0, 'close': 1101.2}, 'change': -1.4166363966582034, 'last_trade_time': datetime.datetime(2019, 7, 15, 11, 6, 11), 'oi': 0, 'oi_day_high': 0, 'oi_day_low': 0, 'timestamp': datetime.datetime(2019, 7, 15, 11, 6, 12), 'depth': {'buy': [{'quantity': 24, 'price': 1085.45, 'orders': 1}, {'quantity': 90, 'price': 1085.4, 'orders': 2}, {'quantity': 23, 'price': 1085.35, 'orders': 1}, {'quantity': 12, 'price': 1085.3, 'orders': 2}, {'quantity': 231, 'price': 1085.25, 'orders': 2}], 'sell': [{'quantity': 41, 'price': 1085.6, 'orders': 4}, {'quantity': 219, 'price': 1086.0, 'orders': 3}, {'quantity': 2, 'price': 1086.1, 'orders': 1}, {'quantity': 9, 'price': 1086.15, 'orders': 1}, {'quantity': 46, 'price': 1086.25, 'orders': 1}]}}]

# QUOTE
# tick = [{'tradable': True, 'mode': 'quote', 'instrument_token': 897537, 'last_price': 1086.2, 'last_quantity': 1, 'average_price': 1089.13, 'volume': 1055785, 'buy_quantity': 864953, 'sell_quantity': 438516, 'ohlc': {'open': 1110.0, 'high': 1110.05, 'low': 1079.0, 'close': 1101.2}, 'change': -1.3621503814021068}]

# tick_df = pd.read_csv('data/tick_data.csv', parse_dates=['Timestamp'])

# tick_df = tick_df.set_index(['Timestamp'])

# tick_df.index = pd.to_datetime(tick_df.index, unit='s')


# data_ohlc = tick_df['LTP'].resample('5Min').ohlc()

# print(data_ohlc)

# data_ohlc.to_csv('ohlc.csv')

# tick_df = tick_df.append({'Token': 0, 'Timestamp': 0, 'LTP': 0}, ignore_index=True)