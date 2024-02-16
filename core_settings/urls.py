from django.contrib import admin
from django.contrib.auth import views
from django.shortcuts import redirect
from django.urls import path, include
from motor_testing.forms import UserLoginForm

urlpatterns = [
    path('', lambda request: redirect('home/', permanent=True)),
    path('admin/', admin.site.urls),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.LoginView.as_view(authentication_form=UserLoginForm), name="login"),
    path("", include("motor_testing.urls")),
]
