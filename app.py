from flask import Flask, render_template, request, send_file, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
import subprocess
import zipfile
from datetime import datetime
import threading
import shutil
import google.generativeai as genai
from dotenv import load_dotenv
import json
import time

# Google Drive imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # 1GB limit
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'
app.config['GOOGLE_CLIENT_SECRETS_FILE'] = "credentials.json"

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# Google AI Studio
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'}

# ---------------- GOOGLE DRIVE HELPERS ---------------- #

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_drive_service():
    """Return an authenticated Drive API service"""
    if "credentials" not in session:
        return None
    creds = Credentials.from_authorized_user_info(session["credentials"], SCOPES)
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds)

@app.route("/authorize")
def authorize():
    flow = Flow.from_client_secrets_file(
        app.config["GOOGLE_CLIENT_SECRETS_FILE"],
        scopes=SCOPES,
        redirect_uri=url_for("oauth2callback", _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )
    session["state"] = state
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    state = session["state"]
    flow = Flow.from_client_secrets_file(
        app.config["GOOGLE_CLIENT_SECRETS_FILE"],
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for("oauth2callback", _external=True)
    )
    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    session["credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }
    return redirect(url_for("index"))

@app.route("/upload_drive/<filename>")
def upload_drive(filename):
    """Upload a processed ZIP file to Google Drive"""
    file_path = os.path.join(app.config["TEMP_FOLDER"], filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    service = get_drive_service()
    if not service:
        return redirect(url_for("authorize"))

    file_metadata = {"name": filename, "mimeType": "application/zip"}
    media = MediaFileUpload(file_path, mimetype="application/zip", resumable=True)
    uploaded = service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()

    return jsonify({
        "success": True,
        "file_id": uploaded.get("id"),
        "drive_link": uploaded.get("webViewLink")
    })

# ---------------- EXISTING CODE (shortened) ---------------- #
# I kept your full AI + splitting logic intact.
# Only change: after creating ZIP, you can now call /upload_drive/<filename>.

@app.route('/')
def index():
    return render_template('index.html', ai_available=bool(GOOGLE_API_KEY))

# (rest of your original analyze, upload, download, cleanup endpoints here...)

if __name__ == '__main__':
    print("🔮 Video AI Splitter with Google Drive Integrated!")
    app.run(debug=True, host='0.0.0.0', port=5000)
