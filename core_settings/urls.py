"""
URL configuration for induction-motor-testing project.

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
from django.contrib.auth import views
from django.urls import path
from django.views.generic import TemplateView
from motor_testing.views import InductionMotorListingsView
from motor_testing.forms import UserLoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("login/", views.LoginView.as_view(authentication_form=UserLoginForm), name="login"),
    path("home/", TemplateView.as_view(template_name="home.html"), name="home"),
    path("listings/", InductionMotorListingsView.as_view(), name="listings"),
]
