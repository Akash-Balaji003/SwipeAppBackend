from fastapi import HTTPException
import mysql.connector
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Akash003!",
        database="swipe"
    )

def hash_password(password: str):
    return pwd_context.hash(password)

def register_user(user_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Hash the password before storing it
    hashed_password = hash_password(user_data['password'])

    try:
        # Insert into Users table
        query_users = """INSERT INTO Users (username, password, common_name, phone_number) 
                         VALUES (%s, %s, %s, %s)"""
        cursor.execute(query_users, (user_data['username'], hashed_password, user_data['common_name'], user_data['phone_number']))
        user_id = cursor.lastrowid  # Get the user_id of the newly created user

        # Insert into Profiles table
        query_profiles = """INSERT INTO Profiles (user_id, profile_title, entity_name, primary_phone, secondary_phone, 
                              email1, email2, address1, address2, company_name, city, pincode, country) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_profiles, (user_id, user_data['profile_title'], user_data['entity_name'], user_data['primary_phone'],
                                        user_data.get('secondary_phone'), user_data['email1'], user_data.get('email2'),
                                        user_data['address1'], user_data.get('address2'), user_data['company_name'],
                                        user_data['city'], user_data['pincode'], user_data['country']))
        
        connection.commit()
    
    except mysql.connector.Error as err:
        connection.rollback()
        raise HTTPException(status_code=400, detail=f"Error: {err}")
    
    finally:
        cursor.close()
        connection.close()
