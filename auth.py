#coding:utf-8

import logging
import functools
import tornado


def admin(method):
    """要求admin可以访问"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user or \
                not self.current_user.is_admin():
            logging.info('auth.admin:current_user->%s' %(str(self.current_user)))
            raise tornado.web.HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper
