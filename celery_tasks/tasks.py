import os

from django.conf import settings
# 使用celery
from celery import Celery
from django.core.mail import send_mail
from django.template import loader
from apps.goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner

# django初始化
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
django.setup()


# 创建一个Celery类的实例对象
app = Celery('celery_tasks.tasks', broker='redis://192.168.5.157:6379/0')


# 定义任务函数
@app.task
def send_register_activate_email(to_email, username, token):
    # 发送激活邮件
    subject = '天天生鲜激活邮件'
    message = ''
    from_email = settings.FROM_EMAIL
    recipient_list = [to_email]
    html_message = '<h1>%s, 欢迎您注册成为天天生鲜会员</h1>清点击下面链接激活您的账户<br/><a ' \
                   'href="http:127.0.0.1:8000/active/%s">http:127.0.0.1:8000/active/%s</a> ' % {username, token,
                                                                                                token}
    send_mail(
        subject,
        message,
        from_email,
        recipient_list
    )


@app.task
def generate_static_index_html():
    """产生首页静态化页面"""

    # 获取商品的种类信息
    types = GoodsType.objects.all()

    # 获取轮播图信息
    banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取促销信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        type.image_banners = image_banners
        type.title_banners = title_banners

    context = {
        'types': types,
        'goods_banners': banners,
        'promotion_banners': promotion_banners,
    }

    # 产生静态界面
    temp = loader.get_template('static_index.html')
    static_index_html = temp.render(context)

    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')

    with open(save_path, 'w') as f:
        f.write(static_index_html)

