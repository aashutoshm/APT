# Import dependencies
import configparser
import re
import os
from selenium import webdriver
import time
from kiteconnect import KiteConnect
import pandas as pd

# Get all info
print("Starting Trading Engine...", flush=True)
config = configparser.ConfigParser()
# For Ubuntu
# path = os.getcwd()
# path = '/home/ubuntu/APT/APT/Simulation'

## For Windows
path = os.getcwd()
path = 'F:/DevAPT/APT/Paper_Trading'

os.chdir(path)
config_path = path + '/config.ini'
config.read(config_path)
api_key = config['API']['API_KEY']
api_secret = config['API']['API_SECRET']
username = config['USER']['USERNAME']
password = config['USER']['PASSWORD']
pin = config['USER']['PIN']
homepage = 'https://kite.zerodha.com/'


## Selenium for ubuntu
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(executable_path='F:\DevAPT\APT\chromedriver.exe',
                          chrome_options=chrome_options)
page = driver.get(homepage)

# Selenium for windows
# driver = webdriver.Chrome(executable_path='D:\\DevAPT\\APT\\chromedriver.exe')
# page = driver.get(homepage)

# Login using username and password
print("Authenticating...", flush=True)
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
time.sleep(3)

# Log in using Pin
pin_box = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[2]/div/input')
continue_box = driver.find_element_by_xpath(
    '//*[@id="container"]/div/div/div/form/div[3]/button')
pin_box.send_keys(pin)
continue_box.click()
time.sleep(3)

# Redirecting to Kiteconnect
kite = KiteConnect(api_key=api_key)
url = kite.login_url()
page = driver.get(url)
current_url = driver.current_url
request_token = re.search('request_token=(.*)', current_url).group(1)[:32]
KRT = kite.generate_session(request_token, api_secret)
print("Connection Successful")
driver.close()

# Get Kite Object
kite = KiteConnect(api_key=api_key)
kite.set_access_token(KRT['access_token'])

## Order Testing
##############################################################################

# Initial Inputs

# Place a Unexecutable Limit Order (OrderId, and Get Response)
# order_id = kite.place_order(tradingsymbol="ADANIPORTS",
#                             variety= 'regular',
#                             exchange=kite.EXCHANGE_NSE,
#                             transaction_type=kite.TRANSACTION_TYPE_BUY,
#                             quantity=1,
#                             price= 360.50,
#                             order_type=kite.ORDER_TYPE_LIMIT,
#                             product=kite.PRODUCT_MIS)
# order_list = pd.DataFrame(kite.orders())
# trade_list = kite.trades()
# order_id_2 = kite.modify_order(variety= 'regular',
#                                order_id= order_id,
#                                quantity=1,
#                                price=362,
#                                order_type=kite.ORDER_TYPE_LIMIT)
# order_list = pd.concat([order_list,pd.DataFrame(kite.orders())],axis=0)
# trade_list = pd.DataFrame(kite.trades())
# Modify that order (immidiate and orders function)
# kite.trades()

# Cancel that order (immidiate and orders function)
# kite.cancel_order(variety='regular',
#                   order_id=order_id)
# trade_list = pd.concat([trade_list,pd.DataFrame(kite.trades())],axis=0)
# order_list = pd.concat([order_list,pd.DataFrame(kite.orders())],axis=0)
# Place an Execuatable Limit Order

# Market Order

# Bracket Order
order_id = kite.place_order(tradingsymbol="ADANIPORTS",
                            variety= 'bo',
                            exchange=kite.EXCHANGE_NSE,
                            transaction_type=kite.TRANSACTION_TYPE_BUY,
                            quantity=1,
                            price= 365.90,
                            order_type=kite.ORDER_TYPE_LIMIT,
                            product=kite.PRODUCT_MIS,stoploss=3,squareoff=5)

orders = pd.DataFrame(kite.orders())

# Automated Bracket Order Modify
order_id = kite.modify_order(variety='bo',order_id=order_id,quantity=1,price=366.0)
orders = pd.DataFrame(kite.orders())
orders.to_csv('F:\DevAPT\APT\Simulation\Sample_Order_Response.csv')

# cancel BO
kite.cancel_order(variety='bo',
                  order_id=order_id)
