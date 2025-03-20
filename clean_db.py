
import json
import os

def clean_users():
    try:
        # Load users
        with open('users.json', 'r') as f:
            users = json.load(f)
        
        # Filter users with existing save files
        valid_users = []
        for user in users['users']:
            save_path = f"saves/{user['userid']}.save.json"
            if os.path.exists(save_path):
                valid_users.append(user)
            else:
                print(f"Removing user {user['username']} (no save file)")
        
        # Save cleaned users list
        users['users'] = valid_users
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=2)
            
        print(f"Cleaned {len(users['users'])} users remain")
            
    except Exception as e:
        print(f"Error cleaning users: {str(e)}")

if __name__ == "__main__":
    clean_users()
