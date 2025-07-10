import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Upload ingredients to the database from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **options):
        json_file_path = options['json_file']
        with open(json_file_path, 'r') as file:
            ingredients = json.load(file)

        for ingredient in ingredients:
            Ingredient.objects.create(
                name=ingredient['name'],
                measurement_unit=ingredient['measurement_unit'])
