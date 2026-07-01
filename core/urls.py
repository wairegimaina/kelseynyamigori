from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('contact/', views.contact_submit, name='contact_submit'),
    path('admin/login/', views.AdminLoginView.as_view(), name='admin_login'),
]
