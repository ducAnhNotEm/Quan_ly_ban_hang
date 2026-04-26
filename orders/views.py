import json
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from accounts.models import Customer
from products.models import Cart, CartItem, Product

"""
Module view contract cho luong gio hang va chuan bi mua ngay.

Muc tieu:
- Cung cap route/view nen de frontend goi duoc ngay.
- Chuan hoa guard login + chan staff di luong mua.
- Tra ve contract checkout o dang JSON.
"""

MONEY_QUANTIZE = Decimal("0.01")


def _json_error(message: str, *, status: int = 400, code: str | None = None) -> JsonResponse:
    error_payload = {"message": message}
    if code:
        error_payload["code"] = code
    return JsonResponse({"ok": False, "error": error_payload}, status=status)


def _to_decimal_string(value: Decimal) -> str:
    return format(value.quantize(MONEY_QUANTIZE, rounding=ROUND_HALF_UP), "f")


def _parse_request_data(request) -> dict:
    if "application/json" in (request.content_type or ""):
        try:
            body = request.body.decode("utf-8").strip()
            return json.loads(body) if body else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Payload JSON khong hop le.") from exc

    return request.POST.dict()


def _parse_positive_int(data: dict, field_name: str) -> int | None:
    raw_value = data.get(field_name)
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None

    return value if value > 0 else None


def _parse_bool(data: dict, field_name: str) -> bool | None:
    raw_value = data.get(field_name)
    if isinstance(raw_value, bool):
        return raw_value

    normalized = str(raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _build_checkout_payload(source: str, items_with_amount: list[dict]) -> dict:
    subtotal = sum((item["line_subtotal"] for item in items_with_amount), Decimal("0"))
    checkout_items = [
        {
            "product_id": item["product_id"],
            "quantity": item["quantity"],
        }
        for item in items_with_amount
    ]
    return {
        "source": source,
        "items": checkout_items,
        "subtotal": _to_decimal_string(subtotal),
    }


def _cart_snapshot(cart: Cart) -> dict:
    cart_items = []
    selected_items_for_checkout = []

    for item in cart.items.select_related("product").order_by("id"):
        line_subtotal = item.sub_total or Decimal("0")
        item_payload = {
            "product_id": item.product_id,
            "quantity": item.quantity,
            "is_selected": item.is_selected,
            "unit_price": _to_decimal_string(item.product.discounted_price),
            "line_subtotal": _to_decimal_string(line_subtotal),
        }
        cart_items.append(item_payload)

        if item.is_selected:
            selected_items_for_checkout.append(
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "line_subtotal": line_subtotal,
                }
            )

    return {
        "cart": {
            "id": cart.id,
            "total_items": sum(item["quantity"] for item in cart_items),
            "items": cart_items,
        },
        "checkout": _build_checkout_payload("CART", selected_items_for_checkout),
    }


def _ensure_post(request) -> JsonResponse | None:
    if request.method != "POST":
        return _json_error(
            "Method khong duoc ho tro cho endpoint nay.",
            status=405,
            code="method_not_allowed",
        )
    return None


def _get_customer_or_error(request):
    customer = Customer.objects.filter(user=request.user).first()
    if customer is None:
        return None, _json_error(
            "Tai khoan chua co ho so khach hang.",
            status=403,
            code="customer_profile_missing",
        )
    return customer, None


def purchase_flow_guard(view_func):
    @wraps(view_func)
    @login_required(login_url="login")
    def _wrapped(request, *args, **kwargs):
        if request.user.is_staff:
            return _json_error(
                "Tai khoan staff khong duoc di luong mua hang.",
                status=403,
                code="staff_forbidden",
            )
        return view_func(request, *args, **kwargs)

    return _wrapped


@purchase_flow_guard
def cart_view(request):
    if request.method != "GET":
        return _json_error(
            "Method khong duoc ho tro cho endpoint nay.",
            status=405,
            code="method_not_allowed",
        )

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    cart, _ = Cart.objects.get_or_create(customer=customer)
    return JsonResponse({"ok": True, "data": _cart_snapshot(cart)})


@purchase_flow_guard
def cart_add(request):
    method_error = _ensure_post(request)
    if method_error:
        return method_error

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    try:
        payload = _parse_request_data(request)
    except ValueError as exc:
        return _json_error(str(exc), code="invalid_json")

    product_id = _parse_positive_int(payload, "product_id")
    if product_id is None:
        return _json_error("product_id phai la so nguyen duong.", code="invalid_product_id")

    quantity = payload.get("quantity", 1)
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return _json_error("quantity phai la so nguyen duong.", code="invalid_quantity")
    if quantity <= 0:
        return _json_error("quantity phai la so nguyen duong.", code="invalid_quantity")

    product = Product.objects.filter(pk=product_id).first()
    if product is None:
        return _json_error("Khong tim thay san pham.", status=404, code="product_not_found")
    if quantity > product.stock_quantity:
        return _json_error("So luong vuot qua ton kho hien tai.", code="quantity_exceeds_stock")

    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={
            "quantity": quantity,
            "is_selected": True,
        },
    )

    if not created:
        next_quantity = cart_item.quantity + quantity
        if next_quantity > product.stock_quantity:
            return _json_error("So luong vuot qua ton kho hien tai.", code="quantity_exceeds_stock")
        cart_item.quantity = next_quantity
        cart_item.is_selected = True
        cart_item.full_clean()
        cart_item.save()

    return JsonResponse(
        {
            "ok": True,
            "message": "Da them san pham vao gio hang.",
            "data": _cart_snapshot(cart),
        }
    )


@purchase_flow_guard
def cart_update(request):
    method_error = _ensure_post(request)
    if method_error:
        return method_error

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    try:
        payload = _parse_request_data(request)
    except ValueError as exc:
        return _json_error(str(exc), code="invalid_json")

    product_id = _parse_positive_int(payload, "product_id")
    quantity = _parse_positive_int(payload, "quantity")
    if product_id is None:
        return _json_error("product_id phai la so nguyen duong.", code="invalid_product_id")
    if quantity is None:
        return _json_error("quantity phai la so nguyen duong.", code="invalid_quantity")

    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item = CartItem.objects.select_related("product").filter(
        cart=cart,
        product_id=product_id,
    ).first()
    if cart_item is None:
        return _json_error("San pham khong ton tai trong gio hang.", status=404, code="cart_item_not_found")
    if quantity > cart_item.product.stock_quantity:
        return _json_error("So luong vuot qua ton kho hien tai.", code="quantity_exceeds_stock")

    cart_item.quantity = quantity
    cart_item.full_clean()
    cart_item.save()

    return JsonResponse(
        {
            "ok": True,
            "message": "Da cap nhat so luong san pham trong gio hang.",
            "data": _cart_snapshot(cart),
        }
    )


@purchase_flow_guard
def cart_remove(request):
    method_error = _ensure_post(request)
    if method_error:
        return method_error

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    try:
        payload = _parse_request_data(request)
    except ValueError as exc:
        return _json_error(str(exc), code="invalid_json")

    product_id = _parse_positive_int(payload, "product_id")
    if product_id is None:
        return _json_error("product_id phai la so nguyen duong.", code="invalid_product_id")

    cart, _ = Cart.objects.get_or_create(customer=customer)
    deleted_count, _ = CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    if deleted_count == 0:
        return _json_error("San pham khong ton tai trong gio hang.", status=404, code="cart_item_not_found")

    return JsonResponse(
        {
            "ok": True,
            "message": "Da xoa san pham khoi gio hang.",
            "data": _cart_snapshot(cart),
        }
    )


@purchase_flow_guard
def cart_select(request):
    method_error = _ensure_post(request)
    if method_error:
        return method_error

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    try:
        payload = _parse_request_data(request)
    except ValueError as exc:
        return _json_error(str(exc), code="invalid_json")

    product_id = _parse_positive_int(payload, "product_id")
    is_selected = _parse_bool(payload, "is_selected")

    if product_id is None:
        return _json_error("product_id phai la so nguyen duong.", code="invalid_product_id")
    if is_selected is None:
        return _json_error("is_selected phai la bool.", code="invalid_is_selected")

    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
    if cart_item is None:
        return _json_error("San pham khong ton tai trong gio hang.", status=404, code="cart_item_not_found")

    cart_item.is_selected = is_selected
    cart_item.save()

    return JsonResponse(
        {
            "ok": True,
            "message": "Da cap nhat trang thai chon san pham.",
            "data": _cart_snapshot(cart),
        }
    )


@purchase_flow_guard
def buy_now_prepare(request):
    method_error = _ensure_post(request)
    if method_error:
        return method_error

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    try:
        payload = _parse_request_data(request)
    except ValueError as exc:
        return _json_error(str(exc), code="invalid_json")

    product_id = _parse_positive_int(payload, "product_id")
    quantity = _parse_positive_int(payload, "quantity")

    if product_id is None:
        return _json_error("product_id phai la so nguyen duong.", code="invalid_product_id")
    if quantity is None:
        return _json_error("quantity phai la so nguyen duong.", code="invalid_quantity")

    product = Product.objects.filter(pk=product_id).first()
    if product is None:
        return _json_error("Khong tim thay san pham.", status=404, code="product_not_found")
    if quantity > product.stock_quantity:
        return _json_error("So luong vuot qua ton kho hien tai.", code="quantity_exceeds_stock")

    line_subtotal = (product.discounted_price * Decimal(quantity)).quantize(
        MONEY_QUANTIZE,
        rounding=ROUND_HALF_UP,
    )
    checkout_payload = _build_checkout_payload(
        "BUY_NOW",
        [
            {
                "product_id": product.id,
                "quantity": quantity,
                "line_subtotal": line_subtotal,
            }
        ],
    )

    return JsonResponse(
        {
            "ok": True,
            "data": {
                "checkout": checkout_payload,
            },
        }
    )
