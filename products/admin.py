from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'available', 'is_featured', 'is_popular', 'rating')
    list_filter = ('available', 'is_featured', 'is_popular', 'category')
    list_editable = ('price', 'stock', 'available')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
