"""
URL configuration for gymnow_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from gym.serializers import GymTokenObtainPairSerializer


class GymTokenObtainPairView(TokenObtainPairView):
    serializer_class = GymTokenObtainPairSerializer
    permission_classes = (AllowAny,)


class GymTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)

schema_view = get_schema_view(
   openapi.Info(
      title="GymNow API",
      default_version='v1',
      description=(
         "API para gestión de gimnasio con clientes, ejercicios, rutinas y seguimiento de progreso. "
         "RBAC: owner administra todo; trainer gestiona operación sin borrar clientes ni ver credenciales; "
         "client/guest solo acceden a sus propios datos. Cada operación autenticada declara x-required-roles."
      ),
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@gymnow.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gym.urls')),
    
    # JWT Authentication
    path('api/token/', GymTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', GymTokenRefreshView.as_view(), name='token_refresh'),
    
    # Swagger Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
