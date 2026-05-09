import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Product

class Command(BaseCommand):
    help = 'Seed database with dummy products'

    def handle(self, *args, **kwargs):
        dummy_products = [
            {"name": "Áo thun basic nam", "price": "120000", "stock": 20, "category": "Thời trang", "desc": "Áo thun cotton mềm mát.", "image_path": "products/images/ao_thun.jpg"},
            {"name": "Quần jean xanh", "price": "350000", "stock": 12, "category": "Thời trang", "desc": "Quần jean dáng ôm thoải mái.", "image_path": "products/images/quan_jean.jpg"},
            {"name": "Giày sneaker trắng", "price": "590000", "stock": 8, "category": "Giày dép", "desc": "Giày thể thao êm chân.", "image_path": "products/images/giay_sneaker.jpg"},
            {"name": "Balo laptop chống nước", "price": "420000", "stock": 15, "category": "Phụ kiện", "desc": "Balo có ngăn chống sốc an toàn.", "image_path": "products/images/balo.jpg"},
            {"name": "Tai nghe bluetooth", "price": "299000", "stock": 25, "category": "Điện tử", "desc": "Tai nghe âm thanh nổi, pin trâu.", "image_path": "products/images/tai_nghe.jpg"},
            {"name": "Chuột không dây", "price": "180000", "stock": 30, "category": "Điện tử", "desc": "Chuột quang nhạy bén, tiết kiệm pin.", "image_path": "products/images/chuot.jpg"},
            {"name": "Bình giữ nhiệt inox", "price": "150000", "stock": 10, "category": "Gia dụng", "desc": "Bình giữ lạnh/nóng 12 giờ.", "image_path": "products/images/binh_giu_nhiet.jpg"},
            {"name": "Sổ tay bìa da", "price": "90000", "stock": 18, "category": "Văn phòng phẩm", "desc": "Sổ ghi chép công việc cao cấp.", "image_path": "products/images/so_tay.jpg"},
            {"name": "Đồng hồ thể thao", "price": "750000", "stock": 5, "category": "Phụ kiện", "desc": "Đồng hồ thông minh đo nhịp tim.", "image_path": "products/images/dong_ho.jpg"},
            {"name": "Áo khoác gió", "price": "480000", "stock": 0, "category": "Thời trang", "desc": "Áo khoác mỏng nhẹ chống thấm.", "image_path": "products/images/ao_khoac.jpg"},
            {"name": "Loa mini bluetooth", "price": "260000", "stock": 0, "category": "Điện tử", "desc": "Loa siêu nhỏ bass mạnh.", "image_path": "products/images/loa.jpg"},
            {"name": "Túi đeo chéo", "price": "210000", "stock": 7, "category": "Phụ kiện", "desc": "Túi đeo nhỏ gọn thời trang.", "image_path": "products/images/tui_deo.jpg"}
        ]

        for item in dummy_products:
            base_slug = slugify(item['name'])
            slug = base_slug
            
            existing_product = Product.objects.filter(product_name=item['name']).first()
            if existing_product:
                slug = existing_product.slug
            else:
                counter = 1
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

            Product.objects.update_or_create(
                product_name=item['name'],
                defaults={
                    'slug': slug,
                    'description': item['desc'],
                    'price': Decimal(item['price']),
                    'stock_quantity': item['stock'],
                    'category': item['category'],
                    'image': item['image_path'],
                    'image_url': None  # Clear the URL to use local image
                }
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(dummy_products)} products.'))
