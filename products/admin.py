from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'price', 'discount_percent', 'discounted_price', 'stock_quantity')
    list_filter = ('category',)
    search_fields = ('product_name', 'description')
    readonly_fields = ('discounted_price',)
