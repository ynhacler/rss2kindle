#coding:utf-8
import os
import logging
from tornado import escape
#debug = False
debug = True
log_lev = logging.INFO

#sqlalchemy 设置
db_engine_config = "postgresql+psycopg2://supei@localhost:5432/rss_dev"

db_engine_opt =dict(
        encoding='utf-8',
        echo=False)

#email 设置
email_domain = '@foo.bar'
admin_email = 'your_admin' + email_domain
notice_email = 'noreply' + email_domain


#app 路径设置
app_root = os.path.dirname(__file__)
static_path = os.path.join(app_root, "static")
template_path = os.path.join(app_root, 'template')

#tornado app 初始化参数
app_args = dict(
    template_path=template_path,
    static_path=static_path,
    debug=debug,
    xsrf_cookies=True,
    cookie_secret="dev",
    #autoescape="xhtml_escape",
    autoescape=None,
    login_url="/login",
)

#分页，每页项目个数
ipp = 10

#不登录X天取消投递
expire_time = 7

#临时目录，制作mobi是存放mobi文件以及其源文件
tmp_path= os.path.join(app_root, 'tmp')

#存放图片的目录名
img_storage_dir = 'image'
#完整图片存储目录
img_storage_path = os.path.join(tmp_path, img_storage_dir)
#限制每篇条目图片超过限定大小，则不再添加图片
img_size_per_entry = 1024*1024 #1M
#限制每次推送目图片超过限定大小，则不再添加图片
img_size_per_push = 2*1024*1024 #2M
#制作mobi的可执行文件, 绝对路径
kindlegen_path = '/home/supei/documents/python/dev/kindle/kindlegen/kindlegen'
