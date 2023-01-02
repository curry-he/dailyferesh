import re
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous import SignatureExpired
from dailyfresh import settings
from django.core.mail import send_mail
from apps.user.models import User, Address
from celery_tasks.tasks import send_register_activate_email
from django.contrib.auth import authenticate, login, logout
from utils.mixin import LoginRequiredMixin
from apps.goods.models import GoodsSKU


# Create your views here.
# /user/register
def register(request):
    if request.method == 'GET':
        """"显示注册页面"""
        return render(request, 'register.html')
    else:
        """进行注册处理"""
        # 接收数据
        # 用户名
        username = request.POST.get('user_name')
        # 密码
        password = request.POST.get('pwd')
        # 确认密码
        re_password = request.POST.get('cpwd')
        # 邮箱
        email = request.POST.get('email')
        # 同意协议
        allow = request.POST.get('allow')
        # 数据校验
        if not all({username, password, re_password, email}):
            # 判断传入数据是否完整
            return render('request', 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render('request', 'register.html', {'errmsg': '邮箱格式错误'})
        # 校验两次输入的密码是否一致
        if password != re_password:
            return render('request', 'register.html', {'errmsg': '两次输入的密码不一致'})
        # 判断是否同意协议
        if allow != 'on':
            return render('request', 'register.html', {'errmsg': '清勾选同意用户协议'})
        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render('request', 'register.html', {'errmsg': '此用户名已存在'})
        # 业务处理
        # 创建用户
        user = User.objects.create_user(username, password, email)
        user.is_active = 0
        user.save()
        # 返回应答
        # 注册完成后，跳转到首页
        # return
        return HttpResponse('ok')


# /user/register_handler
def register_handler(request):
    """进行注册处理"""
    # 接收数据
    # 用户名
    username = request.POST.get('user_name')
    # 密码
    password = request.POST.get('pwd')
    # 确认密码
    re_password = request.POST.get('cpwd')
    # 邮箱
    email = request.POST.get('email')
    # 同意协议
    allow = request.POST.get('allow')
    # 数据校验
    if not all({username, password, re_password, email}):
        # 判断传入数据是否完整
        return render('request', 'register.html', {'errmsg': '数据不完整'})
    # 校验邮箱
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render('request', 'register.html', {'errmsg': '邮箱格式错误'})
    # 校验两次输入的密码是否一致
    if password != re_password:
        return render('request', 'register.html', {'errmsg': '两次输入的密码不一致'})
    # 判断是否同意协议
    if allow != 'on':
        return render('request', 'register.html', {'errmsg': '清勾选同意用户协议'})
    # 校验用户名是否重复
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # 用户名不存在
        user = None

    if user:
        # 用户名已存在
        return render('request', 'register.html', {'errmsg': '此用户名已存在'})
    # 业务处理
    # 创建用户
    user = User.objects.create_user(username, password, email)
    user.is_active = 0
    user.save()
    # 返回应答
    # 注册完成后，跳转到首页
    return redirect(reverse('goods:index'))


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """进行注册处理"""
        # 接收数据
        # 用户名
        username = request.POST.get('user_name')
        # 密码
        password = request.POST.get('pwd')
        # 确认密码
        re_password = request.POST.get('cpwd')
        # 邮箱
        email = request.POST.get('email')
        # 同意协议
        allow = request.POST.get('allow')
        # 数据校验
        if not all({username, password, re_password, email}):
            # 判断传入数据是否完整
            return render('request', 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render('request', 'register.html', {'errmsg': '邮箱格式错误'})
        # 校验两次输入的密码是否一致
        if password != re_password:
            return render('request', 'register.html', {'errmsg': '两次输入的密码不一致'})
        # 判断是否同意协议
        if allow != 'on':
            return render('request', 'register.html', {'errmsg': '清勾选同意用户协议'})
        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render('request', 'register.html', {'errmsg': '此用户名已存在'})
        # 业务处理
        # 创建用户
        user = User.objects.create_user(username, password, email)
        user.is_active = 0
        user.save()
        # 发送激活邮件包含激活链接
        # 激活链接中需要i包含用户的身份信息，并对身份信息进行加密
        # 加密用户身份信息，生成激活token
        serializer = Serializer('settings.SECRET_KEY', 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()
        # 发邮件
        # subject = '天天生鲜激活邮件'
        # message = ''
        # from_email = settings.FROM_EMAIL
        # recipient_list = [email]
        # html_message = '<h1>%s, 欢迎您注册成为天天生鲜会员</h1>清点击下面链接激活您的账户<br/><a ' \
        #                'href="http:127.0.0.1:8000/active/%s">http:127.0.0.1:8000/active/%s</a> ' % {username, token,
        #                                                                                             token}
        # send_mail(
        #     subject,
        #     message,
        #     from_email,
        #     recipient_list
        # )
        # celery异步发送邮件
        send_register_activate_email.delay(email, username, token)
        # 返回应答
        # 注册完成后，跳转到首页
        # return redirect(reverse('goods:index'))
        return HttpResponse('注册成功')


class ActiveView(View):
    """用户激活"""

    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            # 解析token
            info = serializer.load(token)
            # 获取待激活用户id
            user_id = info['confirm']
            # 获取带激活用户对象
            user = User.objects.get(id=user_id)
            # 激活用户
            user.is_active = 1
            user.save()
            # 跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


class LoginView(View):
    def get(self, request):
        """显示登录页面"""
        # 判断是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录校验"""
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 业务处理
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户登录状态
                login(request, user)
                # 获取登录后所要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))
                # 跳转到next_url
                response = redirect(next_url)
                # 判断是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 需要记住用户名
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')
                # 返回response
                return response

            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


# /user/logout
class LogOutView(View):
    """退出登录"""

    def get(self, request):
        """退出登录页面"""
        logout(request)
        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user/info
class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        """用户信息显示"""
        return render(request, 'user_center_info.html')
        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # redis = StrictRedis(host='127.0.0.1', port=6379, db=9)
        from django_redis import get_redis_connection
        con = get_redis_connection('default')
        history_key = 'history%d' % user.id
        # 获取用户最新浏览的5条数据
        sku_ids = con.lrange(history_key, 0, 4)
        # 从数据库中查询最近浏览的商品详情信息
        # goods_li = GoodsSKU.objects.filter(id__in=sku_ids)
        # goods_res = []
        # for id in sku_ids:
        #     for goods in goods_li:
        #         if goods.id == id:
        #             goods_res.append(goods)
        #
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)
        # 组织上下文
        context = {
            'page': 'user',
            'address': address,
            'goods_li': goods_li
        }
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequiredMixin, View):
    def get(self, request):
        """订单显示"""
        # 获取用户的订单信息

        return render(request, 'user_center_order.html')


# /user/address
class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        """地址显示"""
        # 获取登录用户
        user = request.user
        # # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page': address, 'address': address})

    def post(self, request):
        """添加收货地址"""
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机号格式不正确'})

        # 业务处理
        # 如果已存在默认收货地址，就不设置为默认收货地址，否则就设置为默认收货地址
        # 获取登录用户
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address = None
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True
        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               address=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答
        return redirect(reverse('user:address'))
