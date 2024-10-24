from fastapi import FastAPI, HTTPException, Request
import mysql.connector
from passlib.context import CryptContext
from pydantic import BaseModel

from DB_Interface import register_user

app = FastAPI()

@app.post("/register")
async def receive_data(request: Request):
    user_data = await request.json()  # Get JSON data from request
    register_user(user_data)  # Call the separate function with the data
    return {"message": "User registered successfully"}

