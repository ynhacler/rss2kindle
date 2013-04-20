#coding:utf-8

import logging

from hashlib import md5
from random import random
from functools import wraps
from datetime import datetime
from time import mktime

import smtplib,email
from email.message import Message
from email.header import Header
from email.mime.text import MIMEText



def get_timestamp(obj):
    ts = getattr(obj,'date_parsed', None) or\
            getattr(obj, 'published_parsed', None)
    if ts is not None :
        return  datetime.fromtimestamp(mktime(ts))
    return None 




def md5_hexdigest(seed=None):
    if seed is None:
        seed = str(random())
    return md5(seed).hexdigest()


#TODO Email 要移出去 放到 mail.py?maybe
class Email():
    def __init__(self,host, port=25, timeout=5, user=None, password=None):
        #logging.info('tools.Email.__init__->' +host)
        self.args = {}
        self.args['host'] = host
        self.args['port'] = port 
        self.args['timeout'] = timeout
        self.user = user 
        self.password = password
        if user is not None and password is not None:
            self.require_auth = True
        else:
            self.require_auth = False
        self._connection = None

    def connection(self):
        if self._connection is not None:
            self.close()
        logging.info("tools.Email.connection->"+\
                str(self.args))
        self._connection = smtplib.SMTP(**self.args)
        if self.require_auth:
            self._connection.login(self.user,
                    self.password)

    def close(self):
        if self._connection is not None:
            self._connection.quit()
            self._connection = None

    def send(self, subject, txt, frm, to):
        """
        send an email without handling exception
        for dev only.
        """
        self.connection()
        msg = MIMEText(txt,_charset='utf-8')
        msg['From'] = frm
        msg['To'] = to
        msg['Subject'] =Header(subject,charset="utf-8")
        msg['Date'] = email.utils.formatdate(localtime=True)
        self._connection.send_message(msg,frm,to)
        logging.info("tools.Email.send->mail from %s to %s,subject:%s" \
                %(frm, to, subject))
        self.close()
            



