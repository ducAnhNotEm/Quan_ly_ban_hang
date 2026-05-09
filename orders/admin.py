from django.contrib import admin
from .models import Order, OrderDetail

class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0
    readonly_fields = ('sub_total',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'sub_total_amount', 'discount_amount', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderDetailInline]
    readonly_fields = ('sub_total_amount', 'discount_amount', 'total_amount')
