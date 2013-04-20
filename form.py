#coding:utf-8
import re
import model as m

class Form(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return ''

    def __setattr__(self, name, value):
        self[name] = value


def check_len(data, min_len=0, max_len=None,err_msg=None):
    if len(data) < min_len:
        return err_msg or u'最小长度' + str(min_len)
    if max_len is not None and len(data)> max_len:
        return err_msg or u'最大长度' + str(max_len)
    return ''


#-------------------注册表单:验证

EMAIL_PATTERN = re.compile(r'^([0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*@([0-9a-zA-Z][-\w]*[0-9a-zA-Z]\.)+[a-zA-Z]{2,9})$')

def register_form_check_email(handler, email):
    if not EMAIL_PATTERN.match(email):
        return u"邮箱格式不正确"
    elif len(email) >100:
        return u"呵呵，你邮箱有这么长?"
    elif handler.db.query(m.User).\
            filter_by(email=email).first():
        return u"邮箱已被注册"
    return ''

def register_form_check(h,form):
    if form.password_1 != form.password_2:
        return u'两次秘密输入不一致'
    return ''

#-------------------注册表单:field定义

register_form = dict( 
        email = [register_form_check_email],
        name = [lambda h,d:check_len(d,2,50)],
        password_1= [lambda h,d:check_len(d,1,50)],
        password_2= [],
        _form = [register_form_check]
        )
#-------------------注册表单:END

#-------------------更改密码表单:验证函数
#-------------------更改密码表单:field定义
change_password_form = dict(
        old_password = [] ,
        password_1= [lambda h,d:check_len(d,1,50)],
        password_2= [],
        _form = [register_form_check]
        )
#-------------------更改密码表单:END

#-------------------忘记密码表单:验证函数

#-------------------忘记密码表单:field定义
forget_password_form = dict(
        email = [lambda h,d:check_email_pattern(d)] ,
        _form = []
        )
#-------------------忘记密码表单:END


#-------------------重置密码表单:验证函数
def reset_password_form_check(handler, form):
    password_1 = form['password_1']
    password_2 = form['password_2']
    if password_1 != password_2:
        return u"两次密码输入不一致"
    return ''
#-------------------重置密码表单:field定义
reset_password_form = dict(
        email = [lambda h,d:check_email_pattern(d)] ,
        token = [lambda h,d:check_len(d, 16, 32)],
        password_1= [lambda h,d:check_len(d,1,50)],
        password_2= [],
        _form = [reset_password_form_check]
        )
#-------------------重置密码表单:END




#-------------------登录表单:验证函数
def check_email_pattern(email):
    if not EMAIL_PATTERN.match(email):
        return u'邮箱格式不正确'
    return ''

def  login_form_check(handler, form):
    email = form['email']
    password = form['password']
    user = handler.db.query(m.User).\
            filter_by(email=email).first()
    if not user or not user.auth(password):
        return u"登录验证失败"


#-------------------登录表单:field定义
login_form = dict(
        email = [lambda h,d:check_email_pattern(d)] ,
        password = [lambda h,d:check_len(d,1,50)],
        _form = [login_form_check]
        )
#-------------------登录表单:END

#-------------------add feed form:validators
def check_syncTime(_,data):
    try:
        data = int(data)
    except ValueError:
        return u'非法输入，请输入整数'
    return ''

SLUG_PATTERN = re.compile(r'[-_0-9a-zA-Z]{1,70}$')
def check_slug_pattern(_, data):
    if not SLUG_PATTERN.match(data):
        return u'字母数字横杠下划线,1-70个'
    return ''

#-------------------add feed form:define
add_feed_form = dict(
        frequency= [check_syncTime],
        name = [lambda h,d:check_len(d,1,50)],
        slug = [check_slug_pattern],
        #TODO url做re检查
        url = [lambda h,d:check_len(d,1)],
        )
#-------------------add feed form:End

#-------------------edit feed form:validators
#-------------------edit feed form:define
edit_feed_form = dict(
        frequency= [check_syncTime],
        name = [lambda h,d:check_len(d,1,50)],
        url = [lambda h,d:check_len(d,1)],
        )
#-------------------eidit feed form:End
