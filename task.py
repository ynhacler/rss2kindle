#coding:utf-8

import model as m
import config
from tool import get_timestamp, md5_hexdigest
from sendMail import send_mail, send_notice

import feedparser
from jinja2 import Environment, FileSystemLoader 
from shutil import copy, rmtree
import os
from os import path, listdir, system
import re
from hashlib import md5
import logging

try:
    #py3
    from urllib.request import urlopen 
except ImportError:
    #py2
    from urllib import urlopen

from datetime import datetime,timedelta
from time import mktime

#jinja2初始化环境
tmp_env = Environment(loader=FileSystemLoader(config.template_path))

PICTURE_RE = re.compile(r'src="(http://[-_+=a-zA-Z0-9/.]+(jpe?g|gif|png)[?]?[^"]*)"')


#把rss里的信息分析后存入数据库
def sync_feed(slug, check_exist=True):
    """
    抓取feed文本内容
    """
    #日志
    logging.info('task.sync_feed: slug->%s ' %(slug))
    db = m.Session()#数据库的session，不是HTTP的。
    
    feed = db.query(m.Feed).filter_by(slug=slug).first()
    
    
    if feed is None: 
        logging.warning('feed not found , slug->%s' %(slug))
        db.close()
        return 
    
    #用feedsparser取得rss
    data = feedparser.parse(feed.url)
    if not data.entries: return #内容为空就返回

    #时间戳
    feed_timestamp = get_timestamp(data.feed) or \
            datetime.now()
    fetch_timestamp = datetime.now()
    
    #第三个参数是it is returned when the attribute doesn't exist
    feed_title = getattr(data.feed,'title',feed.name)
    for entry in data.entries:
        title = getattr(entry,'title','')
        author = getattr(entry,'author','')
        source_link = getattr(entry,'link','')
        time_stamp = get_timestamp(entry) or feed_timestamp,
        if check_exist:
            old_entry = db.query(m.Entry).\
                    filter_by(author=author,
                            fid=feed.id,
                            title=title,
                            source_link=source_link).first()
            if old_entry  is not None: 
                continue
        if hasattr(entry, 'content') and entry.content:
            content = u'\n'.join([c.value for c in entry.content])
        else:
            content = getattr(entry,'summary','')
            
        #存入数据库
        new_entry = m.Entry(
                title = title,
                time_stamp = time_stamp,
                fetch_timestamp = fetch_timestamp,
                author = author,
                source_link = source_link,
                content = content,
                fid = feed.id)
        db.add(new_entry)
        
    feed.sync_time = datetime.now()
    try:
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()





PICTURE_RE = re.compile(r'src="(http://[-_+=a-zA-Z0-9/.]+(jpe?g|gif|png)[?]?[^"]*)"')

def fetch_img(feed_slug, eid, force=False):
    """
    获取图片
    """
    #eid文档id号
    
    #日志
    logging.info('task.fetch_image:entry id->%s ' %(str(eid)))
    
    #数据库session
    db = m.Session()
    feed = db.query(m.Feed).filter_by(slug=feed_slug).first()
    if feed is not None and not feed.fetch_image:
        db.close()
        return
    
    #根据文章id提取rss
    entry = db.query(m.Entry).filter_by(id=eid).first()
    
    #rss是否合法或存在图片地址
    if entry is None or (entry.got_img and not force):
        logging.warning('entry not found , entry id->%s \n'
                'or encounter error when I try fetch image for it last time.' %(eid))
        db.close()
        return

    img_serial = 0
    total_size = 0
    
    #解析并提取图片地址
    matches = list(PICTURE_RE.finditer(entry.content, re.I)) 
    
    #创建存储图片的文件夹
    if matches and not path.exists(path.join(config.img_storage_path,str(entry.id))):
        os.mkdir(path.join(config.img_storage_path,str(entry.id)))
        
    for match in matches:
        #图片类型
        if match.group(2).strip().lower() == 'gif':
            extend, media_type= '.gif', 'image/gif'
        elif match.group(2).strip().lower() == 'png':
            extend, media_type = '.png', 'image/png'
        else:
            extend, media_type = '.jpg', 'image/jpeg'
            
        #求md5
        file_name = md5(feed_slug+str(entry.id)+str(img_serial)).hexdigest()
        
        #创建图片文件
        with open(path.join(config.img_storage_path,str(entry.id),file_name+extend), 'wb') as f: 
            try:
                #读图片
                resopne = urlopen(match.group(1))
            except Exception, e:
                logging.warning("encounter exception %s" %(str(e)))
                continue

            if resopne.getcode() != 200:
                logging.warning("response status %s \n Can not fetch img from src: %s",response.status, match.group(1))
                continue
            #写入图片
            f.write(resopne.read())
        #endwith
        
        #得到所有图片的大小
        total_size += path.getsize(path.join(config.img_storage_path,str(entry.id),file_name+extend))
        
        #图片信息存入数据库
        img = m.Image(eid = entry.id, serial_no = img_serial, file_name = file_name, extend = extend)
        db.add(img)
        img_serial += 1
        
        #图片体积过大就报错
        if total_size >= config.img_size_per_entry:
            logging.warning('entry %s contain too much image size: %sM%sK' %( eid, total_size/1024/1024, total_size%1024))
            break
    #endfor
    entry.got_img=True
    try:
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def push(uid):
    
    #日志
    logging.info('task.push:user id->%s ' %(str(uid)))
    #数据库session
    db = m.Session()
    
    #查询用户信息
    user = db.query(m.User).filter_by(id=uid).first()
    if user is None:
        logging.warning(u'task.push user not found uid->%s' %(str(uid)))
        db.close()
        return
    play_order = 1
    feeds = []
    total_image_size  =  0
    
    #把用户订阅的rss提取出来
    #for feed in user.feeds:
    for subscription in user.subscription_relation:
        if not subscription.active:
            continue
        
        #订阅的rss
        feed = subscription.feed
        
        #用户刚推送过就不推送
        if user.push_timestamp > feed.sync_time:
            continue
        
        #提取文章
        entries = [ e for e in feed.entries \
                if e.fetch_timestamp > subscription.subscribe_timestamp \
                and len(e.images) <4]
                
        if len(entries) <= 0:
            continue
        
        latest_timestamp = max([ e.fetch_timestamp for e in entries])
        
        play_order += 1
        f = {'fid': str(feed.id),
                'name': feed.name,
                'play_order': play_order,
                'entries': [],
            }
            
        #处理文章中的章节
        for e in entries:
            play_order += 1
            entry = { 'title': e.title,
                    'author': e.author,
                    'source_link': e.source_link,
                    'time_stamp': e.time_stamp,
                    'play_order': play_order,
                    'eid': str(e.id),
                    }
            if len(e.images) ==  0 or not feed.fetch_image or total_image_size >= config.img_size_per_push:
                #没有图片
                    entry['content'] = e.content
            else:
                #有图片
                img_map = {}
                for i,match in enumerate(PICTURE_RE.finditer(e.content,re.I)):

                    #计算添加的图片大小
                    total_image_size += path.getsize(path.join(config.img_storage_path,
                        str(e.id), e.images[i].file_name + e.images[i].extend))
                    
                    #图片总体积过大就不放入
                    if total_image_size >= config.img_size_per_push:
                        break

                    #取得图片地址
                    img_path = path.join(config.img_storage_dir, 
                            str(e.id),
                            e.images[i].file_name + e.images[i].extend
                            )
                            
                    #把http地址换成本机图片地址
                    img_map[match.group(1)] = 'src="%s"' %(img_path)
                
                entry['content'] = PICTURE_RE.sub( lambda match: img_map[match.group(1)], e.content)
                
            f['entries'].append(entry)
            subscription.subscribe_timestamp = latest_timestamp
        #endfor
        
        #文章放入订阅中
        feeds.append(f)
        
    if len(feeds) == 0:
        logging.info('task.push:user id->%s has no update' %(str(uid)))
        db.close()
        return 
    #endfor-else
    wrap = {'feeds' : feeds,
            'title' : 'kindle daily news',
            'date' : datetime.now(),
            'language' : 'zh-cn',
            }

    # TOC (NCX)
    render_and_write('mobi/toc.xml', wrap, 'toc.ncx', config.tmp_path)
    # TOC (HTML)
    render_and_write('mobi/toc.html', wrap, 'toc.html', config.tmp_path)
    # OPF
    render_and_write('mobi/opf.xml', wrap, 'daily.opf', config.tmp_path)
    for feed in feeds:
        render_and_write('mobi/feed.html', feed, feed['fid'] + '.html', config.tmp_path)

    # gen mobi file
    mobi(path.join(config.tmp_path,'daily.opf'), config.kindlegen_path)

    #send_mail(user.kindle_mail, path.join(config.tmp_path, 'daily.mobi'))

    #clean 
    for fn in listdir(config.tmp_path):
        f_path = path.join(config.tmp_path, fn)
        if path.isfile( f_path):
            os.remove(f_path)

    user.push_timestamp = datetime.now()
    try:
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

    
    

        
def render_and_write(template_name, args, output_name, output_dir):
    template = tmp_env.get_template(template_name)
    f = open(path.join(output_dir, output_name), "w")
    f.write(template.render(**args).encode('utf8'))
    f.close()


def mobi(input_file, exec_path):
    system("%s %s" % (exec_path, input_file))

def del_img(eid):
    logging.info('task.del_image:entry id->%s ' %(str(eid)))
    db = m.Session()
    target_dir_path = path.join(config.img_storage_path, str(eid))
    if path.isdir(target_dir_path):
        rmtree(target_dir_path)
    db.close()

def reset_password(uid):
    db = m.Session()
    user = db.query(m.User).filter_by(id=uid).first() 
    if user is None:
        logging.warning('try reset password for uid->%s but user not found' %(str(uid)))
        return
    old_request = db.query(m.Password).filter_by(uid=uid).first()
    if old_request is not None:
        db.delete(old_request)

    token = md5_hexdigest()
    password = m.Password(token=token, uid=user.id)
    db.add(password)
    template = tmp_env.get_template('email/reset_password.txt')
    subject = 'reset password token'
    content = template.render(username=user.name, token = token).encode('utf8')
    to_addr = user.email
    try:
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()
    send_notice(subject, content, to_addr)





if __name__ == '__main__':
    sync_feed('guokr')
    #push(3)
