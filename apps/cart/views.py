from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection


# Create your views here.

class CartAddView(View):
    """"购物车记录添加"""

    def post(self, request):
        user = request.user
        # 判断是否登录
        if not user.is_authenticated():
            return HttpResponse({'res': 0, 'errmsg': '请先登录'})
        # 购物车记录添加
        # 接收数据
        sku_id = request.Post.get('sku_id')
        count = request.Post.get('count')
        # 数据校验
        if not all([sku_id, count]):
            return HttpResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验添加商品的数量
        try:
            count = int(count)
        except Exception as e:
            # 数目出错
            return HttpResponse({'res': 2, 'errmsg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except Exception.DosesNotExist as e:
            # 商品不存在
            return HttpResponse({'res': 3, 'errmsg': '商品不存在'})
            # 业务处理：添加购物车记录
            con = get_redis_connection('default')
            cart_key = 'cart%d' % user.id
            cart_count = con.hget(cart_key, sku_id)
            if cart_count:
                # 累加购物车中商品的数目
                count += int(cart_count)
                # 校验库存
                if count > sku.stock:
                    return HttpResponse({'res': 4, 'errmsg': '商品库存不足'})
                # 更新hash中sku_id的值
                con.hset(cart_key, sku_id, count)

                # 返回应答
        return HttpResponse({'res': 4, 'message': '添加购物车成功'})
