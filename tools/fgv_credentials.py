#!/usr/bin/env python3
"""
FGV Credentials - Encrypted local file storage
Stores username/password in an encrypted file in your home folder
"""

import json
import base64
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import tkinter as tk
from tkinter import simpledialog, messagebox

# Files stored in user's home directory (hidden)
CRED_FILE = Path.home() / ".fgv_creds.enc"
KEY_FILE = Path.home() / ".fgv_key"


def _get_encryption_key():
    """Get or create a machine-specific encryption key"""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    
    # Generate key from machine-specific data
    import uuid
    machine_id = str(uuid.getnode()).encode()  # Uses MAC address
    salt = b'fgv_eclass_prova_ai_2026'
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(machine_id))
    KEY_FILE.write_bytes(key)
    
    # Hide the file on Windows
    import subprocess
    subprocess.run(['attrib', '+H', str(KEY_FILE)], capture_output=True)
    
    return key


def save_credentials(username: str, password: str):
    """Encrypt and save credentials to file"""
    key = _get_encryption_key()
    fernet = Fernet(key)
    
    data = json.dumps({"username": username, "password": password}).encode()
    encrypted = fernet.encrypt(data)
    
    CRED_FILE.write_bytes(encrypted)
    
    # Hide the file on Windows
    import subprocess
    subprocess.run(['attrib', '+H', str(CRED_FILE)], capture_output=True)
    
    print(f"✅ Credentials saved to: {CRED_FILE}")


def get_credentials():
    """Load and decrypt credentials"""
    if not CRED_FILE.exists():
        return None, None
    
    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        
        encrypted = CRED_FILE.read_bytes()
        decrypted = fernet.decrypt(encrypted)
        data = json.loads(decrypted.decode())
        
        return data.get("username"), data.get("password")
    except Exception as e:
        print(f"⚠️ Could not decrypt credentials: {e}")
        return None, None


def setup_gui():
    """GUI to enter and save credentials"""
    root = tk.Tk()
    root.withdraw()
    
    # Check if already saved
    existing_user, _ = get_credentials()
    if existing_user:
        update = messagebox.askyesno(
            "FGV Credentials",
            f"Credentials already saved for: {existing_user}\n\nDo you want to update them?"
        )
        if not update:
            root.destroy()
            return
    
    messagebox.showinfo(
        "FGV eClass Login",
        "Enter your FGV credentials.\nThey will be encrypted and saved locally."
    )
    
    username = simpledialog.askstring("FGV Username", "Username (email or CPF):", parent=root)
    if not username:
        root.destroy()
        return
    
    password = simpledialog.askstring("FGV Password", "Password:", parent=root, show='*')
    if not password:
        root.destroy()
        return
    
    try:
        save_credentials(username, password)
        messagebox.showinfo("Success", f"✅ Credentials saved!\n\nUser: {username}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save:\n{e}")
    
    root.destroy()


def check_credentials():
    """Check if credentials exist"""
    username, password = get_credentials()
    if username and password:
        print(f"✅ Credentials found for: {username}")
        return True
    else:
        print("❌ No credentials saved yet")
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_credentials()
    else:
        setup_gui()
