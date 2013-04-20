#coding:utf-8
from datetime import datetime
import logging

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, relationship, backref


import config

from tool import md5_hexdigest


class ModelExtend(object):
    """
    model mixin.
    provide extra method.
    """
    def update(self, **kwargs):
        for attr, val in kwargs.items():
            if hasattr(self, attr):
                setattr(self, attr, val)


BaseModel = declarative_base()


#subscription_table = sa.Table('subscriptions', 
#        BaseModel.metadata,
#        sa.Column('uid', sa.Integer, 
#            sa.ForeignKey('users.id', ondelete='CASCADE' )),
#        sa.Column('fid', sa.Integer, 
#            sa.ForeignKey('feeds.id', ondelete='CASCADE' ))
#        )


class User(BaseModel, ModelExtend):
    """
    user model
    """
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    email = sa.Column(sa.String(100), nullable=False, unique=True, index=True)
    name = sa.Column(sa.String(100), nullable=False, index=True)
    kindle_mail = sa.Column(sa.String(100))
    register_time = sa.Column(sa.DateTime, default=datetime.now)
    login_timestamp = sa.Column(sa.DateTime, default=datetime.now)
    login_ip = sa.Column(sa.String(32))
    push_timestamp = sa.Column(sa.DateTime, default=datetime.now)
    push_timing = sa.Column(sa.SMALLINT, default=0)
    admin = sa.Column(sa.Boolean, default=False)
    active = sa.Column(sa.Boolean, default=False)
    premium = sa.Column(sa.Boolean, default=False)
    password = sa.Column(sa.String(32))
    salt = sa.Column(sa.String(32))
    
    reset_password = relationship('Password', backref=backref('user'),
            cascade="all, delete-orphan", passive_deletes=True, uselist=False)

    feeds = association_proxy('subscription_relation',
            'feed')

    def _set_salt(self):
        self.salt = md5_hexdigest()

    def set_password(self, raw_password):
        self._set_salt()
        self.password = md5_hexdigest(raw_password + self.salt)
        #logging.info("salt:%s\npassword:%s" \
        #        %(self.salt,self.password) )

    def auth(self, raw_password):
        password = md5_hexdigest(raw_password + self.salt)
        return password == self.password

    def is_admin(self):
        return self.admin


class Feed(BaseModel, ModelExtend):
    """
    feed source 
    """
    __tablename__ = 'feeds'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    sync_time = sa.Column(sa.DateTime, default=datetime.now)
    frequency = sa.Column(sa.Integer, nullable=False, default=7)
    name = sa.Column(sa.String(100),unique=True, nullable=False, index=True)
    slug = sa.Column(sa.String(100),unique=True, nullable=False, index=True)
    url = sa.Column(sa.String(200),unique=True, nullable=False)
    active = sa.Column(sa.Boolean, default=False)
    fetch_image = sa.Column(sa.Boolean, default=True)
    hidden = sa.Column(sa.Boolean, default=False)

    click = sa.Column(sa.Integer, nullable=False, default=0)
    subscribe = sa.Column(sa.Integer, nullable=False, default=0)
    download = sa.Column(sa.Integer, nullable=False, default=0)
    
    entries = relationship('Entry', backref=backref('feed'),
            cascade="all, delete-orphan", passive_deletes=True)


class Entry(BaseModel, ModelExtend):
    """
    feed entry
    """
    __tablename__ = 'entries'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    time_stamp = sa.Column(sa.DateTime)
    fetch_timestamp = sa.Column(sa.DateTime)
    title = sa.Column(sa.String(100))
    author = sa.Column(sa.String(100))
    source_link = sa.Column(sa.String(200), index=True)
    content = sa.Column(sa.Text, default='')
    hidden = sa.Column(sa.Boolean, default=False)
    got_img = sa.Column(sa.Boolean, default=False)
    

    like = sa.Column(sa.Integer, nullable=False, default=0)
    hate = sa.Column(sa.Integer, nullable=False, default=0)
    share = sa.Column(sa.Integer, nullable=False, default=0)

    fid = sa.Column(sa.Integer,
            sa.ForeignKey('feeds.id', ondelete='CASCADE'),
            nullable=False
            )

    images = relationship('Image', backref=backref('entry'),
            cascade="all, delete-orphan", passive_deletes=True)


class Subscription(BaseModel, ModelExtend):
    __tablename__ = 'subscriptions'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    uid = sa.Column(sa.Integer, 
            sa.ForeignKey('users.id', ondelete='CASCADE'), 
            primary_key=True)
    fid = sa.Column(sa.Integer, 
            sa.ForeignKey('feeds.id', ondelete='CASCADE'), 
            primary_key=True)
    active = sa.Column(sa.Boolean, default=True)
    user = relationship('User', backref=backref('subscription_relation', cascade='all, delete-orphan'))
    subscribe_timestamp = sa.Column(sa.DateTime, default=datetime.now)

    feed = relationship('Feed', backref=backref('subscriptions', cascade='all, delete-orphan'))


class Image(BaseModel, ModelExtend):
    __tablename__ = 'images'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    eid = sa.Column(sa.Integer,
            sa.ForeignKey('entries.id', ondelete='CASCADE'),
            nullable=False
            )
    serial_no = sa.Column(sa.Integer, nullable=False)
    file_name = sa.Column(sa.String(32), nullable=False)
    extend = sa.Column(sa.String(8), nullable=False)

class Password(BaseModel, ModelExtend):
    __tablename__ = 'passwords'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    token = sa.Column(sa.String(32), nullable=False)
    timestamp = sa.Column(sa.DateTime, default=datetime.now)
    uid = sa.Column(sa.Integer, 
            sa.ForeignKey('users.id', ondelete='CASCADE'))


engine = create_engine(config.db_engine_config,
        **config.db_engine_opt)

Session = scoped_session(sessionmaker(bind=engine))

def initDb(force=False):
    metadata = BaseModel.metadata
    if force:
        metadata.drop_all(engine)
    metadata.create_all(engine)


if __name__ == '__main__':
    """
    如果运行这个脚本，数据库将可能被初始化
    """
    if setting.debug:
        force = raw_input(u'输入`yes` 将删除旧表')
        if force.lower() == 'yes':
            initDb(force=True)
        else:
            print(u'什么都没做')
    else:
        initDb()


