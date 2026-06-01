# from django.shortcuts import render
# from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User
from django.db import transaction
from gateway.serializers import *
from .utils import transport_file, check_file, health_check


# Create your views here.
class GatewayViewSet(viewsets.ViewSet):
    
    def get_permissions(self):
        if self.action in ["health"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='transport')
    def transport(self, request: Request, *args, **kwargs):

        file = request.FILES["file"].file
        if not check_file(file):
            return Response(data="Invalid file")
        file.seek(0)
        msg = transport_file(str(request.user.id), file)

        return Response(data=msg)
    
    @action(detail=False, methods=['get'], url_path='health')
    def health(self, request: Request, *args, **kwargs):
        module = request.query_params.get("module", "/health.php")

        if health_check(module):
            return Response(data="OK")
        return Response(data="ERR")

    


class UserViewSet(viewsets.ViewSet):
    
    def get_permissions(self):
        if self.action in ["create"]:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request: Request, *args, **kwargs):
        serializer = AuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request_data = serializer.data
        try:
            with transaction.atomic():
                user = User.objects.filter(
                    username = request_data["username"]
                ).first()
                if not user:
                    user = User.objects.create(
                        **request_data
                    )
                user.set_password(request_data["password"])
                user.save()
            return Response(data=request_data["username"])
        except Exception as e:
            return Response(data=str(e))
    
    

    @action(detail=False, methods=['post'], url_path='find')
    def find(self, request: Request, *args, **kwargs):
        try:
            offset = request.query_params.get("offset", "0")
            offset = int(offset)
        except:
            offset = 0

        users = User.objects.filter(**request.data)[offset:offset+10]
        serializer = UserSerializer(users, many=True)

        return Response(serializer.data)



    
