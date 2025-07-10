from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as ViewSet
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Subscription, Tag)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeReadSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserRecipesSerializer, UserSerializer)
from .utils import get_short_link

User = get_user_model()


class UserViewSet(ViewSet):
    """Вьюсет модели User."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def get_queryset(self):
        if self.action == 'subscriptions':
            queryset = User.objects.filter(
                subscription__user=self.request.user)
            return queryset
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action == 'avatar':
            return AvatarSerializer
        if self.action == 'subscriptions':
            return UserRecipesSerializer
        if self.action == 'subscribe':
            return SubscriptionSerializer
        return super().get_serializer_class()

    @action(
        detail=False, methods=['get'],
        permission_classes=(permissions.IsAuthenticated,))
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=['put'],
        permission_classes=(permissions.IsAuthenticated,))
    def avatar(self, request, **kwargs):
        """Установка аватара."""
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request, **kwargs):
        """Удаление аватара."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        """Список подписок текущего пользователя."""
        page = self.paginate_queryset(self.get_queryset())
        serializer = self.get_serializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=['post'],
        permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        """Подписка на пользователя."""
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'subscribed_to': self.get_object()})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, subscribed_to=self.get_object())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, **kwargs):
        """Отписка от пользователя."""
        subscription = Subscription.objects.filter(
            user=request.user, subscribed_to=self.get_object())
        if not subscription.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели Recipe."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user, short_link=get_short_link(Recipe))

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        if self.action == 'favorite':
            return FavoriteSerializer
        if self.action == 'shopping_cart':
            return ShoppingCartSerializer
        return RecipeCreateSerializer

    @action(
        detail=True, methods=['get'],
        permission_classes=(permissions.AllowAny,), url_path='get-link')
    def get_link(self, request, **kwargs):
        """Получение короткой ссылки на рецепт."""
        return Response(
            {'short-link': request.build_absolute_uri('/')
             + 's/' + self.get_object().short_link},
            status=status.HTTP_200_OK)

    def add_recipe(self, request, model):
        """Добавляет рецепт в избранное или список покупок."""
        serializer = self.get_serializer(
            data=request.data,
            context={
                'request': request,
                'recipe': self.get_object(),
                'model': model})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, recipe=self.get_object())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_recipe(self, request, model):
        """Удаляет рецепт из избранного или списка покупок."""
        try:
            obj = model.objects.get(
                user=request.user,
                recipe=self.get_object())
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post'],
        permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, **kwargs):
        return self.add_recipe(request=request, model=Favorite)

    @favorite.mapping.delete
    def delete_favorite(self, request, **kwargs):
        return self.remove_recipe(request=request, model=Favorite)

    @action(
        detail=True, methods=['post'],
        permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, **kwargs):
        return self.add_recipe(request=request, model=ShoppingCart)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, **kwargs):
        return self.remove_recipe(request=request, model=ShoppingCart)

    @action(
        detail=False, methods=['get'],
        permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Скачивание Списка покупок."""
        indredients = IngredientRecipe.objects.filter(
            recipe__shopping_cart__user=request.user).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount_sum=Sum('amount'))
        shopping_cart = ''
        for ingredient in indredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['amount_sum']
            shopping_cart += f'{name} ({measurement_unit}) - {amount}\n'
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response
