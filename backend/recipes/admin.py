from django.contrib import admin
from django.contrib.admin import ModelAdmin, register

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Subscription, Tag)


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@register(IngredientRecipe)
class IngredientRecipeAdmin(ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')


class IngredientInline(admin.StackedInline):
    model = IngredientRecipe
    min_num = 1


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('name', 'text', 'cooking_time', 'favorites')
    search_fields = ('name', 'tags__name')
    inlines = (IngredientInline,)

    @admin.display(description='Число добавлений в избранное')
    def favorites(self, obj):
        return obj.favorite.count()


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display = ('user', 'subscribed_to')
    search_fields = ('user__username', 'subscribed_to__username')
