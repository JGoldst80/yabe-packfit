# ---------- YABE eBay PROXY SECTION (safe to paste as-is) ----------
# Requires: `requests` in requirements.txt (already added)

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
import requests

EBAY_API = "https://api.ebay.com"
router = APIRouter()

def _forward_headers(req: Request) -> dict:
    h = {"Accept": "application/json"}
    auth = req.headers.get("authorization")
    if auth:
        h["Authorization"] = auth
    ctype = req.headers.get("content-type")
    if ctype:
        h["Content-Type"] = ctype
    return h

async def _proxy(req: Request, method: str, ebay_path: str, inject_headers: dict | None = None) -> Response:
    url = f"{EBAY_API}{ebay_path}"
    params = dict(req.query_params)
    body = await req.body()
    headers = _forward_headers(req)
    if inject_headers:
        headers.update(inject_headers)

    r = requests.request(method, url, params=params, data=body if body else None, headers=headers, timeout=30)
    mt = r.headers.get("content-type", "application/json")
    return Response(content=r.content, status_code=r.status_code, media_type=mt)

# ---------- Inventory ----------
@router.get("/sell/inventory/v1/inventory_item/{sku}")
async def proxy_get_inventory_item(sku: str, request: Request):
    return await _proxy(request, "GET", f"/sell/inventory/v1/inventory_item/{sku}")

@router.put("/sell/inventory/v1/inventory_item/{sku}")
async def proxy_put_inventory_item(sku: str, request: Request, contentLanguage: str = "en-US"):
    return await _proxy(
        request, "PUT", f"/sell/inventory/v1/inventory_item/{sku}",
        inject_headers={"Content-Language": contentLanguage}
    )

# ---------- Offers ----------
@router.post("/sell/inventory/v1/offer")
async def proxy_post_offer(request: Request, contentLanguage: str = "en-US"):
    return await _proxy(
        request, "POST", "/sell/inventory/v1/offer",
        inject_headers={"Content-Language": contentLanguage}
    )

@router.get("/sell/inventory/v1/offer/{offerId}")
async def proxy_get_offer(offerId: str, request: Request):
    return await _proxy(request, "GET", f"/sell/inventory/v1/offer/{offerId}")

@router.put("/sell/inventory/v1/offer/{offerId}")
async def proxy_put_offer(offerId: str, request: Request, contentLanguage: str = "en-US"):
    return await _proxy(
        request, "PUT", f"/sell/inventory/v1/offer/{offerId}",
        inject_headers={"Content-Language": contentLanguage}
    )

@router.post("/sell/inventory/v1/offer/{offerId}/publish")
async def proxy_publish_offer(offerId: str, request: Request):
    return await _proxy(request, "POST", f"/sell/inventory/v1/offer/{offerId}/publish")

# ---------- Account policies ----------
@router.get("/sell/account/v2/payment_policy")
async def proxy_list_payment_policies(request: Request):
    return await _proxy(request, "GET", "/sell/account/v2/payment_policy")

@router.get("/sell/account/v2/return_policy")
async def proxy_list_return_policies(request: Request):
    return await _proxy(request, "GET", "/sell/account/v2/return_policy")

@router.get("/sell/account/v2/fulfillment_policy")
async def proxy_list_fulfillment_policies(request: Request):
    return await _proxy(request, "GET", "/sell/account/v2/fulfillment_policy")

# ---------- Fulfillment (orders) ----------
@router.get("/sell/fulfillment/v1/order")
async def proxy_search_orders(request: Request):
    return await _proxy(request, "GET", "/sell/fulfillment/v1/order")

# ---------- Browse (comps) ----------
@router.get("/browse/search")
async def proxy_browse_search(request: Request, q: str, limit: int = 10, fieldgroups: str | None = None):
    # Builder can't send the header; we inject it here
    inject = {"X-EBAY-C-MARKETPLACE-ID": "EBAY_US"}
    return await _proxy(request, "GET", "/buy/browse/v1/item_summary/search", inject_headers=inject)

# --- register router without disturbing your existing app/routes ---
try:
    app.include_router(router)  # if `app` already exists in your file
except NameError:
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
# ---------- END PROXY SECTION ----------
