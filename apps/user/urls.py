from django.urls import path
from django.contrib.auth.decorators import login_required
from apps.user import views
from apps.user.views import RegisterView, ActiveView, LoginView, LogOutView, UserInfoView, UserOrderView, AddressView
app_name = 'user'
urlpatterns = [
    # path('register/', views.register),  # /register
    # path('register_handler/', views.register_handler),  # /register_handler
    path('register/', RegisterView.as_view(), name='register'),
    path('active<str:token>/', ActiveView.as_view(), name='active'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogOutView.as_view(), name='logout'),
    # path('info/', login_required(UserInfoView.as_view), name='info'),
    # path('order/', login_required(UserOrderView.as_view()), name='order'),
    # path('address/', login_required(AddressView.as_view()), name='address'),
    path('info/', UserInfoView.as_view, name='info'),
    path('order/', UserOrderView.as_view(), name='order'),
    path('address/', AddressView.as_view(), name='address'),
]
