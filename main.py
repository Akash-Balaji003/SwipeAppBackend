import base64
import qrcode
from io import BytesIO
from fastapi import FastAPI, HTTPException, Query, Request
import json
import mysql.connector


from DB_Interface import add_friend2, get_friends, get_friends2, get_profile_data, login_user, register_user, remove_friend

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
    get_fnd_data = get_friend_test(data)
    return get_fnd_data

@app.get("/test")
async def test():
    return {"Test": "Working"}

def get_db_connection():
    return mysql.connector.connect(
        host="swipe-mysql-server.mysql.database.azure.com",
        port=3306,
        username="Swipeadmin",
        password="Swipeadmin123",
        database="swipe_schema"
    )

def get_friend_test(profile_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Use dictionary=True to return results as dicts

    try:
        query = """
            SELECT 
                CASE 
                    WHEN f.profile_id1 = %s THEN f.profile_id2
                    ELSE f.profile_id1
                END AS friend_profile_id,
                p.profile_title,
                u.common_name
            FROM friends f
            JOIN profiles p ON p.profile_id = 
                CASE 
                    WHEN f.profile_id1 = %s THEN f.profile_id2
                    ELSE f.profile_id1
                END
            JOIN users u ON u.user_id = p.user_id
            WHERE f.profile_id1 = %s OR f.profile_id2 = %s
        """
        cursor.execute(query, (profile_id, profile_id, profile_id, profile_id))
        friends = cursor.fetchall()

        print("Friends found:", friends)
        return friends

    except Exception as e:
        print("Database error:", e)
        print("Error fetching friends:", e)
        raise
    finally:
        cursor.close()
        connection.close()
