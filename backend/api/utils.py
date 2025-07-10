import random
from string import ascii_letters, digits

from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipe


def get_short_link(model):
    while True:
        short_link = ''.join(random.choices(ascii_letters + digits, k=5))
        if not model.objects.filter(short_link=short_link).exists():
            break
    return short_link


def recipe_redirection(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    recipe_id = recipe.id
    return redirect(
        request.build_absolute_uri('/') + f'recipes/{recipe_id}/')
