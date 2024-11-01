from fastapi import HTTPException
import mysql.connector
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

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

def login_user(user_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Fetch results as dictionary

    try:
        # Check if user exists and retrieve profiles
        query = """
            SELECT u.user_id, u.password, u.common_name, u.phone_number, p.profile_id, p.profile_title
            FROM Users u
            LEFT JOIN Profiles p ON u.user_id = p.user_id
            WHERE u.phone_number = %s
        """
        cursor.execute(query, (user_data['phone_number'],))
        db_user_profiles = cursor.fetchall()

        if not db_user_profiles or not verify_password(user_data['password'], db_user_profiles[0]['password']):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Extract user info from the first result
        db_user = db_user_profiles[0]
        profile_ids = [profile['profile_id'] for profile in db_user_profiles]
        profile_titles = [profile['profile_title'] for profile in db_user_profiles]


        # Return user details along with profile_ids
        return {
            "user_id": db_user['user_id'],
            "Name": db_user['common_name'],
            "Mobile Number": db_user['phone_number'],
            "Profile IDs": profile_ids,
            "Profile Titles": profile_titles,
        }
    
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def get_profile_data(profileID: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # Fetch results as dictionary

    try:
        query = """
            SELECT 
                u.username,
                p.profile_title,
                p.primary_phone,
                p.secondary_phone,
                p.email1,
                p.email2,
                p.address1,
                p.address2,
                p.company_name,
                p.city,
                p.pincode,
                p.country
            FROM Profiles p
            JOIN Users u ON p.user_id = u.user_id
            WHERE p.profile_id = %s;
        """
        cursor.execute(query, (profileID,))
        db_data = cursor.fetchone()  # fetchone() since we expect only one result with a unique profile_id

        if db_data is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        return {
            "username": db_data['username'],
            "profile_title": db_data['profile_title'],
            "primary_phone": db_data['primary_phone'],
            "secondary_phone": db_data['secondary_phone'],
            "email1": db_data['email1'],
            "email2": db_data['email2'],
            "address1": db_data['address1'],
            "address2": db_data['address2'],
            "company_name": db_data['company_name'],
            "city": db_data['city'],
            "pincode": db_data['pincode'],
            "country": db_data['country'],
        }

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error: {err}")
    
    finally:
        cursor.close()
        connection.close()

