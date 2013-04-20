#coding:utf-8

from datetime import datetime,timedelta
from time import mktime

import tornado.web

from rq import Connection, Queue
from redis import Redis

import model as m
import form as f
import config 
from handler import BaseHandler
import task
import auth

redis_conn = Redis()
queue = Queue('admin', connection=redis_conn)

class IndexHandler(BaseHandler):
    """
    后台管理首页
    """
    @auth.admin
    def get(self):
        args = dict()
        self.jrender('dev_backstage_index.html', **args)


class AddFeedHandler(BaseHandler):
    """
    添加一个 *feed* 
    """
    @auth.admin
    def get(self):
        form = self.get_form(f.login_form)
        args = dict(form=form, err_msg=f.Form())
        self.jrender('dev_backstage_add_feed.html', **args)

    @auth.admin
    def post(self):
        form = self.get_form(f.add_feed_form)
        error, err_msg = self.validate(form, f.add_feed_form)
        if error:
            args = dict(form=form, err_msg=err_msg)
            self.jrender('dev_backstage_add_feed.html',**args) 
        else:
            if not form.url.startswith(r'http://'):
                form.url = r'htpp://' + form.url
            feed = m.Feed(**form)
            self.db.add(feed)
            self.db_commit()
            self.redirect('/feed_list')

class EditFeedHandler(BaseHandler):
    """
    修改feed的 frequency name url 等属性
    """
    @auth.admin
    def get(self, slug):
        feed = self.db.query(m.Feed).filter_by(slug=slug).first()
        if feed is None :
            raise tornado.web.HTTPError(404)
        form = self.get_form(f.login_form, feed)
        args = { 'feed' : feed,
                'err_msg' : f.Form()
                }

        self.jrender('dev_backstage_edit_feed.html', **args)

    @auth.admin
    def post(self, slug):
        feed = self.db.query(m.Feed).filter_by(slug=slug).first()
        if feed is None :
            raise tornado.web.HTTPError(404)
        form = self.get_form(f.edit_feed_form)
        error, err_msg = self.validate(form, f.edit_feed_form)
        if error:
            args = dict(form=form,
                    err_msg=err_msg,
                    feed = feed,
                    )
            self.jrender('dev_backstage_edit_feed.html',**args) 
        else:
            if not form.url.startswith(r'http://'):
                form.url = r'htpp://' + form.url
            feed.update(**form)
            self.db_commit()
            self.redirect('/backstage/feed/'+feed.slug)

class FeedListHandler(BaseHandler):
    """
    TODO:
    这里将罗列Feed，提供一些高级搜索选项，一遍过滤得想要的Feed
    """
    @auth.admin
    def get(self):
        feeds = self.db.query(m.Feed).all()
        args = dict(feeds=feeds)
        self.jrender('dev_backstage_feed_list.html', **args)

class FeedIndexHandler(BaseHandler):
    @auth.admin
    def get(self,slug):
        feed = self.db.query(m.Feed).filter_by(slug=slug).first()
        if feed is None :
            raise tornado.web.HTTPError(404)
        args = dict(feed = feed)
        self.jrender('dev_backstage_feed_index.html', **args)


class ControlFeedHandler(BaseHandler):
    @auth.admin
    def get(self, slug, action):
        feed = self.db.query(m.Feed).filter_by(slug=slug).first()
        next_url = '/backstage/feed/' + feed.slug
        if feed is None: 
            raise tornado.web.HTTPError(404)
        if action.lower() == 'active':
            feed.active= True
        elif action.lower() == 'deactive':
            feed.active= False
        elif action.lower() == 'hide':
            feed.hidden = True
        elif action.lower() == 'show':
            feed.hidden = False
        elif action.lower() == 'img_on':
            feed.hidden = True
        elif action.lower() == 'img_off':
            feed.hidden = False
        self.db_commit()
        self.redirect(next_url)


class DeleteFeedHandler(BaseHandler):
    @auth.admin
    def get(self, slug):
        feed = self.db.query(m.Feed).filter_by(slug=slug).first()
        if feed is None: 
            raise tornado.web.HTTPError(404)
        for entry in feed.entries:
            queue.enqueue(task.del_img,entry.id)
        self.db.delete(feed)
        self.db_commit()
        next_url = self.get_argument('next_url', '/feed_list')
        self.redirect(next_url)


class FetchFeedHandler(BaseHandler):
    """
    即时更新一个 *feed*
    """
    @auth.admin
    @tornado.web.asynchronous
    def get(self,slug):
        queue.enqueue(task.sync_feed,slug)
        self.write('sync %s . task enquque.' %(slug))
        self.finish()


class EntryListHandler(BaseHandler):
    #TODO 接受一定参数，根据条件列出 *entry*
    @auth.admin
    def get(self):
        entries = self.db.query(m.Entry).\
                filter_by(hidden=True).all()
        args = dict(entries = entries)
        self.jrender('dev_backstage_entry_list.html', **args)


class DeleteEntryHandler(BaseHandler):
    """
    删除一个 *entry*
    """
    @auth.admin
    def get(self, eid):
        entry = self.db.query(m.Entry).filter_by(id=eid).first()
        if entry is None:
            raise tornado.web.HTTPError(404)
        eid = entry.id
        self.db.delete(entry)
        self.db_commit()
        queue.enqueue(task.del_img,eid)
        next_url = self.get_argument('next_url', '/backstage/entry')
        self.redirect(next_url)
    

class ControlEntryHandler(BaseHandler):
    """
    控制 entry 属性，目前属性有 *hidden* 
    """
    @auth.admin
    def get(self, eid, action):
        entry = self.db.query(m.Entry).filter_by(id=eid).first()
        if entry is None:
            raise tornado.web.HTTPError(404)
        if action.lower() == 'hide':
            entry.hidden = True
        elif action.lower() == 'show':
            entry.hidden = False 
        self.db_commit()
        next_url = self.get_argument('next_url', '/backstage/entry')
        self.redirect(next_url)

class DelEntryImageHandler(BaseHandler):
    """
    删除 entry 的图片以其图片文件夹
    """
    @auth.admin
    def get(self, eid):
        entry = self.db.query(m.Entry).filter_by(id=eid).first()
        if entry is None:
            raise tornado.web.HTTPError(404)
        queue.enqueue(task.del_img,eid)
        next_url = self.get_argument('next_url', '/backstage/entry')
        self.redirect(next_url)

class UserListHandler(BaseHandler):
    """
    列出特别用户
    """
    #TODO 根据条件列出用户
    @auth.admin
    def get(self):
        users = self.db.query(m.User).all()
        admin = [u for u in users if u.admin ]
        premium = [u for u in users if u.premium]
        deactive = [u for u in users if not u.active]
        expire = [u for u in users \
                if u.login_timestamp + \
                timedelta(days=config.expire_time) < \
                datetime.now()]
        #TODO 这要遍历一次代价可能挺高的
        #TODO 用sqlalchemy的方法获取对应的用户组
        args = locals()
        args.pop('self')
        self.jrender('dev_backstage_user_list.html', **args)


class DeleteUserHandler(BaseHandler):
    """
    注销一个用户
    """
    @auth.admin
    def get(self, uid):
        user = self.db.query(m.User).filter_by(id=uid).one()
        if user is None:
            raise tornado.web.HTTPError(404)
        self.db.delete(user)
        self.db_commit()
        #TODO 取消重定向
        self.redirect('/backstage/user')

class ControlUserHandler(BaseHandler):
    """
    设置用乎的 *active* 和 *premium* 状态
    """
    @auth.admin
    def get(self, uid):
        user = self.db.query(m.User).filter_by(id=uid).one()
        if user is None:
            raise tornado.web.HTTPError(404)
        premium = self.get_argument('premium', None)
        active = self.get_argument('active', None)
        if premium is not None:
            user.premium = premium== '1'
        if active is not None:
            user.active = active == '1'
        if premium is not None or active is not None:
            self.db_commit()
        #TODO 取消重定向
        self.redirect('/backstage/user')
        


