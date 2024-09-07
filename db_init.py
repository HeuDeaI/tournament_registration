import sqlite3
import random
import string


# Create table
with sqlite3.connect('users.db') as connection:
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,        
        user_id INTEGER NOT NULL UNIQUE, 
        user_name TEXT NOT NULL,        
        team_number INTEGER NOT NULL CHECK(team_number >= 1 AND team_number <= 8),       
        is_captain INTEGER CHECK(is_captain IN (0, 1))     
    )
    ''')
    connection.commit()


import sqlite3
import random
import string

def random_string(length=8):
    """Generate a random string of fixed length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def insert_random_users(num_users=10):
    """Insert a specified number of random users into the users table."""
    with sqlite3.connect('users.db') as connection:
        cursor = connection.cursor()
        teams_with_captains = set()  # Track teams that already have a captain
        
        for _ in range(num_users):
            user_id = random.randint(1, 10000)  # Random user_id
            user_name = random_string()  # Random user_name
            team_number = random.randint(1, 8)  # Random team_number between 1 and 8
            
            if team_number not in teams_with_captains or random.choice([True, False]):
                is_captain = 1 if team_number not in teams_with_captains and random.choice([True, False]) else 0
                if is_captain:
                    teams_with_captains.add(team_number)  # Add team to the set if a captain is assigned
            else:
                is_captain = 0
            
            cursor.execute('''
                INSERT INTO users (user_id, user_name, team_number, is_captain)
                VALUES (?, ?, ?, ?)
            ''', (user_id, user_name, team_number, is_captain))
        
        connection.commit()

# Insert 10 random users
insert_random_users(10)


