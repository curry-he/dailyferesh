from django.conf import settings
# 使用celery
from celery import Celery

# 创建一个Celery类的实例对象
celery = Celery('celery_tasks.tasks', broker='redis://192.168.5.157:6379/8')


# 定义任务函数
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
