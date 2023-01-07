from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin


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
        # 计算购物车中商品总数
        total_count = con.hlen(cart_key)
        # 返回应答
        return HttpResponse({'res': 5, 'total_count': total_count, 'message': '添加购物车成功'})


class CartInfoView(LoginRequiredMixin, View):
    """显示购物车页面"""
    def get(self, request):
        # 获取登录的用户
        user = request.user
        # 获取购物车中商品信息
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_dict = con.hgetall(cart_key) # {'商品id':'商品数量'}
        skus = []
        # 保存总件数和总价格
        total_count = 0
        total_price = 0
        for sku_id, count in cart_dict.items():
            # 根据商品id获取商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 计算商品小计
            amount = sku.price * int(count)
            # 动态增加属性，保存小计
            sku.amount = amount
            # 动态增加属性，保存商品数量
            sku.count = count
            skus.append(sku)
            # 计算总件数和总价格
            total_count += int(count)
            total_price += amount
        # 组织上下文
        context = {
            'total_price': total_price,
            'total_count': total_count,
            'skus': skus,
        }
        # 使用模板
        return render(request, 'cart.html', context)


class CartUpdateView(View):
    """购物车记录更新"""
    def post(self, request):
        user = request.user
        if not user.is_authenticated():
            return HttpResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 数据校验
        if not all([sku_id, count]):
            return HttpResponse({'res': 1, 'error': '数据不完整'})
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
        # 业务处理：更新购物车记录
        con = get_redis_connection('default')
        cart_key = 'cart%d' % user.id
        cart_count = con.hget(cart_key, sku_id)
        # 校验库存
        if count > sku.stock:
            return HttpResponse({'res': 4, 'errmsg': '商品库存不足'})
        # 更新hash中sku_id的值
        con.hset(cart_key, sku_id, count)
        # 计算购物车中商品总件数
        total_count = 0
        vals = con.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return HttpResponse({'res': 5, 'total_count': total_count, 'message': '更新购物车成功'})


class CartDeleteView(View):
    """删除购物车数据"""
    def get(self, request):
        # 获取用户
        user = request.user
        # 判断用户是否登录
        if not user.is_authenticated:
            return HttpResponse({'res': 0, 'errmsg': '请先登录'})
        # 接收数据
        sku_id = request.GET.get('sku_id')
        # 校验数据
        if not sku_id:
            return HttpResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except Exception.DosesNotExist as e:
            # 商品不存在
            return HttpResponse({'res': 2, 'errmsg': '商品不存在'})
        # 业务处理
        con = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 删除hash表中的数据
        con.hdel('cart_key', sku_id)

        # 返回应答
        return HttpResponse({'res': 3, 'msg': '购物车删除商品成功'})


