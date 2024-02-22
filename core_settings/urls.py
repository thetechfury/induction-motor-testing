from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.shortcuts import redirect
from django.urls import path, include
from wkhtmltopdf.views import PDFTemplateView
from core_settings import settings
from motor_testing.forms import UserLoginForm

urlpatterns = [
    path('', lambda request: redirect('home/', permanent=True)),
    path('admin/', admin.site.urls),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.LoginView.as_view(authentication_form=UserLoginForm), name="login"),
    path("", include("motor_testing.urls")),
    path("pdf/", PDFTemplateView.as_view(template_name="index.html", filename="index.pdf"), name="pdf"),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)