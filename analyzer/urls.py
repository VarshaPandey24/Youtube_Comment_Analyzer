from django.urls import path
from . import views
from .views import logout_view

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('analyze/', views.analyze, name='analyze'),
    path('download-pdf/', views.download_pdf, name='download_pdf'),
    path('logout/', logout_view, name='logout'),
]
