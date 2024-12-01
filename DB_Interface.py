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
        query_users = """INSERT INTO Users (password, common_name, phone_number) 
                         VALUES (%s, %s, %s)"""
        cursor.execute(query_users, (hashed_password, user_data['common_name'], user_data['phone_number']))
        user_id = cursor.lastrowid  # Get the user_id of the newly created user

        # Insert into Profiles table with default values for optional fields
        query_profiles = """INSERT INTO Profiles (user_id, profile_title, primary_phone, secondary_phone, 
                              email1, email2, address1, address2, company_name, city, pincode, country) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_profiles, (
            user_id, 
            user_data['profile_title'], 
            user_data['primary_phone'], 
            user_data.get('secondary_phone'),  # Optional field
            user_data['email1'], 
            user_data.get('email2'),  # Optional field
            user_data['address1'], 
            user_data.get('address2', ''),  # Optional field
            user_data['company_name'], 
            user_data['city'], 
            user_data['pincode'], 
            user_data['country']
        ))
        
        connection.commit()
    
    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
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
                u.user_id,
                u.common_name,
                p.profile_id,
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
            "user_id": db_data['user_id'],
            "common_name": db_data['common_name'],
            "profile_id": db_data['profile_id'],
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

def add_friend(profile_id1: int, profile_id2: int):
    if profile_id1 == profile_id2:
        print("A profile cannot friend itself.")
        return{"message":"A profile cannot friend itself."}

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Check if profiles belong to the same user
        cursor.execute(
            """
            SELECT user_id FROM profiles WHERE profile_id = %s
            """, (profile_id1,)
        )
        user_id1 = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT user_id FROM profiles WHERE profile_id = %s
            """, (profile_id2,)
        )
        user_id2 = cursor.fetchone()[0]

        if user_id1 == user_id2:
            print("Profiles from the same user cannot be friends.")
            return {"message":"Profiles from the same user cannot be friends."}

        # Ensure the friendship doesn't already exist
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM friends
            WHERE (profile_id1 = %s AND profile_id2 = %s)
               OR (profile_id1 = %s AND profile_id2 = %s)
            """,
            (profile_id1, profile_id2, profile_id2, profile_id1)
        )
        exists = cursor.fetchone()[0]

        if exists:
            print("These profiles are already friends.")
            return {"message":"These profiles are already friends."}

        # Insert the friendship
        cursor.execute(
            """
            INSERT INTO friends (profile_id1, profile_id2)
            VALUES (%s, %s)
            """,
            (profile_id1, profile_id2)
        )
        connection.commit()
        print("Friend added successfully.")
        return{"message":"Friend added successfully"}

    except mysql.connector.Error as err:
        print("Error: ", err)
    finally:
        cursor.close()
        connection.close()

def remove_friend(profile_id1: int, profile_id2: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM friends
            WHERE (profile_id1 = %s AND profile_id2 = %s)
               OR (profile_id1 = %s AND profile_id2 = %s)
            """,
            (profile_id1, profile_id2, profile_id2, profile_id1)
        )
        connection.commit()

        if cursor.rowcount > 0:
            print("Friend removed successfully.")
            return{"message":"Friend removed successfully"}
        else:
            print("Friendship does not exist.")
            return{"message":"You are not friends"}

    except mysql.connector.Error as err:
        print("Error: ", err)
    finally:
        cursor.close()
        connection.close()

def get_friends(profile_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
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
            """,
            (profile_id, profile_id, profile_id)
        )
        friends = cursor.fetchall()
        friend_ids = [row[0] for row in friends]
        
        print("Friends found:", friend_ids)
        return friend_ids

    except mysql.connector.Error as err:
        print("Error: ", err)
        return []
    finally:
        cursor.close()
        connection.close()

def get_friends_with_details(profile_id: int):
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
        print("Error fetching friends:", e)
        raise
    finally:
        cursor.close()
        connection.close()
