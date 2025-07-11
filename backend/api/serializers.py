import base64

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserCreateSerializer as CreateSerializer
from djoser.serializers import UserSerializer as Serializer
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Subscription, Tag)
from rest_framework import serializers

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Класс для декодирования изображения base64."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class StatusFieldsMixin(serializers.ModelSerializer):

    def checking_fields(self, model, obj):
        """Функция проверяет, является ли пользователь подписчиком,
           добавил ли он объект в избранное или в корзину покупок.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if model == Subscription:
            return request.user.subscribed_to.filter(
                subscribed_to=obj).exists()
        return model.objects.filter(user=request.user, recipe=obj).exists()


class UserCreateSerializer(CreateSerializer):
    """Сериализатор создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')

    def validate(self, data):
        if data['email'] == data['username']:
            raise serializers.ValidationError(
                'Имя пользователя не может совпадать '
                'с адресом электронной почты!')

        try:
            user = User.objects.get(username=data['username'])
            if user:
                raise serializers.ValidationError(
                    'Имя пользователя уже занято!')
        except ObjectDoesNotExist:
            pass

        try:
            user = User.objects.get(email=data['email'])
            if user:
                raise serializers.ValidationError(
                    'Email уже используется!')
        except ObjectDoesNotExist:
            pass

        return data


class UserSerializer(Serializer, StatusFieldsMixin):
    """Сериализатор для модели пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        return self.checking_fields(model=Subscription, obj=obj)


class AvatarSerializer(UserSerializer):
    """Сериализатор для добавление аватара."""

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data):
        if not data.get('avatar'):
            raise serializers.ValidationError('Аватар не добавлен!')
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientForRecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами при создании рецепта."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0!')
        return value


class IngredientForRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для представления информации об ингредиентах
       в рецептах при чтении данных."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeReadSerializer(StatusFieldsMixin):
    """Сериализатор для модели Recipe при GET-запросах."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = IngredientForRecipeReadSerializer(
        many=True, source='ingredients_in_recipe')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time')
        read_only_fields = fields

    def get_is_favorited(self, obj):
        return self.checking_fields(model=Favorite, obj=obj)

    def get_is_in_shopping_cart(self, obj):
        return self.checking_fields(model=ShoppingCart, obj=obj)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe при POST, PATCH, DELETE запросах."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, allow_empty=False)
    ingredients = IngredientForRecipeCreateSerializer(
        many=True, allow_empty=False)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time', 'short_link')
        read_only_fields = ('author', 'short_link')

    def validate(self, data):
        if not self.initial_data.get('tags'):
            raise serializers.ValidationError(
                'Нужно выбрать тег!')
        if not self.initial_data.get('ingredients'):
            raise serializers.ValidationError(
                'Нужно указать ингредиент!')
        return data

    def validate_tags(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Повтор тега недопустим!')
        return value

    def validate_ingredients(self, value):
        ingredients_id = []

        for ingredient_data in value:
            ingredient_id = ingredient_data['id']
            try:
                Ingredient.objects.get(id=ingredient_id)
            except ObjectDoesNotExist:
                raise serializers.ValidationError(
                    f'Ингредиента с id={ingredient_id} нет в базе!')

            ingredients_id.append(ingredient_id)

        if len(ingredients_id) != len(set(ingredients_id)):
            raise serializers.ValidationError(
                'Повтор ингредиентов недопустим!')

        return value

    def create_tags(self, tags, recipe):
        recipe.tags.set(tags)

    def create_ingredients(self, ingredients, recipe):
        ingredient_recipes = []

        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(pk=ingredient['id'])
            ingredient_recipe = IngredientRecipe(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=ingredient['amount'])
            ingredient_recipes.append(ingredient_recipe)

        IngredientRecipe.objects.bulk_create(ingredient_recipes)

    def get_tags(self, data):
        return data.pop('tags')

    def get_ingredients(self, data):
        return data.pop('ingredients')

    @transaction.atomic
    def create(self, validated_data):
        tags = self.get_tags(validated_data)
        ingredients = self.get_ingredients(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients, recipe)
        self.create_tags(tags, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.tags.clear()
        self.create_tags(self.get_tags(validated_data), instance)

        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(self.get_ingredients(validated_data), instance)

        instance = super().update(instance, validated_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        serializer = RecipeReadSerializer(instance)
        return serializer.data


class RecipePreviewSerializer(serializers.ModelSerializer):
    """Сериализатор для получения основных данных модели Recipe."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UniqueRecipeMixin(serializers.ModelSerializer):
    """Миксин для сериализаторов, проверяющий уникальность рецепта в модели."""

    class Meta:
        fields = ('user', 'recipe',)
        read_only_fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe')
        model = self.context.get('model')
        if model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                f'Рецепт - {recipe.name} уже добавлен!')
        return data

    def to_representation(self, instance):
        serializer = RecipePreviewSerializer(instance.recipe)
        return serializer.data


class FavoriteSerializer(UniqueRecipeMixin):
    """Сериализатор для модели Favorite."""

    class Meta(UniqueRecipeMixin.Meta):
        model = Favorite


class ShoppingCartSerializer(UniqueRecipeMixin):
    """Сериализатор для модели ShoppingCart."""

    class Meta(UniqueRecipeMixin.Meta):
        model = ShoppingCart


class UserRecipesSerializer(UserSerializer):
    """Сериализатор для модели User и его рецептов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source="recipes.count")

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipePreviewSerializer(recipes, many=True)
        return serializer.data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subscription."""

    class Meta:
        model = Subscription
        fields = ('user', 'subscribed_to',)
        read_only_fields = ('user', 'subscribed_to',)

    def validate(self, data):
        user = self.context.get('request').user
        subscribed_to = self.context.get('subscribed_to')
        if user == subscribed_to:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя!')
        if Subscription.objects.filter(
            user=user, subscribed_to=subscribed_to
        ).exists():
            raise serializers.ValidationError(
                f'Вы уже подписаны на {subscribed_to.username}!')
        return data

    def to_representation(self, instance):
        serializer = UserRecipesSerializer(
            instance.subscribed_to,
            context=self.context
        )
        return serializer.data
