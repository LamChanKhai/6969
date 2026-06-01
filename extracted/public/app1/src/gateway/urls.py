from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
# from . import views

gateway_router = DefaultRouter()
gateway_router.register('', GatewayViewSet, basename='gateway')

user_router = DefaultRouter()
user_router.register('', UserViewSet, basename='user')

urlpatterns = [
    path('', include(gateway_router.urls)),
    path('user/',include(user_router.urls))
    # path('auth')
]
