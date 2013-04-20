#coding=utf8
from datetime import timedelta
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base  import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import mimetypes
from random import randrange
import config as c

ATTACH_FILENAME= 'rss4kindle_feed.mobi' 

def send_mail(to_addr, attach_path):
    from_addr = str(randrange(10000,99999)) + c.email_domain
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = 'rss4kindle 新闻'
    msg.attach(MIMEText(''))
    ctype, encoding = mimetypes.guess_type(attach_path)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    part = MIMEBase(maintype, subtype)
    with open(attach_path, 'rb') as fp:
        part.set_payload(fp.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment',
            filename=ATTACH_FILENAME)
    msg.attach(part)
    smtp = smtplib.SMTP('127.0.0.1', 25)
    smtp.sendmail(from_addr, to_addr, msg.as_string())
    smtp.quit()
        

def send_notice(subject, content, to_addr):
    from_addr = c.notice_email
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    smtp = smtplib.SMTP('127.0.0.1', 25)
    smtp.sendmail(from_addr, to_addr, msg.as_string())
    smtp.quit()
