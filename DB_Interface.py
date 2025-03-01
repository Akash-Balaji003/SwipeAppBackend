from fastapi import HTTPException
import mysql.connector
from passlib.context import CryptContext
from pymysql import NULL

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_db_connection():
    return mysql.connector.connect(
        host="digivcard.mysql.database.azure.com",
        port=3306,
        username="digicard",
        password="Raviswaminathan123@",
        database="DigiVcard"
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
                              email1, email2, address1, company_name, city, pincode, country) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_profiles, (
            user_id, 
            user_data['profile_title'], 
            user_data['primary_phone'], 
            user_data.get('secondary_phone'),  # Optional field
            user_data['email1'],
            user_data.get('email2'),  # Optional field
            user_data['address1'], 
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

def add_friend2(profile_id1: int, profile_id2: int, remarks: str, location: str):
    if profile_id1 == profile_id2:
        print("A profile cannot friend itself.")
        return {"message": "A profile cannot friend itself."}

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
            return {"message": "Profiles from the same user cannot be friends."}

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
            return {"message": "These profiles are already friends."}

        # Insert the friendship along with remarks
        cursor.execute(
            """
            INSERT INTO friends (profile_id1, profile_id2, remarks, location)
            VALUES (%s, %s, %s, %s)
            """,
            (profile_id1, profile_id2, remarks, location)
        )
        connection.commit()
        return {"message": "Friend added successfully"}

    except mysql.connector.Error as err:
        print("Error: ", err)
        return {"message": f"Error: {err}"}

    finally:
        cursor.close()
        connection.close()

def update_profile(profile_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Update the Profiles table with the provided data
        query = """
        UPDATE Profiles
        SET 
            profile_title = %s,
            qualification = %s,
            designation = %s,
            company_name = %s,
            primary_phone = %s,
            secondary_phone = %s,
            email1 = %s,
            email2 = %s,
            address1 = %s,
            city = %s,
            pincode = %s,
            country = %s
        WHERE profile_id = %s
        """
        cursor.execute(query, (
            profile_data['profile_title'],
            profile_data['qualification'],
            profile_data['designation'],
            profile_data['company_name'],
            profile_data['primary_phone'],
            profile_data.get('secondary_phone'),  # Optional field
            profile_data['email1'],
            profile_data.get('email2'),  # Optional field
            profile_data['address1'],
            profile_data['city'],
            profile_data['pincode'],
            profile_data['country'],
            profile_data['profile_id']  # Using profile_id as the identifier
        ))

        connection.commit()
        return {"message": "Updated the profile successfully"}
    
    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def insert_card_data(card_data: dict):
    connection = get_db_connection()  # Replace with your DB connection function
    cursor = connection.cursor()

    try:
        # Insert into Cards table
        query_cards = """INSERT INTO Cards (
                            profile_id, name, card_designation, primary_phone, primary_email, 
                            title, user_qualification, company_name, secondary_phone, 
                            secondary_email, address, city, pincode, country, remarks
                         ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_cards, (
            card_data['profile_id'],
            card_data['name'],
            card_data.get('card_designation', None),  # Optional field
            card_data['primary_phone'],
            card_data['primary_email'],
            card_data['title'],
            card_data.get('user_qualification', None),  # Optional field
            card_data['company_name'],
            card_data.get('secondary_phone', None),  # Optional field
            card_data.get('secondary_email', None),  # Optional field
            card_data['address'],
            card_data['city'],
            card_data['pincode'],
            card_data['country'],
            card_data['remark']
        ))
        
        connection.commit()

    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def search_friends(profile_id: int, search_term: str):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Query to search for friends based on common_name, profile_title, or remarks
        query = """
        SELECT 
            CASE 
                WHEN f.profile_id1 = %s THEN f.profile_id2
                ELSE f.profile_id1
            END AS friend_profile_id,
            p.profile_title,
            u.common_name,
            f.remarks
        FROM friends f
        JOIN profiles p ON p.profile_id = 
            CASE 
                WHEN f.profile_id1 = %s THEN f.profile_id2
                ELSE f.profile_id1
            END
        JOIN users u ON u.user_id = p.user_id
        WHERE (f.profile_id1 = %s OR f.profile_id2 = %s)
          AND (
              u.common_name LIKE %s   -- Search in user's common name
              OR p.profile_title LIKE %s  -- Search in profile title
              OR f.remarks LIKE %s    -- Search in remarks
          )
        """
        
        # Execute the query with search term in all fields
        cursor.execute(query, (profile_id, profile_id, profile_id, profile_id, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        friends = cursor.fetchall()

        return friends
    
    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def get_cards(profile_id: int):
    connection = get_db_connection()  # Replace with your DB connection function
    cursor = connection.cursor(dictionary=True)  # Use dictionary=True for a dict result

    try:
        # SQL query to fetch all cards for the given profile_id
        query = """
        SELECT 
            card_id,
            name,
            title,
            company_name,
            remarks
        FROM Cards
        WHERE profile_id = %s
        """
        
        # Execute the query
        cursor.execute(query, (profile_id,))
        
        # Fetch all rows and return them
        cards = cursor.fetchall()
        return cards

    except mysql.connector.Error as err:
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def search_my_cards(profile_id: int, search_term: str):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # SQL query to search cards for the given profile_id and search_term
        query = """
        SELECT 
            c.card_id,
            c.profile_id,
            c.name,
            c.card_designation,
            c.primary_phone,
            c.primary_email,
            c.title,
            c.user_qualification,
            c.company_name,
            c.secondary_phone,
            c.secondary_email,
            c.address,
            c.city,
            c.pincode,
            c.country,
            c.remarks
        FROM Cards c
        JOIN profiles p ON c.profile_id = p.profile_id
        JOIN users u ON p.user_id = u.user_id
        WHERE c.profile_id = %s
          AND (
              c.title LIKE %s
              OR c.remarks LIKE %s
              OR c.name LIKE %s
          )
        """
        
        # Execute the query with the search term in all fields
        cursor.execute(query, (profile_id, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        cards = cursor.fetchall()

        return cards

    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")

    finally:
        cursor.close()
        connection.close()

def get_card_data(card_id: int):
    connection = get_db_connection()  # Replace with your DB connection function
    cursor = connection.cursor(dictionary=True)

    try:
        # Query to fetch card data for the specific card_id
        query = """
        SELECT 
            name, card_designation, primary_phone, primary_email,
            title, user_qualification, company_name, secondary_phone,
            secondary_email, address, city, pincode, country, remarks
        FROM Cards
        WHERE card_id = %s
        """
        
        cursor.execute(query, (card_id,))
        card_data = cursor.fetchone()  # Fetch a single record
        
        if not card_data:
            raise HTTPException(status_code=404, detail=f"Card with ID {card_id} not found")
        
        return card_data

    except mysql.connector.Error as err:
        print("Database error:", err)
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def insert_profile(user_id: int, profile_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Insert into Profiles table
        query_profiles = """INSERT INTO Profiles (user_id, profile_title, primary_phone, secondary_phone, 
                              email1, email2, address1, company_name, city, pincode, country, 
                              designation, qualification)  
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_profiles, (
            user_id, 
            profile_data['profile_title'], 
            profile_data['primary_phone'], 
            profile_data.get('secondary_phone'),  # Optional field
            profile_data['primary_email'], 
            profile_data.get('secondary_email'),  # Optional field
            profile_data['address'], 
            profile_data['company_name'], 
            profile_data['city'], 
            profile_data['pincode'], 
            profile_data['country'],
            profile_data.get('card_designation'),  # Optional field with default empty string
            profile_data.get('user_qualification')
        ))

        connection.commit()
    
    except mysql.connector.Error as err:
        connection.rollback()
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()

def check_account(user_data: dict):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Check for existing account based on phone number or email
        query = """
        SELECT phone_number
        FROM Users
        WHERE phone_number = %s
        """
        cursor.execute(query, (
            user_data['phone_number'],
        ))
        
        existing_user = cursor.fetchone()

        if existing_user:
            return {"message": "This number or email already has an account"}

        return {"message": "No account exists with the provided phone number or email."}
    
    except mysql.connector.Error as err:
        print("Database error:", err)  # Debugging
        raise HTTPException(status_code=400, detail=f"Database error: {err}")
    
    finally:
        cursor.close()
        connection.close()
