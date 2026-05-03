import os
import requests
from fastapi import FastAPI, HTTPException, Header

app = FastAPI()

DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsInN2IjoiMSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmcmVlbGFuY2VyLmNvbS9hdXRoIiwiaWF0IjoxNzc3Nzc3MjIzLCJkZXZpY2VfaWQiOiJDWTV2NjhzOW03RWxZSURmVWlZZmpwODVKMTVSNjBxKyIsInR5cGUiOiJkZXZpY2UtdG9rZW4ifQ.rsoaIloLebId04EjlbPJXLQSOBJm2uX9eM4jzOQq5ss"

PROXY_URL  = os.environ.get("PROXY_URL", "")
API_SECRET = os.environ.get("API_SECRET", "changeme")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/fl-login")
async def fl_login(body: dict, x_api_secret: str = Header(None)):
    if x_api_secret != API_SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")

    email    = body.get("email")
    password = body.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="missing fields")

    proxies = None  # Sin proxy, usar IP de Railway directamente

    try:
        res = requests.post(
            "https://www.freelancer.com/ajax-api/auth/login.php?compact=true&new_errors=true&new_pools=true",
            headers={
                "Content-Type":  "application/x-www-form-urlencoded",
                "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Origin":        "https://www.freelancer.com",
                "Referer":       "https://www.freelancer.com/login",
                "Accept":        "application/json",
            },
            data={
                "user":         email,
                "password":     password,
                "device_token": DEVICE_TOKEN,
            },
            proxies=proxies,
            timeout=15,
        )
        data = res.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    if data.get("status") != "success":
        raise HTTPException(status_code=401, detail=data)

    print("FL response:", data)

    if "token" not in data.get("result", {}):
        raise HTTPException(status_code=502, detail={"fl_response": data})

    fl_token   = data["result"]["token"]
    fl_user_id = str(data["result"]["user"])

    fl_username = None
    try:
        pr = requests.get(
            f"https://www.freelancer.com/api/users/0.1/users/{fl_user_id}/?compact=true",
            headers={
                "freelancer-auth-v2": f"{fl_user_id};{fl_token}",
                "User-Agent": "Mozilla/5.0",
            },
            proxies=proxies,
            timeout=10,
        )
        fl_username = pr.json().get("result", {}).get("username")
    except Exception:
        pass

    return {
        "ok":          True,
        "fl_token":    fl_token,
        "fl_user_id":  fl_user_id,
        "fl_username": fl_username,
    }
