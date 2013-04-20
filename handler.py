#coding:utf-8
import tornado.web
import config as c
import model as m
import form as f

class BaseHandler(tornado.web.RequestHandler):
    """
    handler的基类
    """

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        return self.db.query(m.User).\
                filter_by(id=int(user_id)).first()

    @property
    def current_user(self):
        return self.get_current_user()

    def initialize(self):
        self.db = m.Session()

    def on_finish(self):
        m.Session.remove()
        self.db = None

    def db_commit(self):
        try:
            self.db.commit()
        except:
            self.db.rollback()
            raise

    def jrender_string(self, tmp_name, **kwargs):
        tmp = self.application.tmp_env.get_template(tmp_name)
        namespace = self.get_template_namespace()
        namespace.update(kwargs)
        return tmp.render(**namespace)

    def jrender(self, tmp_name, **kwargs):
        tmp = self.application.tmp_env.get_template(tmp_name)
        namespace = self.get_template_namespace()
        namespace.update(kwargs)
        self.finish(tmp.render(**namespace))

    def get_form(self, form_define, instance=None):
        """
        如果没有instance这个参数
        则通过get_argument 方法
        从handler.request.argument 获取

        如果有instance则从instance获取
        instance是一个模型实例

        如果想获取一个空form 直接生成一个Form实例
        """
        form = f.Form()
        if instance is not None:
            get=lambda field : getattr(instance, field, '')
        else:
            get=lambda field : self.get_argument(field, '')

        for field in form_define.keys():
            if field == '_form':
                continue
            form[field] = get(field)
        return form

    def validate(self, form, form_define):
        error_message = f.Form()
        error = False
        for field, validators in form_define.iteritems():
            if field == '_form' : continue
            if error : break 
            for validator in validators:
                error_message[field] = validator(self,form[field])
                error = bool(error_message[field])
                if error : break 

        if not error and '_form' in form_define:
            for validator in form_define['_form']:
                error_message['_form'] = validator(self, form)
                error = bool(error_message['_form'])
                if error :break
        return error, error_message

    def paging_clue(self,length,current_page):
        """
        分页策略
        length:总页数
        current_page:当前页码，0,1,2 ... length-1
        显示前两页和最后两页，
        显示current_page 和其之前的两页以及之后的两页
        如果两个页码之间间隔了一个或多个页码，
        则插入 -1以示省略
        """
        if current_page < 1 or current_page >= length:
            current_page  = 1
        if length <=1:
            return [1]
        page_set = set([2,1,current_page,length-1,length])
        if current_page-1 > 0:
            page_set.add(current_page-1)
        if current_page-2 > 0:
            page_set.add(current_page-2)
        if current_page +1 <= length:
            page_set.add(current_page+1)
        if current_page +2 <= length:
            page_set.add(current_page+2)
        page_set = list(page_set)
        page_set.sort()
        if current_page > 5:
            page_set.insert(2,-1)
        if length-current_page > 4:
            page_set.insert(-2,-1)
        return page_set

    def paging(self, query):
        # 条目总数
        count =  query.count()
        # 分页总数
        length = count // c.ipp
        if count % c.ipp:
            length += 1
        page = self.get_argument('page', 1)
        if page == 'last':
            page = length
        try:
            page = int(page)
        except: #TODO I should do something!
            page = 1
        if page > length:
            page = length
        if page <= 0:
            page = 1
        items = query.offset( (page-1)*c.ipp ).limit(c.ipp).all()
        page_clue = self.paging_clue(length, page)
        return page, page_clue, items

