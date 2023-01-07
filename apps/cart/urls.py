from django.urls import path
from apps.cart.views import CartAddView
urlpatterns = [
    path('add/', CartAddView.as_view(), name='add'),

]
