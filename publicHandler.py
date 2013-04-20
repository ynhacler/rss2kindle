#coding:utf-8

from datetime import datetime,timedelta
from time import mktime
import re
import logging

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
queue = Queue('cron', connection=redis_conn)

class subscribeHandler(BaseHandler):
    """
    提供订阅/取消订阅一个 *feed* 的功能
    """
    @tornado.web.authenticated
    def get(self, slug, action):
        feed = self.db.query(m.Feed).filter_by(slug = slug).first()
        subscription = self.db.query(m.Subscription).\
                filter_by(uid=self.current_user.id,fid=feed.id).first()
        if feed is None:
            raise tornado.web.HTTPError(404)
        if action.lower() == 'unsubscribe' and \
                subscription is not None:
            self.db.delete(subscription) 
            self.db_commit()
        elif action.lower() == 'subscribe' and \
                subscription is None:
            subscription = m.Subscription(uid=self.current_user.id, fid=feed.id)
            self.db.add(subscription)
            self.db_commit()
        else:
            raise tornado.web.HTTPError(404)
        self.redirect(self.get_argument('next', '/feed/'+feed.slug))

class subscriptionControlHandler(BaseHandler):
    """
    将订阅 deactive 以暂停推送
    或者 active 以回复
    吐嘈 类名太长
    """
    @tornado.web.authenticated
    def get(self, action):
        if action.lower() == 'active':
            active = True
        elif action.lower() =='deactive':
            active = False
        else:
            raise tornado.web.HTTPError(404)
        sid_set = self.get_arguments('sid')
        sub_set = []
        for sid in sid_set :
            sub_set.append( self.db.query(m.Subscription).\
                    filter_by(id=sid, uid=self.current_user.id).first())
            if sub_set[-1] is None:
                logging.warning('illegal request.' 
                        'action->%s subscription_id->%s user_id_>%s'
                        %(action, str(sid), str(self.current_user.id)))
                raise tornado.web.HTTPError(400)
        map( lambda s:setattr(s,'active',active), sub_set )
        if action.lower() == 'active':
            map( lambda s:setattr(s,'subscribe_timestamp',datetime.now()), sub_set)

        self.db_commit()
        self.redirect('/account')


class AccountHandler(BaseHandler):
    """
    显示用户基本信息 以及订阅列表
    """
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user()
        args = locals()
        args.pop('self')
        self.jrender('dev_account.html', **args)

    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user()
        try:
            push_timing = int(self.get_argument('push_timing', -1))
            if push_timing in range(12):
                if user.push_timing != push_timing:
                    logging.info('user change push_timing. uid->%s' %(str(user.id)))
                user.push_timing = push_timing
        except ValueError:
            logging.warning('illegal push_timing value`%s`. uid->%s ' \
                    %(self.get_argument('push_timing', ''), str(user.id)))

        mail = self.get_argument('push_mail', '')
        if EMAIL_PATTERN.match(mail):
            user.kindle_mail = mail

        self.db_commit()
        self.redirect('/account')

class ForgetPasswordHandler(BaseHandler):
    """
    处理找回密码申请
    """
    def get(self):
        self.jrender('dev_forget_password.html')

    def post(self):
        email = self.get_argument('email', 'no argument')
        if EMAIL_PATTERN.match(email):
            user = self.db.query(m.User).filter_by(email=email).first()
            if user is None:
                logging.warning('user try reset password but email (%s)not exist' %(email))
                #TODO should reply meaningful message
            else:
                queue.enqueue(task.reset_password,user.id)
                self.redirect('/reset_password')

        

class RestPasswordHandler(BaseHandler):
    """
    找回密码
    """
    def get(self):
        form = self.get_form(f.change_password_form)
        args = dict(
                form = form,
                err_msg = f.Form()
                )
        self.jrender('dev_reset_password.html', **args)

    def post(self):
        form = self.get_form(f.reset_password_form)
        error, err_msg = self.validate(form, f.change_password_form)
        if not error:
            user = self.db.query(m.User).filter_by(email = form['email']).first()
            if user is not None:
                reset_requset = self.db.query(m.Password).\
                        filter_by(uid=user.id, token=form['token']).first()

                expire = datetime.now() > reset_requset.timestamp + timedelta(hours=24)
        
        if user and reset_requset and not expire: 
            self.db.delete(reset_requset)
            user.set_password(form['password_1'])
            self.db_commit()
            self.redirect('/login')
        else:
            error, err_msg._form = True, u'有效性验证失败'
            args = dict(
                    form = form,
                    err_msg = err_msg
                    )
            self.jrender('dev_reset_password.html', **args)



class ChangePasswordHandler(BaseHandler):
    """
    更改密码
    """
    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user()
        form = self.get_form(f.change_password_form)
        args = dict(
                user = user,
                form = form,
                err_msg = f.Form()
                )
        self.jrender('dev_change_password.html', **args)

    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user()
        form = self.get_form(f.change_password_form)
        error, err_msg = self.validate(form, f.change_password_form)
        if not error : 
            error = error or not user.auth(form.old_password)
            err_msg.old_password = u'原始密码错误'
        if not error :
            user.set_password(form.password_1)
            self.db_commit()
            self.redirect('/account')
        else:
            args = dict(
                    user = user,
                    form = form,
                    err_msg = err_msg
                    )
            self.jrender('dev_change_password.html', **args)

EMAIL_PATTERN = re.compile(r'^([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@([0-9a-zA-Z][-\w]*[0-9a-zA-Z]\.)+[a-zA-Z]{2,9})$')

class ChangePushMaildHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        user = self.get_current_user()
        mail = self.get_argument('push_mail', '')
        if EMAIL_PATTERN.match(mail):
            user.kindle_mail = mail
            self.db_commit()
        self.redirect('/account')
            

