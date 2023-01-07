from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from django.http import HttpResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address
from utils.mixin import LoginRequiredMixin
from apps.order.models import OrderInfo, OrderGoods
from datetime import datetime


# Create your views here.
class OrderPlaceView(LoginRequiredMixin, View):
    """提交订单页面显示"""

    def post(self, request):
        # 获取登录的用户
        user = request.user
        # 获取参数 sku_ids
        sku_ids = request.POST.get('sku_ids')
        # 校验参数
        if not sku_ids:
            return redirect(reverse('cart:cart_info'))
        # 业务处理
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 根据商品的id获取商品的信息
        skus = []
        # 计算商品总数
        total_count = 0
        # 计算商品总价
        total_price = 0
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户所要购买的商品数量
            count = con.hget(cart_key, sku_id)
            # 计算商品小计
            amount = sku.price * int(count)
            # 动态增加属性
            sku.count = count
            sku.amount = amount
            skus.append(sku)
            total_count += int(count)
            total_price += amount

        # 运费
        transit_price = 10
        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收件地址
        address = Address.objects.filter(user=user)
        # 组织上下文
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'address': address,
        }
        # 使用模板
        return render(request, 'place_order.html', context)


class OrderCommitView(View):
    """订单提交"""

    def post(self, request):
        # 获取用户
        user = request.user
        # 判断用户是否登录
        if not user.is_authenticated():
            return HttpResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接收参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        # 校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return HttpResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return HttpResponse({'res': 2, 'errmsg': '支付方式非法'})
        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return HttpResponse({'res': 3, 'errmsg': '地址非法'})

            # 业务处理
        # 组织参数
        # 订单id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 10
        # 总件数和总金额
        total_count = 0
        total_price = 0
        # 向df_order_info表中添加一条记录
        order = OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            addr=addr,
            pay_method=pay_method,
            total_count=total_count,
            total_price=total_price,
            transit_price=transit_price
        )
        # 向df_order_goods中添加记录
        sku_ids = sku_ids.split(',')
        for sku_id in sku_ids:
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                # 商品不存在
                return HttpResponse({'res': 4, 'errmsg': '商品不存在'})

            # 从redis中获取要购买的商品数量
            con = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            count = con.hget(cart_key, sku_id)

            # 向df_order_goods中添加一条记录
            goods = OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=count,
                price=sku.price
            )
            # 更新库存和销量
            sku.stock -= int(count)
            sku.sales += int(count)
            sku.save()

            # 计算商品总数量和总价格
            amount = sku.price * int(count)
            total_count += int(count)
            total_price += amount

        # 更新订单信息表中的总数量和总价格
        order.total = total_count
        order.total_price = total_price
        order.save()

        # 清除购物车对应商品
        con.hdel(cart_key, *sku_ids)

        # 返回响应
        return HttpResponse({'res': 5, 'msg': '创建订单成功'})
