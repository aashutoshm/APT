## Import Libraries
###############################################################
import pandas as pd
import numpy as np
import sys
import os
import requests
from datetime import datetime
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import pdfkit

## Function to send mail
###############################################################
def send_mail(mail_from,mail_to,subject,message,file_paths,password):
    msg = MIMEMultipart()
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg["Subject"] = subject
    # attach the body with the msg instance
    msg.attach(MIMEText(message, 'plain'))

    # open the files to be sent
    for file_path in file_paths:
        attachment = open(file_path, "rb")
        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')

        # To change the payload into encoded form
        p.set_payload((attachment).read())

        # encode into base64
        encoders.encode_base64(p)

        p.add_header('Content-Disposition', "attachment; filename= %s" % file_path)

        # attach the instance 'p' to instance 'msg'
        msg.attach(p)

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login(mail_from, password)

    # Converts the Multipart msg into a string
    text = msg.as_string()

    # sending the mail
    s.sendmail(mail_from, mail_to, text)

    # terminating the session
    s.quit()


## Initial Inputs
###############################################################
# Windows
# folder_path = 'F:/DevAPT/APT/Simulation'
# wkhtmltopdf_path = 'F:/DevAPT/APT/Paper_Trading/wkhtmltopdf/bin/wkhtmltopdf.exe'

# For Ubuntu
folder_path = '/home/ubuntu/APT/APT/Simulation'
wkhtmltopdf_path = '/home/ubuntu/anaconda3/bin/wkhtmltopdf'

file_phrase = 'Simulation_Output'
stock_list_path = 'stock_list_updated.csv'

bot_mail_id = 'apt.automated@gmail.com'
bot_mail_password = 'algotrading2019'
recipients = ['anubhab.ghosh95@gmail.com','sarfraz.contact@gmail.com','arkajeet75@gmail.com']

## Main Body
###############################################################
stock_list = pd.read_csv(folder_path + '/' + stock_list_path)
time_now = str(datetime.strptime(stock_list['Date'][0],'%m/%d/%Y').date())
print('Stock List Imported',flush=True)

os.chdir(folder_path)
summary_df = pd.DataFrame()
for i in stock_list.index.values:
    # Get the Stock wise Output File names
    stock_name = stock_list['Company'][i]
    file = file_phrase + stock_name + '.csv'

    trade_data = pd.read_csv(file)
    print('Calculating For ' + stock_name,flush=True)
    trade_count = trade_data['Order_Status'][trade_data['Order_Status'] == 'Exit'].count()

    trade_data['Double_Entry_Flag'] = np.where(trade_data['Order_Status'] == 'Exit',
                                               np.where(trade_data['Target'] != 0.0,1,0),0)
    trade_data['Amount'] = np.where(trade_data['Order_Signal'] == 'Buy',
                                    np.where(trade_data['Double_Entry_Flag'] == 1,
                                             (-2) * trade_data['Order_Price'],
                                             (-1) * trade_data['Order_Price']),
                                    np.where(trade_data['Order_Signal'] == 'Sell',
                                             np.where(trade_data['Double_Entry_Flag'] == 1,
                                                      2 * trade_data['Order_Price'],
                                                      trade_data['Order_Price']),0.0))
    profit = trade_data['Amount'].sum()
    net_profit = (profit * stock_list['Lot_Size'][i]) - (trade_count * 200)
    summary_df = pd.concat([summary_df,pd.DataFrame(data = [[stock_name,profit,trade_count,net_profit]],
                                                    columns = ['Company','Profit','Trades','Net_Profit'])])
    print('Completed',flush=True)

# Calculate Total Profit
total_profit = summary_df.Net_Profit.sum()
total_trades = summary_df.Trades.sum()
total_summary = pd.DataFrame([['Total',np.nan,total_trades,total_profit]],
                             columns = ['Company','Profit','Trades','Net_Profit'])
summary_df = pd.concat([summary_df,total_summary])
time_now = str(datetime.now().date())

# write Summary as CSV
print('Writing Summary as CSV',flush=True)
output_file_path = 'Simulation_Summary_' + time_now + '.csv'
summary_df.to_csv(output_file_path,index= False)

# Send csv as Mail
print('Sending CSV as Email',flush=True)
body_text = 'Hi All,\n\nPFA the summary of simulation of paper trading for ' + time_now + '\n\nRegards,\nAPT BOT'
attachments = [file_phrase + stock_name + '.csv' for stock_name in stock_list['Company']]
attachments = attachments.append(output_file_path)
for target_mail_id in recipients:
    send_mail(bot_mail_id, 'anubhab.ghosh95@gmail.com', 'Paper Trading Result of The Day',
              body_text, attachments, bot_mail_password)

# Save csv as PDF
output_pdf_path = output_file_path[:(len(output_file_path) - 3)] + 'pdf'
output_html_path = output_file_path[:(len(output_file_path) - 3)] + 'html'
summary_df.to_html(output_html_path,index=False)
config = pdfkit.configuration(wkhtmltopdf= wkhtmltopdf_path)
pdfkit.from_file(output_html_path,output_pdf_path,configuration=config)

# Send pdf to telegram
pdf_summary = open(output_pdf_path, 'rb')
requests.post("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendDocument?chat_id=-383311990",
              files={'document': pdf_summary})
message = 'csv file of daily report is sent in email'
requests.get("https://api.telegram.org/bot823468101:AAEqDCOXI3zBxxURkTgtleUvFvQ0S9a4TXA/sendMessage?chat_id=-383311990&text=" + message)


