from fastapi import FastAPI, HTTPException, Query, Request
import mysql.connector
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
async def login(data: int = Query(...)):
    profile_data = get_profile_data(data)
    return profile_data
