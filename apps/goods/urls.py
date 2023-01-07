from django.urls import path
from apps.goods.views import IndexView

urlpatterns = [
    path(r'^$', IndexView.as_view(), name='index')  # index
]