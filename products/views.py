from django.shortcuts import get_object_or_404, render

from products.models import Product

"""
Module xử lý giao diện cho app `products`.

Các hàm hiện có:
- admin_product_create: hiển thị form tạo sản phẩm (kèm gợi ý danh mục).
- product_detail_preview: trang xem trước chi tiết dạng rỗng (placeholder).
- product_detail: trang chi tiết sản phẩm theo `product_id`.
"""


def admin_product_create(request):
    """
    Hiển thị trang quản trị thêm sản phẩm.

    Luồng:
    - Lấy danh mục sản phẩm duy nhất từ DB để đổ vào datalist.
    - Trả về template `admin_product_create.html`.

    Lưu ý:
    - Hàm này hiện chủ yếu phục vụ hiển thị form;
      logic lưu sản phẩm có thể xử lý ở bước khác.
    """
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

