import base64
import qrcode
from io import BytesIO
from fastapi import FastAPI, HTTPException, Query, Request
import json
import mysql.connector
import aiomysql


from DB_Interface import add_friend2, get_friends, get_friends2, get_profile_data, login_user, register_user, remove_friend

app = FastAPI()

db_pool = None  # Declare a global variable for the connection pool


@app.on_event("startup")
async def startup_event():
    global db_pool
    db_pool = await aiomysql.create_pool(
        host='swipe-mysql-server.mysql.database.azure.com',
        port=3306,
        user='Swipeadmin',
        password='Swipeadmin123',
        db='swipe_schema',
        minsize=1,
        maxsize=10
    )


@app.on_event("shutdown")
async def shutdown_event():
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()

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

@app.get("/add-friend")
async def addFriend(data1: int = Query(...), data2: int = Query(...), remarks: str = Query(...)):
    add_friend_result = add_friend2(data1, data2, remarks)
    return add_friend_result

@app.get("/remove-friend")
async def removeFriend(data1: int = Query(...), data2: int = Query(...)):
    remove_friend_result = remove_friend(data1, data2)
    return remove_friend_result

@app.get("/get-friend-v2")
async def profile(data: int = Query(...)):
    get_fnd_data = get_friends2(data)
    return get_fnd_data

@app.get("/get-friend")
async def profile(data: int = Query(...)):
    async with db_pool.acquire() as connection:
        async with connection.cursor() as cursor:
            query = """
                SELECT users.username, users.common_name, user_profiles.profile_title 
                FROM user_profiles
                JOIN users ON user_profiles.user_id = users.id
                WHERE user_profiles.profile_id IN (%s, %s, %s, %s);
            """
            await cursor.execute(query, (data, data, data, data))
            result = await cursor.fetchall()
    return {"friends": result}

@app.get("/test")
async def test():
    return {"Test": "Working"}

