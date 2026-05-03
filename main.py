import os
import requests
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

app = FastAPI()

DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsInN2IjoiMSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmcmVlbGFuY2VyLmNvbS9hdXRoIiwiaWF0IjoxNzc3Nzc3MjIzLCJkZXZpY2VfaWQiOiJDWTV2NjhzOW03RWxZSURmVWlZZmpwODVKMTVSNjBxKyIsInR5cGUiOiJkZXZpY2UtdG9rZW4ifQ.rsoaIloLebId04EjlbPJXLQSOBJm2uX9eM4jzOQq5ss"

PROXY_USER = os.environ.get("PROXY_USER", "")
PROXY_PASS = os.environ.get("PROXY_PASS", "")
PROXY_HOST = "gate.decodo.com"
PROXY_PORT = "7000"
API_SECRET = os.environ.get("API_SECRET", "changeme")

class LoginRequest(BaseModel):
    email: str
    password: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/fl-login")
def fl_login(body: LoginRequest, x_api_secret: str = Header(None)):
    if x_api_secret != API_SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")

    proxies = None
    if PROXY_USER and PROXY_PASS:
        proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        proxies = {"http": proxy_url, "https": proxy_url}

    try:
        res = requests.post(
            "https://www.freelancer.com/ajax-api/auth/login.php?compact=true&new_errors=true&new_pools=true",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Origin": "https://www.freelancer.com",
                "Referer": "https://www.freelancer.com/login",
                "Accept": "application/json",
            },
            data={
                "user": body.email,
                "password": body.password,
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

    fl_token  = data["result"]["token"]
    fl_user_id = str(data["result"]["user"])

    # Obtener username
    fl_username = None
    try:
        profile_res = requests.get(
            f"https://www.freelancer.com/api/users/0.1/users/{fl_user_id}/?compact=true",
            headers={
                "freelancer-auth-v2": f"{fl_user_id};{fl_token}",
                "User-Agent": "Mozilla/5.0",
            },
            proxies=proxies,
            timeout=10,
        )
        profile_data = profile_res.json()
        fl_username = profile_data.get("result", {}).get("username")
    except Exception:
        pass

    return {
        "ok": True,
        "fl_token": fl_token,
        "fl_user_id": fl_user_id,
        "fl_username": fl_username,
    }
