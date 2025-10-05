from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os, uuid, subprocess, zipfile, shutil, json
from datetime import datetime
from dotenv import load_dotenv

# Google Drive
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load environment
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # 1GB limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# Google Drive OAuth
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in \
           {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'}

def split_video(file_path, output_folder, duration=10):
    """Use ffmpeg to split video"""
    os.makedirs(output_folder, exist_ok=True)
    command = [
        "ffmpeg", "-i", file_path, "-c", "copy", "-map", "0",
        "-segment_time", str(duration), "-f", "segment",
        os.path.join(output_folder, "part_%03d.mp4")
    ]
    subprocess.run(command, check=True)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        job_id = str(uuid.uuid4())
        output_folder = os.path.join(app.config['TEMP_FOLDER'], job_id)
        zip_path = os.path.join(app.config['TEMP_FOLDER'], f"{job_id}.zip")

        try:
            split_video(file_path, output_folder, duration=30)

            # Zip the parts
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, _, files in os.walk(output_folder):
                    for f in files:
                        zipf.write(os.path.join(root, f), arcname=f)

            # Upload to Google Drive
            service = get_drive_service()
            file_metadata = {"name": f"{job_id}.zip", "mimeType": "application/zip"}
            media = MediaFileUpload(zip_path, mimetype="application/zip", resumable=True)
            uploaded = service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()

            # Make file public
            service.permissions().create(
                fileId=uploaded.get("id"),
                body={"role": "reader", "type": "anyone"}
            ).execute()

            drive_link = f"https://drive.google.com/uc?id={uploaded.get('id')}&export=download"

            # Cleanup
            shutil.rmtree(output_folder)
            os.remove(file_path)
            os.remove(zip_path)

            return jsonify({"success": True, "download_link": drive_link})

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file format"}), 400

if __name__ == "__main__":
    print("🚀 AI Video Splitter with Google Drive ready!")
    app.run(host="0.0.0.0", port=5000, debug=True)
