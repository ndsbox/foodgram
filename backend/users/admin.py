from django.contrib import admin
from django.contrib.admin import display

from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'email', 'first_name', 'last_name',
                    'password', 'get_number_of_recipes',
                    'get_number_of_subscribers')
    list_filter = ('username', 'email')
    search_fields = ('email', 'username')

    @display(description='Количество рецептов')
    def get_number_of_recipes(self, obj):
        return obj.get_number_of_recipes()

    @display(description='Количество подписчиков')
    def get_number_of_subscribers(self, obj):
        return obj.get_number_of_subscribers()


admin.site.register(User, UserAdmin)
