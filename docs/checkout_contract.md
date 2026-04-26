# Checkout Contract (CART + BUY_NOW_PREPARE)

## Muc tieu
Tai lieu nay chuan hoa payload checkout de frontend/backend su dung thong nhat cho 2 nguon:
- `CART`
- `BUY_NOW`

## Checkout payload chuan
```json
{
  "source": "CART|BUY_NOW",
  "items": [
    {
      "product_id": 123,
      "quantity": 2
    }
  ],
  "subtotal": "90000.00"
}
```

## Quy uoc field
- `source`: nguon tao checkout, chi nhan `CART` hoac `BUY_NOW`.
- `items`: danh sach item tham gia checkout.
- `items[].product_id`: ID san pham (int).
- `items[].quantity`: so luong mua (int > 0).
- `subtotal`: tong tien theo decimal string (2 chu so thap phan).

## Route contract hien tai
- `GET /gio-hang/` (`cart_view`)
  - Tra ve snapshot gio hang + `checkout` voi `source = CART`.
- `POST /gio-hang/them/` (`cart_add`)
  - Input: `product_id`, `quantity`.
  - Tra ve snapshot gio hang + `checkout` voi `source = CART`.
- `POST /gio-hang/cap-nhat/` (`cart_update`)
  - Input: `product_id`, `quantity`.
  - Tra ve snapshot gio hang + `checkout` voi `source = CART`.
- `POST /gio-hang/xoa/` (`cart_remove`)
  - Input: `product_id`.
  - Tra ve snapshot gio hang + `checkout` voi `source = CART`.
- `POST /gio-hang/chon/` (`cart_select`)
  - Input: `product_id`, `is_selected`.
  - Tra ve snapshot gio hang + `checkout` voi `source = CART`.
- `POST /mua-ngay/chuan-bi/` (`buy_now_prepare`)
  - Input: `product_id`, `quantity`.
  - Tra ve `checkout` voi `source = BUY_NOW`.

## Auth/permission guard
- Tat ca route checkout bat buoc dang nhap.
- Tai khoan `staff` bi chan khoi luong mua (HTTP 403, `error.code = staff_forbidden`).

## Format response tong quat
Thanh cong:
```json
{
  "ok": true,
  "data": {
    "checkout": {
      "source": "CART",
      "items": [{"product_id": 123, "quantity": 1}],
      "subtotal": "45000.00"
    }
  }
}
```

Loi:
```json
{
  "ok": false,
  "error": {
    "code": "invalid_quantity",
    "message": "quantity phai la so nguyen duong."
  }
}
```
