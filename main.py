import base64
import qrcode
from io import BytesIO
from fastapi import FastAPI, HTTPException, Query, Request
import json
from passlib.context import CryptContext
from pydantic import BaseModel

from DB_Interface import get_profile_data, login_user, register_user

app = FastAPI()

@app.post("/register")
async def register(request: Request):
    try:
        user_data = await request.json()
        print("Received user data:", user_data)  # Debugging
        register_user(user_data)
        return {"message": "User registered successfully"}
    except Exception as e:
        print("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")

@app.post("/login")
async def login(request: Request):
    user_data = await request.json()
    response = login_user(user_data)
    return response

@app.get("/profile-data")
async def profile(data: int = Query(...)):
    profile_data = get_profile_data(data)
    return profile_data

@app.get("/get-qr")
async def qrGenerator(data: int = Query(...)):
    profile_data = get_profile_data(data)
    json_data = json.dumps(profile_data)
    qr_img = qrcode.make(json_data)

    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # Return the Base64 string as a JSON response
    return {"qr_code_base64": img_str}
    