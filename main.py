from fastapi import FastAPI, HTTPException, Query, Request
import mysql.connector
from passlib.context import CryptContext
from pydantic import BaseModel

from DB_Interface import get_profile_data, login_user, register_user

app = FastAPI()

@app.post("/register")
async def register(request: Request):
    user_data = await request.json()
    register_user(user_data)
    return {"message": "User registered successfully"}

@app.post("/login")
async def login(request: Request):
    user_data = await request.json()
    response = login_user(user_data)
    return response

@app.get("/profile-data")
async def login(data: int = Query(...)):
    profile_data = get_profile_data(data)
    return profile_data