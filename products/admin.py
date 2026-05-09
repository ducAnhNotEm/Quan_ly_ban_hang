from django.contrib import admin
from .models import Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'price', 'discount_percent', 'discounted_price', 'stock_quantity')
    list_filter = ('category',)
    search_fields = ('product_name', 'description')
    readonly_fields = ('discounted_price',)
    inlines = [ProductImageInline]
