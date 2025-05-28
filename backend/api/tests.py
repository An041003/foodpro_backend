from django.test import TestCase
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class RegisterView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        # tạm thời chưa hash password
        return Response({"msg": f"Registered {email}"}, status=status.HTTP_201_CREATED)

# Create your tests here.
