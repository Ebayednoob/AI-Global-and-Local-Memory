# main.py
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS 
import hashlib
import json
import time
import uuid 
from datetime import datetime, timezone 
from functools import wraps 
import os 
from werkzeug.utils import secure_filename 

# --- Configuration ---
API_KEY = "your_secret_api_key" # CRITICAL: This MUST match the 'Vault API Key' used by the GUI.
                                # If you generate a key in the GUI, update this value and restart the server.
UPLOAD_FOLDER = 'uploads' # For avatars (largely unused by current GUI)
DATA_STORE_FOLDER = 'data_store' # For memory and profile JSON files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # For avatar uploads

app = Flask(__name__)
CORS(app, resources={r"/*": { # Explicit CORS configuration
    "origins": "*",  # Allow all origins (for development)
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "X-API-KEY", "Authorization"]
}})

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DATA_STORE_FOLDER'] = DATA_STORE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB Max upload size

# --- Helper Functions for File Storage ---
def get_user_data_path(user_id):
    """Returns the path to the user's data directory."""
    return os.path.join(app.config['DATA_STORE_FOLDER'], user_id)

def get_user_profile_path(user_id):
    """Returns the path to the user's profile.json file (stores Merkle root)."""
    return os.path.join(get_user_data_path(user_id), 'profile.json')

def get_user_memories_path(user_id):
    """Returns the path to the user's memories directory."""
    return os.path.join(get_user_data_path(user_id), 'memories')

def get_memory_file_path(user_id, memory_id):
    """Returns the path to a specific memory's JSON file."""
    return os.path.join(get_user_memories_path(user_id), f"{memory_id}.json")

def ensure_dir_exists(path):
    """Ensures a directory exists, creating it if necessary."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def load_json_file(file_path, default_data=None):
    """Loads data from a JSON file. Returns default_data if file not found or error."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading JSON from {file_path}: {e}")
    return default_data if default_data is not None else {} # Default to empty dict

def save_json_file(file_path, data):
    """Saves data to a JSON file."""
    try:
        ensure_dir_exists(os.path.dirname(file_path))
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except IOError as e:
        print(f"Error saving JSON to {file_path}: {e}")
        return False

# --- User Profile Data Management (Backend: primarily for Merkle Root) ---
def get_or_initialize_user_profile(user_id):
    """
    Loads user profile (profile.json) from file, or initializes a new one.
    This file mainly stores the Merkle root for the user's memories on the backend.
    """
    user_base_dir = get_user_data_path(user_id)
    ensure_dir_exists(user_base_dir) # Ensure the base user directory (e.g., data_store/user123/) exists
    
    profile_path = get_user_profile_path(user_id)
    profile_data = load_json_file(profile_path)

    if not profile_data or "user_id" not in profile_data: # If file didn't exist or was empty/invalid
        profile_data = {
            "user_id": user_id,
            "merkle_root": None, 
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        if not save_json_file(profile_path, profile_data):
             print(f"CRITICAL: Failed to save initial profile for user {user_id}")
    return profile_data

def save_user_profile(user_id, profile_data):
    """Saves the user's profile.json data to file."""
    profile_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    profile_path = get_user_profile_path(user_id)
    return save_json_file(profile_path, profile_data)

# --- Memory Data Management ---
def get_all_memory_leaf_hashes(user_id):
    """Loads all memory leaf hashes for a user from their memory files."""
    memories_dir = get_user_memories_path(user_id)
    leaf_hashes = []
    if os.path.exists(memories_dir):
        for filename in os.listdir(memories_dir):
            if filename.endswith(".json"):
                memory_path = os.path.join(memories_dir, filename)
                memory_data = load_json_file(memory_path)
                if memory_data and "leaf_hash" in memory_data:
                    leaf_hashes.append(memory_data["leaf_hash"])
    return leaf_hashes

def update_user_merkle_root(user_id):
    """Recalculates and saves the Merkle root for a user's memories to their profile.json."""
    profile = get_or_initialize_user_profile(user_id) 
    leaf_hashes = get_all_memory_leaf_hashes(user_id)
    new_merkle_root = build_merkle_tree(leaf_hashes)
    profile["merkle_root"] = new_merkle_root
    save_user_profile(user_id, profile)
    return new_merkle_root

# --- Avatar Upload Helpers (unused by current GUI, kept for completeness) ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_user_avatar_dir(user_id):
    user_avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', user_id)
    ensure_dir_exists(user_avatar_path)
    return user_avatar_path

# --- Encryption/Decryption (Placeholder - NOT SECURE) ---
def encrypt_data(data_str, key):
    # print(f"Encrypting with key: {key[:5]}...") # Sensitive, comment out for production
    return f"encrypted_{data_str}" # Replace with real encryption

def decrypt_data(encrypted_data_str, key):
    # print(f"Decrypting with key: {key[:5]}...") # Sensitive, comment out for production
    if encrypted_data_str.startswith("encrypted_"):
        return encrypted_data_str[len("encrypted_"):] # Replace with real decryption
    return encrypted_data_str

# --- Merkle Tree Logic ---
def calculate_hash(data_str):
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

def build_merkle_tree(leaf_hashes):
    if not leaf_hashes: return None
    current_level_hashes = list(leaf_hashes) 
    while len(current_level_hashes) > 1:
        if len(current_level_hashes) % 2 != 0: current_level_hashes.append(current_level_hashes[-1]) 
        next_level = []
        for i in range(0, len(current_level_hashes), 2):
            next_level.append(calculate_hash(current_level_hashes[i] + current_level_hashes[i+1]))
        current_level_hashes = next_level
    return current_level_hashes[0] if current_level_hashes else None

# --- API Key Decorator ---
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Flask-CORS handles OPTIONS. This is for actual data requests.
        if request.headers.get('X-API-KEY') == API_KEY:
            return f(*args, **kwargs)
        else:
            print(f"Unauthorized attempt. Expected API Key: '{API_KEY}', Received: '{request.headers.get('X-API-KEY')}' from IP: {request.remote_addr}")
            return jsonify({"error": "Unauthorized. API key is missing or invalid."}), 401
    return decorated_function

# --- API Endpoints ---
@app.route('/')
def home():
    return f"Personal Memory Vault API is running! Expecting API Key in X-API-KEY header for protected routes: '{API_KEY}'"

# --- Profile Endpoints (Largely UNUSED by current GUI, which uses localStorage for profile details) ---
# These backend profile endpoints primarily manage the Merkle root associated with a user.
@app.route('/profile/<user_id>', methods=['GET'])
@require_api_key
def get_profile_endpoint(user_id):
    profile_data = get_or_initialize_user_profile(user_id)
    # The GUI doesn't use avatar_url from here anymore.
    # If it did, you'd construct it:
    # if profile_data.get("avatar_filename_on_server"): 
    #     profile_data["avatar_url_on_server"] = f"/uploads/avatars/{user_id}/{profile_data['avatar_filename_on_server']}"
    return jsonify(profile_data), 200

@app.route('/profile/<user_id>', methods=['POST'])
@require_api_key
def update_profile_endpoint(user_id):
    # This endpoint is NOT used by the current GUI to update display name, bio, or avatar.
    # It's kept for potential backend-only profile metadata updates.
    profile_data = get_or_initialize_user_profile(user_id)
    # Example: if 'some_backend_field' in request.form:
    #    profile_data['some_backend_field'] = request.form['some_backend_field']
    if not save_user_profile(user_id, profile_data):
        return jsonify({"error": "Failed to save backend profile data."}), 500
    return jsonify({"message": "Backend profile data processed (Note: GUI uses localStorage for most profile fields).", "profile_subset": profile_data}), 200

@app.route('/uploads/avatars/<user_id>/<path:filename>', methods=['GET'])
# This endpoint is UNUSED by the current GUI as avatars are base64 in localStorage.
def serve_avatar_endpoint(user_id, filename):
    user_avatar_directory = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', user_id)
    if not os.path.exists(os.path.join(user_avatar_directory, filename)):
        return jsonify({"error": "Avatar not found on server."}), 404
    return send_from_directory(user_avatar_directory, filename)

# --- Memory Endpoints (Actively USED by GUI) ---
@app.route('/memory/<user_id>', methods=['POST'])
@require_api_key
def add_memory(user_id):
    # Ensure user's profile.json (for Merkle root) and memories directory exist
    get_or_initialize_user_profile(user_id) 
    ensure_dir_exists(get_user_memories_path(user_id))

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    req_data = request.get_json()
    if not req_data or 'data' not in req_data or 'encryption_key' not in req_data:
        return jsonify({"error": "Missing 'data' or 'encryption_key' in JSON request"}), 400

    memory_content = req_data['data']
    encryption_key = req_data['encryption_key'] 
    metadata = req_data.get('metadata', {})
    encrypted_memory_data = encrypt_data(memory_content, encryption_key)
    memory_id = uuid.uuid4().hex
    timestamp_created = datetime.now(timezone.utc).isoformat()
    leaf_hash = calculate_hash(encrypted_memory_data) 

    memory_item = {
        "memory_id": memory_id, "user_id": user_id, "timestamp_created": timestamp_created,
        "encrypted_data": encrypted_memory_data, "leaf_hash": leaf_hash, "metadata": metadata
    }
    
    if not save_json_file(get_memory_file_path(user_id, memory_id), memory_item):
        print(f"Error: Failed to save memory file for user {user_id}, memory {memory_id}")
        return jsonify({"error": "Failed to save memory item."}), 500
    
    new_merkle_root = update_user_merkle_root(user_id)
    print(f"Memory added for user {user_id}. New Merkle Root: {new_merkle_root}")
    return jsonify({
        "message": "Memory added successfully.", "user_id": user_id, "memory_id": memory_id,
        "merkle_root": new_merkle_root, "timestamp_created": timestamp_created
    }), 201

@app.route('/memory/<user_id>', methods=['GET'])
@require_api_key
def get_memories(user_id):
    profile = get_or_initialize_user_profile(user_id) 
    decryption_key = request.args.get('decryption_key') 
    if not decryption_key:
        return jsonify({"error": "Missing decryption_key in query parameters"}), 400

    memories_dir = get_user_memories_path(user_id)
    decrypted_memories_list = []
    if os.path.exists(memories_dir):
        for filename in os.listdir(memories_dir):
            if filename.endswith(".json"):
                mem_item = load_json_file(os.path.join(memories_dir, filename))
                if mem_item:
                    decrypted_data_content = decrypt_data(mem_item['encrypted_data'], decryption_key)
                    decrypted_memories_list.append({
                        "memory_id": mem_item['memory_id'], "data": decrypted_data_content,
                        "timestamp_created": mem_item['timestamp_created'], "metadata": mem_item.get('metadata', {})
                    })
    
    current_leaf_hashes = get_all_memory_leaf_hashes(user_id)
    calculated_root_from_files = build_merkle_tree(current_leaf_hashes)
    stored_merkle_root = profile.get("merkle_root")
    integrity_verified = (calculated_root_from_files == stored_merkle_root)
    if not integrity_verified:
        print(f"INTEGRITY WARNING: Merkle root mismatch for user {user_id}. Stored: {stored_merkle_root}, Calculated: {calculated_root_from_files}")

    return jsonify({
        "user_id": user_id, "merkle_root": stored_merkle_root, 
        "memories": decrypted_memories_list, "integrity_verified": integrity_verified 
    }), 200

@app.route('/memory/<user_id>/<string:memory_id>/verify', methods=['GET'])
@require_api_key
def verify_single_memory_integrity(user_id, memory_id):
    profile = get_or_initialize_user_profile(user_id)
    target_memory_item = load_json_file(get_memory_file_path(user_id, memory_id))
    if not target_memory_item or "leaf_hash" not in target_memory_item: 
        return jsonify({"error": f"Memory with ID {memory_id} not found or invalid."}), 404

    leaf_hash_to_verify = target_memory_item['leaf_hash']
    current_merkle_root_from_profile = profile.get('merkle_root')
    all_leaf_hashes = get_all_memory_leaf_hashes(user_id)
    recalculated_overall_root = build_merkle_tree(all_leaf_hashes)

    if recalculated_overall_root == current_merkle_root_from_profile and leaf_hash_to_verify in all_leaf_hashes:
        return jsonify({
            "message": "Conceptual verification: Memory hash is consistent.", "user_id": user_id,
            "memory_id": memory_id, "leaf_hash": leaf_hash_to_verify,
            "merkle_root": current_merkle_root_from_profile, "verified_by_consistency_check": True,
        }), 200
    else:
        return jsonify({
            "message": "Conceptual verification: Memory hash or Merkle root mismatch.",
            "verified_by_consistency_check": False
        }), 400

# --- Main ---
if __name__ == '__main__':
    ensure_dir_exists(app.config['UPLOAD_FOLDER'])
    ensure_dir_exists(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars')) 
    ensure_dir_exists(app.config['DATA_STORE_FOLDER']) 
    print(f"Backend server starting...")
    print(f"IMPORTANT: Server is expecting API Key: '{API_KEY}' in X-API-KEY header for protected routes.")
    print(f"Data will be stored in: {os.path.abspath(app.config['DATA_STORE_FOLDER'])}")
    app.run(debug=True, port=5001)
    # Note: In production, set debug=False and use a proper WSGI server like Gunicorn or uWSGI.
# Note: This server is not secure for production use. Use HTTPS and proper authentication in production.
