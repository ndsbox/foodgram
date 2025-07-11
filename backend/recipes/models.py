from api.constants import (MEASUREMENT_UNIT_MAX_LENGTH, NAME_MAX_LENGTH,
                           NAME_RECIPE_MAX_LENGTH, NAME_TAG_MAX_LENGTH,
                           SHORT_LINK_MAX_LENGTH, SLUG_MAX_LENGTH)
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    """Модель для ингредиента."""
    name = models.CharField(
        max_length=NAME_MAX_LENGTH, blank=False, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=MEASUREMENT_UNIT_MAX_LENGTH, blank=False,
        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Модель для тега."""
    name = models.CharField(
        max_length=NAME_TAG_MAX_LENGTH, unique=True, blank=False,
        verbose_name='Название')
    slug = models.SlugField(
        max_length=SLUG_MAX_LENGTH, unique=True, blank=False)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для рецепта."""
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='recipes',
        verbose_name='Автор рецепта')
    name = models.CharField(
        max_length=NAME_RECIPE_MAX_LENGTH, blank=False,
        verbose_name='Название')
    image = models.ImageField(
        upload_to='images/recipes/', blank=False, verbose_name='Фото')
    text = models.TextField(blank=False, verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientRecipe', blank=False,
        verbose_name='Ингредиенты', related_name='recipes')
    tags = models.ManyToManyField(
        Tag, blank=False, verbose_name='Теги', related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField(
        blank=False, validators=(MinValueValidator(1),),
        verbose_name='Время приготовления')
    short_link = models.CharField(
        max_length=SHORT_LINK_MAX_LENGTH, unique=True, blank=True,
        verbose_name='Короткая ссылка')
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации')

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Промежуточная модель."""
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='ingredients_in_recipe', verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(
        blank=False, validators=(MinValueValidator(1),),
        verbose_name='Количество')

    class Meta:
        verbose_name = 'ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredientrecipe')]

    def __str__(self):
        return f'Ингредиент: {self.ingredient} в рецепте: {self.recipe}'


class BaseUserRecipeModel(models.Model):
    """Базовый класс для ShoppingCart и Favorite."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_constraint')]


class ShoppingCart(BaseUserRecipeModel):
    """Модель для списка покупок."""

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'

    def __str__(self):
        return f'Рецепт: {self.recipe} в списке покупок {self.user}'


class Favorite(BaseUserRecipeModel):
    """Модель для избранного."""

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorite'

    def __str__(self):
        return f'Рецепт: {self.recipe} в избранном у {self.user}'


class Subscription(models.Model):
    """Модель для подписки."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribed_to',
        verbose_name='Пользователь')
    subscribed_to = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Подписан на')

    def clean(self):
        if self.user == self.subscribed_to:
            raise ValidationError("Нельзя подписаться на самого себя")
        super().clean()

    class Meta:
        verbose_name = 'подписки'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribed_to'],
                name='unique_subscription')]

    def __str__(self):
        return f'{self.user} подписан на {self.subscribed_to}'
