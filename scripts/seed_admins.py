import os
import sys

# Add the project root to the Python path so we can import 'bhv'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bhv.db import init_db, create_user, get_user_by_email
from werkzeug.security import generate_password_hash

def seed_admins():
    print("Seeding initial admin accounts...")
    
    # Initialize DB (TinyDB/Mongo depending on env)
    app_db = init_db()
    
    admins_to_create = [
        {"email": "admin1@example.com", "password": "AdminPassword123!"},
        {"email": "admin2@example.com", "password": "AdminPassword456!"}
    ]

    for admin in admins_to_create:
        email = admin["email"]
        password = admin["password"]
        
        # Check if already exists
        if get_user_by_email(email):
            print(f"User {email} already exists. Skipping.")
            continue
            
        print(f"Creating admin user: {email}")
        pw_hash = generate_password_hash(password)
        create_user(email, pw_hash, role='admin')
        
    print("\n✅ Admin seeding complete!")
    print("\n--- Next Steps for adding future admins ---")
    print("If you want to add more admins in the future, you can either:")
    print("1. Modify this script `scripts/seed_admins.py` with the new emails/passwords and re-run it.")
    print("2. Or directly use the python terminal by running:")
    print("   >>> from werkzeug.security import generate_password_hash")
    print("   >>> from bhv.db import init_db, create_user")
    print("   >>> init_db()")
    print("   >>> create_user('newadmin@example.com', generate_password_hash('TheirPassword'), role='admin')\n")

if __name__ == "__main__":
    seed_admins()
