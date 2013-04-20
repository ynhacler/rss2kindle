#coding:utf-8
from datetime import datetime
import logging
import json

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options
from tornado.options import define, options

from jinja2 import Environment, FileSystemLoader 

import model as m
import form as f
import config 
import auth

from handler import BaseHandler
import backstageHandler as backstage
import publicHandler as public


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                ('/',
                    IndexHandler),
                ('/register',
                    RegisterHandler),
                ('/login',
                    LoginHandler),
                ('/logout', 
                    LogoutHandler),
                ('/account',
                    public.AccountHandler),
                ('/change_password',
                    public.ChangePasswordHandler),
                ('/change_push_mail',
                    public.ChangePushMaildHandler),
                ('/forget_password',
                    public.ForgetPasswordHandler),
                ('/reset_password',
                    public.RestPasswordHandler),
                ('/feed_list',
                    FeedListHandler),
                ('/feed/([-_a-zA-Z0-9]+)',
                    FeedIndex),
                ('/feed/([-_a-zA-Z0-9]+)/(unsubscribe|subscribe)',
                    public.subscribeHandler),
                ('/feed/subscription/(active|deactive)',
                    public.subscriptionControlHandler),
                ('/entry/(\d+)',
                    EntryIndex),
                ('/backstage',
                    backstage.IndexHandler),
                ('/backstage/feed',
                    backstage.FeedListHandler),
                ('/backstage/add_feed',
                    backstage.AddFeedHandler),
                ('/backstage/feed/([-_a-zA-Z0-9]+)/edit', 
                    backstage.EditFeedHandler),
                ('/backstage/feed/([-_a-zA-Z0-9]+)', 
                    backstage.FeedIndexHandler),
                ('/backstage/feed/([-_a-zA-Z0-9]+)/(active|deactive|show|hidden|img_on|img_off)',
                    backstage.ControlFeedHandler),
                ('/backstage/feed/([-_a-zA-Z0-9]+)/fetch', 
                    backstage.FetchFeedHandler),
                ('/backstage/feed/([-_a-zA-Z0-9]+)/delete', 
                    backstage.DeleteFeedHandler),
                ('/backstage/entry', 
                    backstage.EntryListHandler),
                ('/backstage/entry/(\d+)/delete', 
                    backstage.DeleteEntryHandler),
                ('/backstage/entry/(\d+)/del_img', 
                    backstage.DelEntryImageHandler),
                ('/backstage/entry/(\d+)/(hide|show)', 
                    backstage.ControlEntryHandler),
                ('/backstage/user', 
                    backstage.UserListHandler),
                ('/backstage/user/(\d+)/delete', 
                    backstage.DeleteUserHandler),
                ('/backstage/user/(\d+)', 
                    backstage.ControlUserHandler),
                ]
        app_args = config.app_args
        tornado.web.Application.__init__(self, handlers, 
                **app_args)
        self.tmp_env = Environment(loader=\
                FileSystemLoader(config.template_path))


class IndexHandler(BaseHandler):
    def get(self):
        if self.current_user:
            name = self.current_user.name
        else:
            name = u'游客'
        args = dict(name=name)
        self.jrender('dev_index.html', **args)
       

class RegisterHandler(BaseHandler):
    def get(self):
        form = self.get_form(f.register_form)
        args = dict(form=form, err_msg=f.Form())
        self.jrender('dev_register.html',**args) 

    def post(self):
        form = self.get_form(f.register_form)
        error, err_msg = self.validate(form, f.register_form)
        if error:
            args = dict(form=form, err_msg=err_msg)
            self.jrender('dev_register.html',**args) 
        else:
            password= form.pop('password_1')
            form.pop('password_2')
            user = m.User(**form)
            user.set_password(password)
            self.db.add(user)
            self.db_commit()
            self.redirect('/login')


class LoginHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        form = self.get_form(f.login_form)
        args = dict(form=form, err_msg=f.Form())
        self.jrender('dev_login.html', **args)

    def post(self):
        self.clear_cookie("user")
        form = self.get_form(f.login_form)
        error, err_msg = self.validate(form, f.login_form)
        if error:
            args = dict(form=form, err_msg=err_msg)
            self.jrender('dev_login.html',**args) 
        else:
            user = self.db.query(m.User).\
                    filter_by(email=form.email).one()
            user.login_timestamp = datetime.now()
            self.db_commit()
            self.set_secure_cookie("user", str(user.id), 
                    expires_days=7)
            self.redirect('/')


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))




class FeedListHandler(BaseHandler):
    def get(self):
        feeds = self.db.query(m.Feed).\
                filter_by(hidden=False).all()

        page, page_clue, feeds = self.paging(feeds)
        user = self.get_current_user()
        base_url = self.request.path
        args = locals()
        args.pop('self')
        self.jrender('dev_feed_list.html', **args)


class FeedIndex(BaseHandler):
    def get(self,slug):
        feed = self.db.query(m.Feed).\
                filter_by(slug=slug, hidden=False).first()
        if feed is None :
            raise tornado.web.HTTPError(404)
        entries = self.db.query(m.Entry).\
                filter_by(fid=feed.id, hidden=False).\
                order_by(m.Entry.fetch_timestamp.desc()).all()
        page, page_clue, entries = self.paging(entries)
        user = self.get_current_user()
        args = locals()
        args.pop('self')
        self.jrender('dev_feed_index.html', **args)


class EntryIndex(BaseHandler):
    def get(self, eid):
        entry = self.db.query(m.Entry).\
                filter_by(id=eid, hidden=False).first()
        if entry is None:
            raise tornado.web.HTTPError(404)
        user = self.get_current_user()
        args = {'entry' : entry,
                'user' : user
                }
        self.jrender('dev_entry.html', **args)

    def post(self, eid):
        entry = self.db.query(m.Entry).\
                filter_by(id=eid, hidden=False).first()
        self.set_header("Content-Type", "application/json")
        if entry is None:
            response = ''
        else:
            response =  self.jrender_string('module/entry_content.html', **dict(entry = entry))
        self.write(json.dumps(response))
        

define("port", default=8888, 
        help="run on the given port", type=int)

def main():
    if config.debug:
        m.initDb()
    tornado.options.parse_command_line()
    application = Application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level = config.log_lev)
    main()
