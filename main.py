import base64
import qrcode
from io import BytesIO
from fastapi import FastAPI, HTTPException, Query, Request
import json
from azure.storage.blob import BlobServiceClient, BlobClient

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from DB_Interface import add_friend2, get_friends, get_profile_data, insert_card_data, login_user, register_user, remove_friend, update_profile

app = FastAPI()

connection_string = "DefaultEndpointsProtocol=https;AccountName=designations;AccountKey=7TGa2pK+6Do7Ehu02h0cqY7BJAQS5AfTEzzvxhLU3wp7uDNVME37yFYJYCHJbCOYy0FQJkOJsFKZ+AStnW7WFQ==;EndpointSuffix=core.windows.net"  # Get this from Azure Portal
container_name = "designations-list"
blob_name = "designations.json"

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

@app.get("/get-designations")
async def get_designations():
    # Download the blob
    download_stream = blob_client.download_blob()
    json_data = download_stream.readall().decode('utf-8')

    # Parse JSON data
    designations = json.loads(json_data)

    return designations

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
    logging.info("Profile data endpoint hit")
    profile_data = get_profile_data(data)
    logging.info("Profile data endpoint after function call")
    return profile_data

@app.get("/get-qr")
async def qrGenerator(data: int = Query(...)):
    logging.info("QR data endpoint hit")
    profile_data = get_profile_data(data)
    logging.info("Profile data function called")
    json_data = json.dumps(profile_data)
    logging.info("json data formed")
    qr_img = qrcode.make(json_data)
    logging.info("QR formed")
    buffered = BytesIO()
    logging.info("BytesIO call")
    qr_img.save(buffered, format="PNG")
    logging.info("QR saved")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    logging.info("QR transformed to base64")
    
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

@app.get("/get-friend")
async def profile(data: int = Query(...)):
    get_fnd_data = get_friends(data)
    return get_fnd_data

@app.get("/test")
async def test():
    return {"Test": "Working"}

@app.post("/update-profile")
async def update_profile_endpoint(request: Request):
    try:
        profile_data = await request.json()
        logging.info("Received profile data:", profile_data)  # Debugging
        
        result = update_profile(profile_data)
        
        return result
    
    except Exception as e:
        logging.error("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")

@app.post("/store-card")
async def register(request: Request):
    try:
        card_data = await request.json()
        print("Received user data:", card_data)  # Debugging
        insert_card_data(card_data)
        return {"message": "Card stored successfully"}
    except Exception as e:
        print("Error:", str(e))  # Debugging
        raise HTTPException(status_code=400, detail=f"Bad request: {str(e)}")