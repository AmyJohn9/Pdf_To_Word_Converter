"""
IOCL PDF-to-Word Converter Project
-----------------------------------
AUTHENTICATION HELPER

Since there's no database, user accounts are stored in a simple JSON file
(users.json) instead of a database table. This file has functions to:
  - load the list of users from that file
  - check if a username/password combination is correct
  - create the users.json file with some starter accounts if it doesn't exist yet

IMPORTANT NOTE ON SECURITY: We never store plain passwords - only a
"hash" (a scrambled, one-way version) of each password. This means even
if someone opened users.json, they couldn't read the real passwords.
This is a basic but genuinely correct security practice.
"""

import json
import os
import hashlib

USERS_FILE = "users.json"


def hash_password(plain_password):
    """
    Turns a plain text password into a scrambled hash.
    The same password always produces the same hash, but you can't
    reverse a hash back into the original password.
    """
    return hashlib.sha256(plain_password.encode()).hexdigest()


def create_default_users_file():
    """
    Creates users.json with a couple of starter accounts, ONLY if the
    file doesn't already exist. Change these default passwords before
    real use.
    """
    if os.path.exists(USERS_FILE):
        return  # already exists, don't overwrite it

    default_users = {
        "admin": {
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "full_name": "IT Administrator"
        },
        "employee": {
            "password_hash": hash_password("employee123"),
            "role": "user",
            "full_name": "IOCL Employee"
        }
    }

    with open(USERS_FILE, "w") as f:
        json.dump(default_users, f, indent=2)


def load_users():
    """Reads and returns all users from users.json as a dictionary."""
    create_default_users_file()  # make sure the file exists first
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def verify_login(username, password):
    """
    Checks if the given username and password are correct.

    Returns a dictionary with the user's info (role, full_name) if the
    login is correct, or None if the username/password is wrong.
    """
    users = load_users()

    if username not in users:
        return None  # no such user

    entered_password_hash = hash_password(password)
    stored_password_hash = users[username]["password_hash"]

    if entered_password_hash == stored_password_hash:
        return {
            "username": username,
            "role": users[username]["role"],
            "full_name": users[username]["full_name"]
        }
    else:
        return None  # wrong password


def add_user(username, password, role, full_name):
    """
    Adds a new user to users.json. Useful later if an admin needs to
    create new accounts. "role" should be either "user" or "admin".
    """
    users = load_users()
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "full_name": full_name
    }
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)