# Personal Memory Vault

## Project Overview

The Personal Memory Vault is a web application designed to provide users with a secure and private way to store, manage, and interact with their personal memories and notes. It features a Python Flask backend for memory storage and integrity verification using Merkle trees, and an HTML/JavaScript frontend for user interaction, profile management (stored locally in the browser), calendar-based note-taking, and integration with Large Language Models (LLMs) like Gemini.
```
The core principles of this project include:
🔐 **Security Focused:** While currently using placeholder encryption, the architecture is designed for robust encryption and data integrity.
🔄 **User-Controlled Data:** Users manage their profiles and API keys locally, and memory data is intended to be user-encrypted.
🧩 **Modular Features:** Includes distinct modules for profile management, API key settings, calendar notes, memory viewing/addition, and LLM interaction.
📜 **Auditable (Conceptual):** Merkle trees are used on the backend to ensure the integrity of stored memory sets.
```
## Features

* **Secure Login:** Basic user login/registration system (using browser `localStorage` for user credentials in this version).
* **User Profile Management (Client-Side):**
    * Set display name and bio.
    * Upload an avatar (stored as base64 in `localStorage`).
    * All profile data is stored locally in the user's browser.
* **API & Encryption Key Management (Client-Side):**
    * Users can set and generate their "Vault API Key" and "Vault Encryption Key".
    * These keys are stored in `localStorage` as part of the user's profile.
    * History management for these keys (view, use historical, delete from history).
    * **Note:** The "Vault API Key" set in the GUI *must* match the `API_KEY` configured in the backend server for memory operations.
* **Memory Storage (Backend):**
    * Add new memories with content and optional JSON metadata.
    * Memories are "encrypted" (placeholder) using a user-provided key.
    * Memories are stored as individual JSON files on the server for persistence.
    * Merkle tree integration on the backend to maintain the integrity of the memory set for each user.
* **Calendar Notes:**
    * Interactive monthly calendar view.
    * Add/view notes for specific days.
    * Daily notes are stored as memories with special metadata (`calendar_date`).
    * Indicators on calendar days show if notes exist.
* **Memories Viewer:**
    * View all memories in a chronological list.
    * Filter memories by a date range.
* **LLM Integration (Gemini):**
    * Interface to send prompts to Google's Gemini API (using `gemini-2.0-flash`).
    * Generate a comprehensive "Memory Summary Prompt" from all stored memories to provide context to an LLM.
    * Input for user's Gemini API Key.
* **User-Friendly Interface:**
    * Tabbed navigation for different sections.
    * Password visibility toggles.
    * Toast notifications for user feedback.
    * Loading indicators for asynchronous operations.

## Folder Structure


personal_memory_vault/
├── backend/
│   ├── main.py             # Flask application (server)
│   ├── data_store/         # PERSISTENT: Stores user profiles (merkle roots) and memories
│   │   └── <user_id>/
│   │       ├── profile.json
│   │       └── memories/
│   │           └── <memory_id>.json
│   ├── uploads/            # For avatar image files (currently unused by GUI, which uses localStorage)
│   │   └── avatars/
│   │       └── <user_id>/
│   │           └── <avatar_filename>
│   ├── .venv/              # Python virtual environment (recommended)
│   └── requirements.txt    # Python dependencies (Flask, Flask-CORS, Werkzeug)
│
├── frontend/
│   └── memory_gui.html     # Main HTML GUI file
│
└── README.md               # This file


## Backend Setup

The backend is a Python Flask application.

**1. Prerequisites:**
   * Python 3.7+
   * `pip` (Python package installer)

**2. Installation:**
   * Clone the repository (or create the `backend` directory and place `main.py` inside).
   * Navigate to the `backend` directory:
     ```bash
     cd path/to/personal_memory_vault/backend
     ```
   * Create and activate a Python virtual environment (recommended):
     ```bash
     python -m venv .venv
     source .venv/bin/activate  # On Windows: .venv\Scripts\activate
     ```
   * Install dependencies:
     ```bash
     pip install Flask Flask-CORS Werkzeug
     ```
     (You can also create a `requirements.txt` file with these package names and run `pip install -r requirements.txt`)

**3. Configuration (Crucial for API Key):**
   * Open `backend/main.py`.
   * Locate the `API_KEY` variable (around line 12):
     ```python
     API_KEY = "your_secret_api_key" 
     ```
   * **Change `"your_secret_api_key"` to a strong, unique secret key.** This is the key the server will expect from the frontend for authorized operations.
   * The server will print the API key it's expecting when it starts.

**4. Running the Server:**
   * While in the `backend` directory (and with the virtual environment activated), run:
     ```bash
     python main.py
     ```
   * The server should start, typically on `http://127.0.0.1:5001/`.
   * It will automatically create the `data_store` and `uploads` directories if they don't exist.
   * **Note the API key printed in the console.**

## Frontend Usage

The frontend is a single HTML file (`memory_gui.html`) that interacts with the backend API.

**1. Prerequisites:**
   * A modern web browser (Chrome, Firefox, Edge, Safari).
   * The backend server must be running.

**2. Accessing the GUI:**
   * Navigate to the `frontend` directory.
   * Open `memory_gui.html` directly in your web browser (e.g., File > Open File, or by dragging it into a browser window).

**3. Login/Registration:**
   * You'll be greeted with a login screen.
   * **Select User:** Choose an existing user from the dropdown or select "--- Add New User ---".
   * **Login:** If an existing user is selected, enter their password. (Default demo: `testuser` / `testpass`).
   * **Register:** If "Add New User" is selected, input fields for a new username and password will appear.
   * User credentials (for login) and profile data (including API keys set by the user) are stored in the browser's `localStorage`.

**4. Using the Application:**
   * Once logged in, you'll see the main application interface with several tabs:
        * **User Profile:** Manage your display name, bio, and avatar. Click "Save Profile & Settings" to save changes to `localStorage`.
        * **API Settings:**
            * **Vault API Key:** Set the API key that the GUI will use to communicate with your backend server. **This MUST match the `API_KEY` you configured in `backend/main.py`.**
            * **Vault Encryption Key:** Set the key used for the (placeholder) encryption/decryption of memories.
            * You can generate new random keys for these fields.
            * Manage history for these keys (view, use, delete from history).
            * **Remember to go to the "User Profile" tab and click "Save Profile & Settings" to persist any changes made to these keys in your local profile.**
        * **Calendar:** View a monthly calendar, add notes for specific days (which are saved as memories), and see indicators for days with notes.
        * **Memories Viewer:** View a list of your memories, filter them by date range.
        * **Add Memory:** (Previously "Memories" tab) Add new general memories with content and optional metadata.
        * **LLM Integration:** Interact with Google's Gemini API. Generate a summary of all your memories to use as a prompt.

## Key Technologies Used

* **Backend:**
    * Python
    * Flask (Web framework)
    * Flask-CORS (For Cross-Origin Resource Sharing)
    * Werkzeug (For secure filenames, though avatar uploads are currently GUI-driven)
* **Frontend:**
    * HTML5
    * Tailwind CSS (for styling, via CDN)
    * JavaScript (for all client-side logic, API calls, DOM manipulation)
* **Data Storage:**
    * **Backend:** JSON files on the server's file system for memories and user profile metadata (like Merkle roots).
    * **Frontend:** Browser `localStorage` for user login credentials, user profile details (name, bio, avatar), and user-set API/Encryption keys.
* **Conceptual:**
    * Merkle Trees (for data integrity on the backend)

## Future Enhancements / Considerations

* **Real Encryption:** Implement strong, end-to-end encryption for memories. The current encryption is a placeholder.
* **Secure Authentication:** Replace the `localStorage`-based login with a robust, server-side authentication system (e.g., OAuth, JWTs, hashed passwords).
* **Database Integration:** For more complex querying and scalability, replace file-based storage on the backend with a proper database (e.g., PostgreSQL, SQLite, MongoDB).
* **Advanced Merkle Proofs:** Implement full Merkle proof generation and verification for individual memory items.
* **Memory Sharing/Permissions:** Allow users to securely share specific memories or memory bundles with others or with specific applications.
* **LLM Contextualization:** More sophisticated ways to select and inject relevant memories as context for LLM prompts.
* **Error Handling & UI/UX Improvements:** More granular error messages, improved visual feedback, and overall user experience enhancements.
* **Deployment:** Instructions and configurations for deploying the backend server to a cloud platform or dedicated server.
* **Testing:** Comprehensive unit and integration tests for both backend and frontend.

---

This README provides a starting point. Feel free to expand and refine it as the project evolves!
