##运行环境
在python2.7.3下开发以及测试

##依赖
1. tornado
2. sqlalchemy 
3. python-rq
4. feedparser
5. psyconpg2
6. jinja2
7. redis

更多文档正在努力整理 :(

----

##非原创文件声明
tmp/style/KUG.css
template/mobi/feed.html
template/mobi/opf.xml
template/mobi/toc.html
template/mobi/toc.xml

来自 https://github.com/pelletier/dailykindle

##授权
BSD

##文件一览

    ├── auth.py
    ├── backstageHandler.py
    ├── config.py
    ├── cron.py
    ├── form.py
    ├── handler.py
    ├── model.py
    ├── publicHandler.py
    ├── README
    ├── sendMail.py
    ├── static
    │   ├── favicon.ico
    │   └── js
    │       ├── ajax.js
    │       └── jquery-1.9.1.min.js
    ├── task.py
    ├── template
    │   ├── dev_account.html
    │   ├── dev_backstage_add_feed.html
    │   ├── dev_backstage_edit_feed.html
    │   ├── dev_backstage_entry_list.html
    │   ├── dev_backstage_feed_index.html
    │   ├── dev_backstage_feed_list.html
    │   ├── dev_backstage_index.html
    │   ├── dev_backstage_user_list.html
    │   ├── dev_base.html
    │   ├── dev_change_password.html
    │   ├── dev_entry.html
    │   ├── dev_feed_index.html
    │   ├── dev_feed_list.html
    │   ├── dev_forget_password.html
    │   ├── dev_index.html
    │   ├── dev_login.html
    │   ├── dev_register.html
    │   ├── dev_reset_password.html
    │   ├── email
    │   │   └── reset_password.txt
    │   ├── mobi
    │   │   ├── feed.html
    │   │   ├── opf.xml
    │   │   ├── toc.html
    │   │   └── toc.xml
    │   └── module
    │       ├── entry_content.html
    │       └── paging.html
    ├── tmp
    │   ├── image
    │   └── style
    │       └── KUG.css
    ├── tool.py
    └── web.py

