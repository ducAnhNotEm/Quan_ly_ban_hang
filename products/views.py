from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages

from products.models import Product, ProductImage

"""
Module xử lý giao diện cho app `products`.

Các hàm hiện có:
- admin_product_create: hiển thị form tạo sản phẩm (kèm gợi ý danh mục).
- product_detail_preview: trang xem trước chi tiết dạng rỗng (placeholder).
- product_detail: trang chi tiết sản phẩm theo `product_id`.
"""


def admin_product_create(request):
    """
    Hiển thị trang quản trị thêm sản phẩm và xử lý lưu sản phẩm mới.

    Luồng:
    - Nếu là GET: lấy danh mục sản phẩm duy nhất từ DB để hỗ trợ nhập liệu.
    - Nếu là POST: tạo sản phẩm mới từ dữ liệu form và file ảnh.
    - Sau khi tạo thành công: thông báo và chuyển hướng về trang chủ.
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Bạn không có quyền truy cập trang này.")
        return redirect("home")

    if request.method == "POST":
        product_name = request.POST.get("product_name")
        category = request.POST.get("category")
        description = request.POST.get("description")
        price = request.POST.get("price")
        discount_percent = request.POST.get("discount_percent") or 0
        stock_quantity = request.POST.get("stock_quantity")
        main_image = request.FILES.get("main_image")

        try:
            product = Product.objects.create(
                product_name=product_name,
                category=category,
                description=description,
                price=price,
                discount_percent=discount_percent,
                stock_quantity=stock_quantity,
                image=main_image
            )
            
            # Lưu các ảnh phụ (gallery) nếu có
            gallery_images = request.FILES.getlist("gallery_images")
            for img in gallery_images:
                ProductImage.objects.create(product=product, image=img)

            messages.success(request, f"Đã thêm sản phẩm '{product_name}' thành công.")
            return redirect("home")
        except Exception as e:
            messages.error(request, f"Lỗi khi thêm sản phẩm: {e}")

    # Danh sách danh mục có sẵn để hỗ trợ quản trị nhập nhanh.
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
    """
    Hiển thị trang xem trước chi tiết sản phẩm ở trạng thái rỗng.

    Mục đích:
    - Dùng khi cần xem bố cục giao diện trước khi gắn dữ liệu thật.
    """
    return render(request, "product_detail.html", {"product": None})


def product_detail(request, product_id: int):
    """
    Hiển thị chi tiết sản phẩm theo ID.

    Luồng:
    - Tìm sản phẩm bằng `product_id`.
    - Nếu không tồn tại -> trả 404.
    - Nếu tồn tại -> hiển thị vào `product_detail.html`.
    """
    product = get_object_or_404(Product, pk=product_id)
    return render(request, "product_detail.html", {"product": product})

