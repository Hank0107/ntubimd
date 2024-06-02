"""
URL configuration for web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from data import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.introduce, name='introduce'),
    path('stock_list', views.stock_list, name='stock_list'),
    path('stock_detail/<str:stock_code>/realtime_data', views.stock_detail, name='stock_detail'),
    path('stock_detail/<str:stock_code>/technical_analysis', views.technical_analysis, name='technical_analysis'),
    path('stock_detail/<str:stock_code>/stock_dividend', views.stock_dividend, name='stock_dividend'),
    path('stock_detail/<str:stock_code>/stock_holder', views.stock_holder, name='stock_holder'),
    path('stock_detail/<str:stock_code>/stock_juridicalperson', views.juridical_data, name='juridical_data'),
    path('stock_search/', views.stock_search, name='stock_search'),
    path('empty_page/', views.empty_page, name='empty_page'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/proxy_get_stock_info/<str:stock_code>/', views.proxy_get_stock_info, name='proxy_get_stock_info'),
]