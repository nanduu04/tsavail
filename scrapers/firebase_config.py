import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": "tsavail",
        "private_key_id": "YOUR_PRIVATE_KEY_ID",  # You'll need to get this from Firebase Console
        "private_key": "YOUR_PRIVATE_KEY",        # You'll need to get this from Firebase Console
        "client_email": "YOUR_CLIENT_EMAIL",      # You'll need to get this from Firebase Console
        "client_id": "460960292053",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "YOUR_CERT_URL",  # You'll need to get this from Firebase Console
        "universe_domain": "googleapis.com"
    })
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    
    return firestore.client()