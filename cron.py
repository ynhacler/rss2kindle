#coding:utf-8

#TODO 将cron分为若干个cron文件

import logging
from datetime import datetime,timedelta
#from time import mktime

from rq import Connection, Queue
from redis import Redis

import model as m
import task
import config

redis_conn = Redis()

queue = Queue('cron',connection=redis_conn)



def cron_sync_feed():
    #TODO 考虑是否必要只取有用的字段。
    db = m.Session()
    feeds = db.query(m.Feed).filter_by(active=True).all()
    for feed in feeds:
        logging.info('cron_sync_feed:id->%s slug->%s ' %(str(feed.id), feed.slug))
        queue.enqueue(task.sync_feed,feed.slug)
    db.close()

def cron_fetch_image():
    db = m.Session()
    entries = db.query(m.Entry).filter_by(hidden=False, got_img=False).all()
    for entry in entries:
        if entry.feed.fetch_image:
            continue
        logging.info('cron_fetch_image:entry id->%s ' %(str(entry.id)))
        queue.enqueue(task.fetch_img, entry.feed.slug, entry.id)
    db.close()



def cron_push():
    db = m.Session()
    users = db.query(m.User).filter_by(active=True).all()
    for user in users:
        #if user.login_timestamp + timedelta(days=config.expire_time) \
        #        < datetime.now():
            #TODO send mail to let user know.
        #    continue
        now = datetime.now()
        if user.push_timestamp + timedelta(hours=12) > now:
            continue
        if now.hour < (user.push_timing * 2) or\
                now.hour >= (user.push_timing * 2 +2) :
            continue
        logging.info('cron_push: id-> %s email->%s' %(str(user.id), user.email))
        queue.enqueue(task.push, user.id)
    db.close()
        
   
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    now = datetime.now()
    if now.minute >= 30:
        cron_sync_feed()
    cron_fetch_image()
    cron_push()

    
