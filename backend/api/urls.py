from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = DefaultRouter()

router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', UserViewSet, basename='users')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('auth/', include('djoser.urls.authtoken')),
]
