from django.shortcuts import get_object_or_404, render

from products.models import Product


def admin_product_create(request):
    categories = [
        category
        for category in Product.objects.order_by("category")
        .values_list("category", flat=True)
        .distinct()
        if category
    ]
    context = {"category_options": categories}
    return render(request, "admin_product_create.html", context)


def product_detail_preview(request):
    return render(request, "product_detail.html", {"product": None})


def product_detail(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, "product_detail.html", {"product": product})
