
import psutil
import json
import time
from threading import Thread

def check_for_cheat_engine():
    cheat_processes = ['cheatengine', 'cheat engine', 'ce']
    
    while True:
        for proc in psutil.process_iter(['name']):
            try:
                for cheat in cheat_processes:
                    if cheat in proc.info['name'].lower():
                        return proc.info['name']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(5)

def ban_user(userid):
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
            
        for user in users['users']:
            if user['userid'] == userid:
                user['banned'] = True
                break
                
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error banning user: {str(e)}")
        return False

def start_anti_cheat(userid):
    def monitor():
        detected = check_for_cheat_engine()
        if detected:
            print(f"Cheat Engine detected: {detected}")
            ban_user(userid)
            
    Thread(target=monitor, daemon=True).start()
