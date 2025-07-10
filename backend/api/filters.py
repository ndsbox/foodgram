import django_filters
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method='is_favorited_filter')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='is_in_shopping_cart_filter')
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all())

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def is_favorited_filter(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def is_in_shopping_cart_filter(self, queryset, name, value):
        if value == 1 and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset


class IngredientFilter(django_filters.FilterSet):
    """Фильтрует ингредиенты по полю name."""
    name = django_filters.CharFilter(
        field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = {'name': ['icontains']}
