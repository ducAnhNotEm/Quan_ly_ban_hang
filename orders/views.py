import json
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from accounts.models import TopUpRequest
from orders.models import Order
from products.models import Cart, CartItem, Product

"""
Module view contract cho luong gio hang va chuan bi mua ngay.

Muc tieu:
- Cung cap route/view nen de frontend goi duoc ngay.
- Chuan hoa guard login + chan staff di luong mua.
- Tra ve contract checkout o dang JSON.
"""

MONEY_QUANTIZE = Decimal("0.01")


def _format_currency_vnd(value) -> str:
    try:
        amount = Decimal(value or 0)
    except Exception:  # pragma: no cover - fallback du phong cho du lieu xau.
        amount = Decimal("0")

    rounded = int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return f"{rounded:,}".replace(",", ".") + " đ"


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


def _resolve_next_url(request, payload: dict) -> str | None:
    if "application/json" in (request.content_type or ""):
        return None

    next_url = str(payload.get("next") or "").strip()
    if not next_url:
        return None

    if url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("cart_checkout")


def _respond_error(request, payload: dict, message: str, *, status: int = 400, code: str | None = None):
    next_url = _resolve_next_url(request, payload)
    if next_url:
        messages.error(request, message)
        return redirect(next_url)
    return _json_error(message, status=status, code=code)


def _respond_success(request, payload: dict, message: str, data: dict):
    next_url = _resolve_next_url(request, payload)
    if next_url:
        messages.success(request, message)
        return redirect(next_url)
    return JsonResponse({"ok": True, "message": message, "data": data})


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
    customer = getattr(request.user, "customer_profile", None)
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
def cart_checkout(request):
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
    all_items = cart.items.select_related("product").order_by("id")

    cart_rows = []
    selected_rows = []
    selected_subtotal = Decimal("0")

    for item in all_items:
        line_subtotal = item.sub_total or Decimal("0")
        row = {
            "product_id": item.product_id,
            "product_name": item.product.product_name,
            "quantity": item.quantity,
            "stock_quantity": item.product.stock_quantity,
            "is_selected": item.is_selected,
            "unit_price_display": _format_currency_vnd(item.product.discounted_price),
            "line_subtotal_display": _format_currency_vnd(line_subtotal),
        }
        cart_rows.append(row)

        if item.is_selected:
            selected_subtotal += line_subtotal
            selected_rows.append(
                {
                    "product_id": item.product_id,
                    "product_name": item.product.product_name,
                    "quantity": item.quantity,
                    "unit_price_display": _format_currency_vnd(item.product.discounted_price),
                    "line_subtotal_display": _format_currency_vnd(line_subtotal),
                }
            )

    context = {
        "checkout_source": "CART",
        "cart_rows": cart_rows,
        "has_cart_items": bool(cart_rows),
        "item_rows": selected_rows,
        "has_items": bool(selected_rows),
        "subtotal_display": _format_currency_vnd(selected_subtotal),
        "discount_code_input": (request.GET.get("discount_code") or "").strip(),
    }
    return render(request, "checkout_cart.html", context)


def _stock_exceeds_message(requested_quantity: int, stock_quantity: int) -> str:
    return (
        f"So luong yeu cau ({requested_quantity}) vuot ton kho hien tai ({stock_quantity})."
    )


@purchase_flow_guard
def buy_now_checkout(request):
    if request.method != "GET":
        return _json_error(
            "Method khong duoc ho tro cho endpoint nay.",
            status=405,
            code="method_not_allowed",
        )

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    product_id_raw = (request.GET.get("product_id") or "").strip()
    quantity_raw = (request.GET.get("quantity") or "").strip()

    preview_row = None
    error_message = ""

    if product_id_raw or quantity_raw:
        try:
            product_id = int(product_id_raw)
            quantity = int(quantity_raw)
            if product_id <= 0 or quantity <= 0:
                raise ValueError
        except ValueError:
            error_message = "product_id va quantity phai la so nguyen duong."
        else:
            product = Product.objects.filter(pk=product_id).first()
            if product is None:
                error_message = "Khong tim thay san pham."
            elif quantity > product.stock_quantity:
                error_message = _stock_exceeds_message(quantity, product.stock_quantity)
            else:
                line_subtotal = (product.discounted_price * Decimal(quantity)).quantize(
                    MONEY_QUANTIZE,
                    rounding=ROUND_HALF_UP,
                )
                preview_row = {
                    "product_id": product.id,
                    "product_name": product.product_name,
                    "quantity": quantity,
                    "unit_price_display": _format_currency_vnd(product.discounted_price),
                    "line_subtotal_display": _format_currency_vnd(line_subtotal),
                }

    context = {
        "checkout_source": "BUY_NOW",
        "preview_row": preview_row,
        "error_message": error_message,
        "product_id_input": product_id_raw,
        "quantity_input": quantity_raw,
        "discount_code_input": (request.GET.get("discount_code") or "").strip(),
    }
    return render(request, "checkout_buy_now.html", context)


@purchase_flow_guard
def orders_list(request):
    if request.method != "GET":
        return _json_error(
            "Method khong duoc ho tro cho endpoint nay.",
            status=405,
            code="method_not_allowed",
        )

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    orders = Order.objects.filter(customer=customer).order_by("-created_at", "-id")
    order_rows = [
        {
            "id": order.id,
            "status": order.status,
            "total_amount_display": _format_currency_vnd(order.total_amount),
            "created_at": order.created_at,
        }
        for order in orders
    ]

    context = {
        "order_rows": order_rows,
        "has_orders": bool(order_rows),
    }
    return render(request, "orders_list.html", context)


@purchase_flow_guard
def order_detail(request, order_id: int):
    if request.method != "GET":
        return _json_error(
            "Method khong duoc ho tro cho endpoint nay.",
            status=405,
            code="method_not_allowed",
        )

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    order = get_object_or_404(
        Order.objects.prefetch_related("details__product"),
        pk=order_id,
        customer=customer,
    )

    detail_rows = [
        {
            "product_name": detail.product.product_name,
            "quantity": detail.quantity,
            "unit_price_display": _format_currency_vnd(detail.unit_price),
            "sub_total_display": _format_currency_vnd(detail.sub_total),
        }
        for detail in order.details.all()
    ]

    context = {
        "order": order,
        "detail_rows": detail_rows,
        "sub_total_display": _format_currency_vnd(order.sub_total_amount),
        "discount_display": _format_currency_vnd(order.discount_amount + order.coupon_discount_amount),
        "total_display": _format_currency_vnd(order.total_amount),
        "coupon_code_display": order.coupon_code or "-",
    }
    return render(request, "order_detail.html", context)


@purchase_flow_guard
def wallet_view(request):
    if request.method != "GET":
        return _json_error(
            "Method khong duoc ho tro cho endpoint nay.",
            status=405,
            code="method_not_allowed",
        )

    customer, error_response = _get_customer_or_error(request)
    if error_response:
        return error_response

    wallet = getattr(customer, "wallet", None)
    balance = wallet.balance if wallet else 0

    topup_rows = [
        {
            "id": row["id"],
            "amount_display": _format_currency_vnd(row["amount"]),
            "status": row["status"],
            "note": row["note"] or "",
        }
        for row in TopUpRequest.objects.filter(customer=customer)
        .order_by("-id")
        .values("id", "amount", "status", "note")[:10]
    ]

    context = {
        "balance_display": _format_currency_vnd(balance),
        "topup_rows": topup_rows,
        "has_topups": bool(topup_rows),
    }
    return render(request, "wallet_view.html", context)


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
    all_items = cart.items.select_related("product").order_by("id")

    cart_rows = []
    selected_subtotal = Decimal("0")

    for item in all_items:
        line_subtotal = item.sub_total or Decimal("0")
        row = {
            "product_id": item.product_id,
            "product_name": item.product.product_name,
            "image_url": item.product.image.url if item.product.image else None,
            "quantity": item.quantity,
            "stock_quantity": item.product.stock_quantity,
            "is_selected": item.is_selected,
            "unit_price_display": _format_currency_vnd(item.product.discounted_price),
            "line_subtotal_display": _format_currency_vnd(line_subtotal),
        }
        cart_rows.append(row)

        if item.is_selected:
            selected_subtotal += line_subtotal

    context = {
        "cart_rows": cart_rows,
        "has_cart_items": bool(cart_rows),
        "subtotal_display": _format_currency_vnd(selected_subtotal),
    }
    return render(request, "cart.html", context)


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
        return _respond_error(
            request,
            payload,
            "product_id phai la so nguyen duong.",
            code="invalid_product_id",
        )

    quantity = payload.get("quantity", 1)
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return _respond_error(
            request,
            payload,
            "quantity phai la so nguyen duong lon hon 0.",
            code="invalid_quantity",
        )
    if quantity <= 0:
        return _respond_error(
            request,
            payload,
            "quantity phai la so nguyen duong lon hon 0.",
            code="invalid_quantity",
        )

    product = Product.objects.filter(pk=product_id).first()
    if product is None:
        return _respond_error(
            request,
            payload,
            "Khong tim thay san pham.",
            status=404,
            code="product_not_found",
        )
    if quantity > product.stock_quantity:
        return _respond_error(
            request,
            payload,
            _stock_exceeds_message(quantity, product.stock_quantity),
            code="quantity_exceeds_stock",
        )

    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={
            "quantity": quantity,
            "is_selected": True,
        },
    )

    if created:
        success_message = (
            f'Da them "{product.product_name}" vao gio hang voi so luong {quantity}.'
        )
    else:
        next_quantity = cart_item.quantity + quantity
        if next_quantity > product.stock_quantity:
            return _respond_error(
                request,
                payload,
                _stock_exceeds_message(next_quantity, product.stock_quantity),
                code="quantity_exceeds_stock",
            )
        cart_item.quantity = next_quantity
        cart_item.is_selected = True
        cart_item.full_clean()
        cart_item.save()
        success_message = (
            f'Da cap nhat "{product.product_name}" trong gio hang len so luong {next_quantity}.'
        )

    return _respond_success(request, payload, success_message, _cart_snapshot(cart))


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
        return _respond_error(
            request,
            payload,
            "product_id phai la so nguyen duong.",
            code="invalid_product_id",
        )
    if quantity is None:
        return _respond_error(
            request,
            payload,
            "quantity phai la so nguyen duong lon hon 0.",
            code="invalid_quantity",
        )

    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item = CartItem.objects.select_related("product").filter(
        cart=cart,
        product_id=product_id,
    ).first()
    if cart_item is None:
        return _respond_error(
            request,
            payload,
            "San pham khong ton tai trong gio hang.",
            status=404,
            code="cart_item_not_found",
        )
    if quantity > cart_item.product.stock_quantity:
        return _respond_error(
            request,
            payload,
            _stock_exceeds_message(quantity, cart_item.product.stock_quantity),
            code="quantity_exceeds_stock",
        )

    cart_item.quantity = quantity
    cart_item.full_clean()
    cart_item.save()

    success_message = (
        f'Da cap nhat "{cart_item.product.product_name}" thanh so luong {quantity}.'
    )
    return _respond_success(request, payload, success_message, _cart_snapshot(cart))


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
        return _respond_error(
            request,
            payload,
            "product_id phai la so nguyen duong.",
            code="invalid_product_id",
        )

    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item = CartItem.objects.select_related("product").filter(
        cart=cart,
        product_id=product_id,
    ).first()
    if cart_item is None:
        return _respond_error(
            request,
            payload,
            "San pham khong ton tai trong gio hang.",
            status=404,
            code="cart_item_not_found",
        )

    product_name = cart_item.product.product_name
    cart_item.delete()

    return _respond_success(
        request,
        payload,
        f'Da xoa "{product_name}" khoi gio hang.',
        _cart_snapshot(cart),
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
        return _respond_error(
            request,
            payload,
            "product_id phai la so nguyen duong.",
            code="invalid_product_id",
        )
    if is_selected is None:
        return _respond_error(
            request,
            payload,
            "is_selected phai la bool.",
            code="invalid_is_selected",
        )

    cart, _ = Cart.objects.get_or_create(customer=customer)
    cart_item = CartItem.objects.select_related("product").filter(
        cart=cart,
        product_id=product_id,
    ).first()
    if cart_item is None:
        return _respond_error(
            request,
            payload,
            "San pham khong ton tai trong gio hang.",
            status=404,
            code="cart_item_not_found",
        )

    cart_item.is_selected = is_selected
    cart_item.save(update_fields=["is_selected"])

    if is_selected:
        success_message = f'Da chon "{cart_item.product.product_name}" cho checkout.'
    else:
        success_message = f'Da bo chon "{cart_item.product.product_name}" khoi checkout.'

    return _respond_success(request, payload, success_message, _cart_snapshot(cart))


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
        return _json_error(_stock_exceeds_message(quantity, product.stock_quantity), code="quantity_exceeds_stock")

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
