print (" [+] Loading basics...")
import os
import json
import urllib
import requests
import io
import bcrypt
import copy

if os.name == 'nt':
    os.system("color")
    os.system("title Social Wars Server")
else:
    import sys
    sys.stdout.write("\x1b]2;Social Wars Server\x07")

print (" [+] Loading game config...")
from get_game_config import get_game_config

print (" [+] Loading players...")
from get_player_info import get_player_info, get_neighbor_info
from sessions import load_saves, load_static_villages, load_quests, all_saves_userid, all_saves_info, save_info, new_village, fb_friends_str
load_saves()
print (" [+] Loading static villages...")
load_static_villages()
print (" [+] Loading quests...")
load_quests()

print (" [+] Loading auction house data...")
from auctions import AuctionHouse
auction_house = AuctionHouse()

print (" [+] Loading server...")
from flask import Flask, render_template, send_from_directory, request, redirect, session, send_file
from flask_socketio import SocketIO, emit
from flask.debughelpers import attach_enctype_error_multidict
from command import command
from engine import timestamp_now
from version import version_name
from bundle import ASSETS_DIR, STUB_DIR, TEMPLATES_DIR, BASE_DIR
from constants import Quests
from bundle import SAVES_DIR

__initial_village = {
    "playerInfo": {
        "pid": 0,
        "name": "New Player"
    },
    "maps": [
        {
            "timestamp": 0
        }
    ]
    # Add other initial village data here...
}


host = '0.0.0.0'  
port = 5055

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder='assets')
socketio = SocketIO(app, cors_allowed_origins="*")

print (" [+] Configuring server routes...")

##########
# ROUTES #
##########

__STATIC_ROOT = "/static/socialwars"
__DYNAMIC_ROOT = "/dynamic/menvswomen/srvsexwars"

## PAGES AND RESOURCES

from anti_cheat import start_anti_cheat

@app.route("/", methods=['GET'])
def login():
    session.pop('USERID', default=None)
    session.pop('GAMEVERSION', default=None)
    load_saves()
    saves_info = all_saves_info()
    return render_template("login.html", saves_info=saves_info, version=version_name)

@app.route("/login", methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        return "Email and password required", 400

    with open('users.json', 'r') as f:
        users = json.load(f)
        for user in users['users']:
            if user['email'].lower() == email.lower():
                # Check banned status before password validation
                if user.get('banned') == True:
                    return "Account has been banned", 403

                if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    # Double check ban status before creating session
                    if user.get('banned') == True:
                        return "Account has been banned", 403
                    session['USERID'] = user['userid']
                    session['GAMEVERSION'] = request.form.get('GAMEVERSION', "Basesec_1.5.4.swf")
                    return redirect("/play.html")

    return "Invalid email or password", 401

@app.route("/play.html")
def play():
    if 'USERID' not in session:
        return redirect("/")
    if 'GAMEVERSION' not in session:
        return redirect("/")

    if session['USERID'] not in all_saves_userid():
        return redirect("/")

    # Check if user is banned
    with open('users.json', 'r') as f:
        users = json.load(f)
        for user in users['users']:
            if user['userid'] == session['USERID'] and user.get('banned') == True:
                session.clear()
                return redirect("/banned")

    USERID = session['USERID']
    GAMEVERSION = session['GAMEVERSION']
    print("[PLAY] USERID:", USERID)
    print("[PLAY] GAMEVERSION:", GAMEVERSION)
    return render_template("play.html", save_info=save_info(USERID), serverTime=timestamp_now(), friendsInfo=fb_friends_str(USERID), version=version_name, GAMEVERSION=GAMEVERSION, SERVERIP=host, SERVERPORT=port)

@app.route("/new.html")
def new():
    return render_template("register.html", version=version_name)

@app.route("/register", methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    username = request.form.get('username')
    profile_pic = request.form.get('profile_pic')

    # Input validation 
    if not email or not password or not username:
        return "All fields are required", 400

    # Load users
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {"users": []}
    except json.JSONDecodeError:
        print("Error: users.json is corrupted")
        return "Server error", 500

    # Check if email exists
    for user in users['users']:
        if user['email'].lower() == email.lower():
            return "Email already exists", 400

    # Create new village
    try:
        userid = new_village(username)
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    except Exception as e:
        print("Error creating village:", str(e))
        return "Error creating player profile", 500

    # Add new user 
    users['users'].append({
        'email': email,
        'password': hashed.decode('utf-8'),
        'userid': userid,
        'username': username,
        'profile_pic': profile_pic,
        'banned': False
    })

    # Save users
    try:
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print("Error saving users:", str(e))
        return "Error saving user data", 500

    # Set session
    session['USERID'] = userid
    session['GAMEVERSION'] = "Basesec_1.5.4.swf"
    return redirect("/play.html")
    # Input validation 
    if not email or not password or not username:
        return "All fields are required", 400

    # Load users
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {"users": []}
    except json.JSONDecodeError:
        print("Error: users.json is corrupted")
        return "Server error", 500

        # Check if email exists
        for user in users['users']:
            if user['email'].lower() == email.lower():
                return "Email already exists", 400

        # Create new village
        try:
            userid = new_village(username)
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        except Exception as e:
            print("Error creating village:", str(e))
            return "Error creating player profile", 500

        # Add new user 
        users['users'].append({
            'email': email,
            'password': hashed.decode('utf-8'),
            'userid': userid,
            'username': username,
            'profile_pic': profile_pic,
            'banned': False
        })

        # Save users
        try:
            with open('users.json', 'w') as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            print("Error saving users:", str(e))
            return "Error saving user data", 500

        # Set session
        session['USERID'] = userid
        session['GAMEVERSION'] = "Basesec_1.5.4.swf"
        return redirect("/play.html")

    except Exception as e:
        print("Registration error:", str(e))
        return "Error during registration", 500

@app.route("/crossdomain.xml")
def crossdomain():
    return send_from_directory(STUB_DIR, "crossdomain.xml")

@app.route("/img/<path:path>")
def images(path):
    return send_from_directory(TEMPLATES_DIR + "/img", path)


@app.route("/avatars/<path:path>")
def avatars(path):
    return send_from_directory(TEMPLATES_DIR + "/avatars", path)

@app.route("/css/<path:path>")
def css(path):
    return send_from_directory(TEMPLATES_DIR + "/css", path)

## GAME STATIC

@app.route(__STATIC_ROOT + "/<path:path>")
def static_assets_loader(path):
    try:
        return send_from_directory(ASSETS_DIR, path)
    except Exception as e:
        print(f"Error serving static file {path}: {str(e)}")
        return "", 404

## GAME DYNAMIC

@app.route(__DYNAMIC_ROOT + "/track_game_status.php", methods=['POST'])
def track_game_status_response():
    status = request.values['status']
    installId = request.values['installId']
    user_id = request.values['user_id']

    # print(f"track_game_status: status={status}, installId={installId}, user_id={user_id}. --", request.values)
    print(f"[STATUS] USERID {user_id}: {status}")
    return ("", 200)

@app.route(__DYNAMIC_ROOT + "/get_game_config.php")
def get_game_config_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']

    # print(f"get_game_config: USERID: {USERID}. --", request.values)
    print(f"[CONFIG] USERID {USERID}.")
    return get_game_config()

@app.route(__DYNAMIC_ROOT + "/get_player_info.php", methods=['POST'])
def get_player_info_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']

    user = request.values['user'] if 'user' in request.values else None
    client_id = int(request.values['client_id']) if 'client_id' in request.values else None
    map = int(request.values['map']) if 'map' in request.values else None

    # print(f"get_player_info: USERID: {USERID}. --", request.values)

    # Current Player
    if user is None:
        print(f"[PLAYER INFO] USERID {USERID}.")
        return (get_player_info(USERID), 200)
    # General Mike
    elif user in ["100000030","100000031"]:
        print(f"[VISIT] USERID {USERID} visiting General Mike ({user}).")
        return (get_neighbor_info("100000030", map), 200)
    # Quest Maps
    elif user.startswith("100000"):
        print(f"[QUEST] USERID {USERID} loading", Quests.QUEST[user] if user in Quests.QUEST else "?", f"({user}).")
        return (get_neighbor_info(user, map), 200)
    # Static Neighbours
    else:
        print(f"[VISIT] USERID {USERID} visiting user: {user}.")
        return (get_neighbor_info(user, map), 200)

## AUCTION HOUSE

@app.route(__DYNAMIC_ROOT + "/bets/get_bets_list.php", methods=['POST'])
def get_bets_list():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']
    data = request.values['data']

    if not data.startswith("{"):
        data = data[65:]
    
    data = json.loads(data)
    user_id = data["user_id"]
    level = data["level"]

    bets = auction_house.get_auctions(user_id, level)
    for bet in bets:
        bet["isPrivate"] = 0
        bet["isWinning"] = 0
        bet["won"] = 0
        bet["finished"] = 0

    r = {}
    r["result"] = "success"
    r["data"] = {"bets": bets}

    response = json.dumps(r)
    return (response, 200)

@app.route(__DYNAMIC_ROOT + "/bets/get_bet_detail.php", methods=['POST'])
def get_bet_detail():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']
    data = request.values['data']
    
    if not data.startswith("{"):
        data = data[65:]
    
    data = json.loads(data)
    uuid = data["uuid"]
    checkFinish = 0
    if "checkFinish" in data:
        checkFinish = data["checkFinish"]

    bet = auction_house.get_auction_detail(USERID, uuid, checkFinish)

    print(f"Get bet details for BET UUID {uuid}")

    r = {}
    r["result"] = "success"
    r["data"] = bet

    return (json.dumps(r), 200)

@app.route(__DYNAMIC_ROOT + "/bets/create_auction.php", methods=['POST']) 
def create_auction():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']
    data = request.values['data']

    if not data.startswith("{"):
        data = data[65:]
    
    data = json.loads(data)
    unit_id = data["unit_id"]
    price = data["price"]
    level = data.get("level", 1)

    auction_house.create_auction(USERID, unit_id, price, level)

    r = {}
    r["result"] = "success" 
    r["data"] = {"auctionResult": "OK"}

    return (json.dumps(r), 200)

@app.route(__DYNAMIC_ROOT + "/bets/set_bet.php", methods=['POST'])
def set_bet():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']
    data = request.values['data']

    if not data.startswith("{"):
        data = data[65:]
    
    data = json.loads(data)
    uuid = data["uuid"]
    bet_amount = data["bet"]
    bet_round = data["round"]

    auction_house.set_bet(USERID, uuid, bet_amount, bet_round)

    r = {}
    r["result"] = "success"
    r["data"] = {
        "betResult": "OK"
    }

    return (json.dumps(r), 200)

@app.route(__DYNAMIC_ROOT + "/sync_error_track.php", methods=['POST'])
def sync_error_track_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']

    # print(f"sync_error_track: USERID: {USERID}. --", request.values)
    return ("", 200)

@app.route("/null")
def flash_sync_error_response():
    sp_ref_cat = request.values['sp_ref_cat']

    if sp_ref_cat == "flash_sync_error":
        reason = "reload On Sync Error"
    elif sp_ref_cat == "flash_reload_quest":
        reason = "reload On End Quest"
    elif sp_ref_cat == "flash_reload_attack":
        reason = "reload On End Attack"

    print("flash_sync_error", reason, ". --", request.values)
    return redirect("/play.html")

@app.route(__DYNAMIC_ROOT + "/command.php", methods=['POST'])
def command_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']

    # print(f"command: USERID: {USERID}. --", request.values)

    data_str = request.values['data']
    data_hash = data_str[:64]
    assert data_str[64] == ';'
    data_payload = data_str[65:]
    data = json.loads(data_payload)

    command(USERID, data)

    return ({"result": "success"}, 200)

# Used by Player's World and Alliance buttons
# I added this so the error message stops appearing
@app.route(__DYNAMIC_ROOT + "/leaderboard/", methods=['GET'])
def leaderboard():
    try:
        saves_list = all_saves_info()
        leaderboard_data = []
        
        for save in saves_list:
            leaderboard_data.append({
                "user_id": save["userid"],
                "name": save["name"],
                "level": save.get("level", 1),
                "score": save.get("score", 0),
                "wins": save.get("wins", 0)
            })
            
        # Sort by score
        leaderboard_data.sort(key=lambda x: x["score"], reverse=True)
        
        response = {
            "result": "success",
            "data": {
                "leaderboard": leaderboard_data
            }
        }
        return response, 200
    except Exception as e:
        print(f"Error getting leaderboard: {str(e)}")
        return {"result": "error", "message": "Failed to get leaderboard"}, 500


@app.route(__DYNAMIC_ROOT + "/send_friend_request", methods=['POST'])
def send_friend_request():
    try:
        USERID = request.values['USERID']
        target_id = request.values['target_id']
        
        target_save = session(target_id)
        if "friend_requests" not in target_save:
            target_save["friend_requests"] = []
            
        if USERID not in target_save["friend_requests"]:
            target_save["friend_requests"].append(USERID)
            
        return {"result": "success"}, 200
    except Exception as e:
        return {"result": "error", "message": str(e)}, 500

@app.route(__DYNAMIC_ROOT + "/accept_friend_request", methods=['POST']) 
def accept_friend_request():
    try:
        USERID = request.values['USERID']
        friend_id = request.values['friend_id']
        
        player_save = session(USERID)
        if "friends" not in player_save:
            player_save["friends"] = []
        if "friend_requests" not in player_save:
            player_save["friend_requests"] = []
            
        if friend_id in player_save["friend_requests"]:
            player_save["friend_requests"].remove(friend_id)
            if friend_id not in player_save["friends"]:
                player_save["friends"].append(friend_id)
                
            # Add friendship for other player too
            friend_save = session(friend_id)
            if "friends" not in friend_save:
                friend_save["friends"] = []
            if USERID not in friend_save["friends"]:
                friend_save["friends"].append(USERID)
                
        return {"result": "success"}, 200
    except Exception as e:
        return {"result": "error", "message": str(e)}, 500

@app.route("/banned")
def banned():
    return render_template("banned.html")

########
# ADMIN #
########

def is_admin(userid):
    return userid == '3ea4302e-8297-4fdb-a312-c0b9589e0571'  # Only allow specific admin

@app.route("/admin/users")
def admin_users():
    if 'USERID' not in session or not is_admin(session['USERID']):
        return "Unauthorized", 403
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
        return render_template("admin_users.html", users=users['users'])
    except Exception as e:
        return str(e), 500

@app.route("/admin/auction")
def admin_auction():
    if 'USERID' not in session or not is_admin(session['USERID']):
        return "Unauthorized", 403
    return render_template("admin_auction.html", auctions=auction_house.config["auctions"])

@app.route("/admin/auction/add", methods=['POST'])
def admin_auction_add():
    if 'USERID' not in session or not is_admin(session['USERID']):
        return "Unauthorized", 403
        
    unit_id = int(request.form['unit_id'])
    level = int(request.form['level'])
    price = int(request.form['price'])
    interval = int(request.form['interval'])
    
    uuid = str(len(auction_house.config["auctions"]) + 1)
    new_auction = {
        "uuid": uuid,
        "unit": unit_id,
        "level": level,
        "interval": interval,
        "price": price,
        "priceIncrement": int(price * 0.1),
        "betPrice": 2
    }
    
    auction_house.config["auctions"].append(new_auction)
    auction_house._write_config()
    return redirect("/admin/auction")

@app.route("/admin/auction/delete/<uuid>", methods=['POST'])
def admin_auction_delete(uuid):
    if 'USERID' not in session or not is_admin(session['USERID']):
        return "Unauthorized", 403
        
    auction_house.config["auctions"] = [a for a in auction_house.config["auctions"] if a["uuid"] != uuid]
    auction_house._write_config()
    return redirect("/admin/auction")

########
# MAIN #
########

print (" [+] Running server...")

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('send_message')
def handle_message(data):
    print(f"Message received: {data}")
    emit('receive_message', {
        'user': data['user'],
        'message': data['message']
    }, broadcast=True)

def ban_user(userid):
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)

        for user in users['users']:
            if user['userid'] == userid:
                user['banned'] = True
                # Reset user data to initial state
                save_file = os.path.join(SAVES_DIR, f"{userid}.save.json")
                if os.path.exists(save_file):
                    initial = copy.deepcopy(__initial_village)
                    initial["playerInfo"]["pid"] = userid
                    initial["playerInfo"]["name"] = user['username']
                    initial["playerInfo"]["pic"] = user.get('profile_pic', '/static/socialwars/images/en/soldado_regalos.png')
                    initial["maps"][0]["timestamp"] = timestamp_now()
                    with open(save_file, 'w') as f:
                        json.dump(initial, f, indent=4)
                break

        with open('users.json', 'w') as f:
            json.dump(users, f, indent=2)

        return True
    except Exception as e:
        print(f"Error banning user: {str(e)}")
        return False

if __name__ == '__main__':
    app.secret_key = 'SECRET_KEY'
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)