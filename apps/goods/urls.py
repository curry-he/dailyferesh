from django.urls import path, re_path

from apps.goods import views

urlpatterns = [
    re_path(r'^$', views.index, name='index')  # index
]
