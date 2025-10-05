from flask import Flask, render_template, request, send_file, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
import subprocess
import zipfile
from dotenv import load_dotenv
import shutil

# Load env variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # 1GB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'}

# ---------------- HELPERS ---------------- #
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_duration(input_path):
    """Get total duration of video in seconds using ffprobe"""
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of',
        'default=noprint_wrappers=1:nokey=1', input_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 0.0

def split_video(input_path, output_dir, segment_duration=120):
    os.makedirs(output_dir, exist_ok=True)
    cmd = [
        'ffmpeg', '-i', input_path,
        '-c', 'copy', '-map', '0',
        '-segment_time', str(segment_duration),
        '-f', 'segment', '-reset_timestamps', '1',
        os.path.join(output_dir, 'segment_%03d.mp4')
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def create_zip(source_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    return True

# ---------------- ROUTES ---------------- #
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['video']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400

    session_id = str(uuid.uuid4())
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(upload_path, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)

    # ---- get video duration (seconds) ----
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of',
             'default=noprint_wrappers=1:nokey=1', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        total_duration = float(result.stdout.strip())
    except Exception:
        total_duration = 0.0

    # ---- split video ----
    segments_dir = os.path.join(app.config['TEMP_FOLDER'], session_id)
    success = split_video(file_path, segments_dir)
    if not success:
        return jsonify({'error': 'Video processing failed'}), 500

    # ---- count segments ----
    segments = [f for f in os.listdir(segments_dir) if f.endswith(".mp4")]
    num_segments = len(segments)

    # ---- zip ----
    zip_filename = f"segments_{session_id}.zip"
    zip_path = os.path.join(app.config['TEMP_FOLDER'], zip_filename)
    create_zip(segments_dir, zip_path)

    # ---- convert duration to minutes ----
    total_duration_minutes = round(total_duration / 60, 2)

    return jsonify({
        "success": True,
        "segments": num_segments,              # ✅ now defined
        "duration": total_duration_minutes,    # ✅ now defined
        "zip_file": zip_filename
    })

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['TEMP_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

if __name__ == "__main__":
    print("🚀 Running AI Video Splitter")
    app.run(debug=True, host="0.0.0.0", port=5000)
