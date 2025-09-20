from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
import os, uuid, base64, requests, urllib.parse
from pydantic import BaseModel
# eBay OAuth configuration
EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET")
EBAY_RUNAME = os.getenv("EBAY_RUNAME")


app = FastAPI(title="PackFit", version="0.1.0")

# --- Health check route ---
@app.get("/ping")
def ping():
    return {"message": "pong"}

# --- Placeholder PackFit route ---
class PackFitRequest(BaseModel):
    itemType: str
    sizeLabel: str = "M"
    weightOz: float = 0

@app.post("/packfit/estimate")
def estimate_packfit(request: PackFitRequest):
    # right now, it just echoes back what you send
    return {
        "chosenPackage": "Poly 10x13",
        "inputs": request.dict(),
        "note": "This is a stub — proves routing works!"
    }


@app.get("/ebay/login")
def ebay_login():
    """Redirect user to eBay’s OAuth authorization page."""
    state = str(uuid.uuid4())
    scopes = [
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.account",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
    ]
    params = {
        "client_id": EBAY_CLIENT_ID,
        "redirect_uri": EBAY_RUNAME,
        "response_type": "code",
        "state": state,
        "scope": " ".join(scopes),
    }
    auth_url = "https://auth.ebay.com/oauth2/authorize?" + urllib.parse.urlencode(params)
    response = RedirectResponse(auth_url)
    response.set_cookie(key="ebay_oauth_state", value=state, httponly=True, samesite="lax")
    return response

@app.get("/ebay/callback")
def ebay_callback(request: Request, code: str = "", state: str = ""):
    """Handle eBay OAuth callback, exchange code for access + refresh tokens."""
    saved_state = request.cookies.get("ebay_oauth_state")
    if not saved_state or state != saved_state:
        return JSONResponse({"error": "invalid_state"}, status_code=400)
    basic_token = base64.b64encode(f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {basic_token}",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": EBAY_RUNAME,
    }
    token_res = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers=headers,
        data=data,
    )
    if not token_res.ok:
        return JSONResponse({"error": f"token_exchange_failed: {token_res.status_code}", "details": token_res.text}, status_code=500)
    return JSONResponse(token_res.json())
