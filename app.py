# from flask import Flask, render_template, request, send_file, jsonify, session
# from werkzeug.utils import secure_filename
# import os
# import uuid
# import subprocess
# import zipfile
# from datetime import datetime
# import threading
# import shutil
# import google.generativeai as genai
# from dotenv import load_dotenv
# import json
# import time
# from concurrent.futures import ThreadPoolExecutor

# # Load environment variables
# load_dotenv()

# app = Flask(__name__)
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
# app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # 1GB limit
# app.config['UPLOAD_FOLDER'] = 'uploads'
# app.config['TEMP_FOLDER'] = 'temp'

# # Ensure directories exist
# os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# # Configure Google AI Studio (Gemini API)
# GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# if GOOGLE_API_KEY:
#     genai.configure(api_key=GOOGLE_API_KEY)

# ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'}

# class GoogleAIService:
#     def __init__(self):
#         self.model = None
#         self.initialize_model()
    
#     def initialize_model(self):
#         """Initialize Gemini model"""
#         try:
#             if GOOGLE_API_KEY:
#                 self.model = genai.GenerativeModel('gemini-pro')
#                 return True
#             return False
#         except Exception as e:
#             print(f"AI Model initialization failed: {e}")
#             return False
    
#     def analyze_video_content(self, video_info):
#         """Use Gemini AI to analyze video and suggest segmentation"""
#         try:
#             if not self.model:
#                 return self.get_fallback_analysis()
            
#             prompt = f"""
#             Analyze this video information and provide:
#             1. A creative title for the video
#             2. Suggested segment titles for {video_info['segment_count']} segments
#             3. Optimal segmentation strategy
#             4. Brief content description
            
#             Video Details:
#             - Duration: {video_info['duration']} seconds
#             - Estimated segments: {video_info['segment_count']}
#             - File size: {video_info['file_size_mb']} MB
            
#             Respond in JSON format:
#             {{
#                 "video_title": "creative title",
#                 "segments": ["Segment 1 title", "Segment 2 title", ...],
#                 "strategy": "segmentation strategy",
#                 "description": "content description"
#             }}
#             """
            
#             response = self.model.generate_content(prompt)
#             return self.parse_ai_response(response.text)
            
#         except Exception as e:
#             print(f"AI Analysis error: {e}")
#             return self.get_fallback_analysis(video_info['segment_count'])
    
#     def parse_ai_response(self, response_text):
#         """Parse AI response and extract JSON"""
#         try:
#             # Extract JSON from response
#             start = response_text.find('{')
#             end = response_text.rfind('}') + 1
#             if start != -1 and end != -1:
#                 json_str = response_text[start:end]
#                 return json.loads(json_str)
#         except:
#             pass
        
#         return self.get_fallback_analysis(3)
    
#     def get_fallback_analysis(self, segment_count=3):
#         """Fallback analysis when AI is unavailable"""
#         return {
#             "video_title": "Your Video Content",
#             "segments": [f"Part {i+1}: Engaging Content" for i in range(segment_count)],
#             "strategy": "Optimal 2-minute segments for viewer engagement",
#             "description": "Video content ready for segmentation"
#         }
    
#     def generate_segment_metadata(self, segments_info):
#         """Generate metadata for each segment using AI"""
#         try:
#             if not self.model:
#                 return []
            
#             prompt = f"""
#             Generate engaging titles and descriptions for {len(segments_info)} video segments.
#             Each segment is approximately 2 minutes long.
            
#             Respond in JSON format:
#             {{
#                 "segments": [
#                     {{
#                         "title": "creative title for segment 1",
#                         "description": "engaging description",
#                         "duration": "2:00"
#                     }},
#                     ...
#                 ]
#             }}
#             """
            
#             response = self.model.generate_content(prompt)
#             return self.parse_segment_metadata(response.text)
            
#         except Exception as e:
#             print(f"Segment metadata error: {e}")
#             return []

#     def parse_segment_metadata(self, response_text):
#         """Parse segment metadata from AI response"""
#         try:
#             start = response_text.find('{')
#             end = response_text.rfind('}') + 1
#             if start != -1 and end != -1:
#                 json_str = response_text[start:end]
#                 data = json.loads(json_str)
#                 return data.get('segments', [])
#         except:
#             pass
#         return []

# # Initialize AI Service
# ai_service = GoogleAIService()

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def get_video_duration(file_path):
#     """Get video duration using ffprobe"""
#     try:
#         cmd = [
#             'ffprobe', '-v', 'error', '-show_entries', 
#             'format=duration', '-of', 
#             'default=noprint_wrappers=1:nokey=1', file_path
#         ]
#         result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
#         return float(result.stdout.strip())
#     except:
#         return 0

# def split_video_optimized(input_path, output_dir, segment_duration=120):
#     """Optimized video splitting with ffmpeg"""
#     try:
#         os.makedirs(output_dir, exist_ok=True)
        
#         # Use fast copying without re-encoding
#         cmd = [
#             'ffmpeg', '-i', input_path,
#             '-c', 'copy',  # No re-encoding for speed
#             '-map', '0',
#             '-segment_time', str(segment_duration),
#             '-f', 'segment',
#             '-reset_timestamps', '1',
#             '-y',  # Overwrite output files
#             os.path.join(output_dir, 'segment_%03d.mp4')
#         ]
        
#         # Run with timeout
#         result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
#         if result.returncode == 0:
#             segments = [f for f in os.listdir(output_dir) if f.startswith('segment_')]
#             return True, sorted(segments)
#         else:
#             return False, f"FFmpeg error: {result.stderr}"
            
#     except subprocess.TimeoutExpired:
#         return False, "Processing timeout"
#     except Exception as e:
#         return False, str(e)

# def create_zip_with_metadata(source_dir, zip_path, metadata):
#     """Create ZIP file with AI-generated metadata"""
#     try:
#         with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
#             # Add all video segments
#             for root, dirs, files in os.walk(source_dir):
#                 for file in files:
#                     if file.startswith('segment_'):
#                         file_path = os.path.join(root, file)
#                         arcname = file  # Keep original filename
#                         zipf.write(file_path, arcname)
            
#             # Add metadata file
#             metadata_file = "segmentation_metadata.json"
#             metadata_path = os.path.join(source_dir, metadata_file)
#             with open(metadata_path, 'w') as f:
#                 json.dump(metadata, f, indent=2)
#             zipf.write(metadata_path, metadata_file)
            
#         return True
#     except Exception as e:
#         print(f"ZIP creation error: {e}")
#         return False

# def cleanup_old_files():
#     """Cleanup files older than 1 hour"""
#     try:
#         current_time = datetime.now()
#         for folder in [app.config['UPLOAD_FOLDER'], app.config['TEMP_FOLDER']]:
#             if os.path.exists(folder):
#                 for filename in os.listdir(folder):
#                     file_path = os.path.join(folder, filename)
#                     if os.path.isfile(file_path):
#                         file_time = datetime.fromtimestamp(os.path.getctime(file_path))
#                         if (current_time - file_time).total_seconds() > 3600:
#                             os.remove(file_path)
#                     elif os.path.isdir(file_path):
#                         file_time = datetime.fromtimestamp(os.path.getctime(file_path))
#                         if (current_time - file_time).total_seconds() > 3600:
#                             shutil.rmtree(file_path)
#     except Exception as e:
#         print(f"Cleanup error: {e}")

# @app.route('/')
# def index():
#     return render_template('index.html', ai_available=bool(GOOGLE_API_KEY))

# @app.route('/analyze', methods=['POST'])
# def analyze_video():
#     """Quick analysis with AI"""
#     if 'video' not in request.files:
#         return jsonify({'error': 'No file selected'}), 400
    
#     file = request.files['video']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected'}), 400
    
#     if not allowed_file(file.filename):
#         return jsonify({'error': 'File type not allowed'}), 400
    
#     # Quick analysis
#     file_size_mb = len(file.read()) / (1024 * 1024)
#     file.seek(0)  # Reset file pointer
    
#     # Estimate segments
#     estimated_segments = max(1, int(file_size_mb / 50))  # Rough estimate
    
#     # AI Analysis
#     video_info = {
#         'duration': 0,  # We don't have duration yet
#         'segment_count': estimated_segments,
#         'file_size_mb': round(file_size_mb, 2)
#     }
    
#     ai_analysis = ai_service.analyze_video_content(video_info)
    
#     analysis_result = {
#         'size_mb': video_info['file_size_mb'],
#         'estimated_segments': estimated_segments,
#         'ai_analysis': ai_analysis,
#         'ai_enabled': bool(GOOGLE_API_KEY),
#         'status': 'ready'
#     }
    
#     return jsonify(analysis_result)

# @app.route('/upload', methods=['POST'])
# def upload_video():
#     """Main upload and processing endpoint"""
#     if 'video' not in request.files:
#         return jsonify({'error': 'No file selected'}), 400
    
#     file = request.files['video']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected'}), 400
    
#     if not allowed_file(file.filename):
#         return jsonify({'error': 'File type not allowed. Supported: MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V'}), 400
    
#     # Generate session ID
#     session_id = str(uuid.uuid4())
#     upload_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
#     os.makedirs(upload_path, exist_ok=True)
    
#     # Save uploaded file
#     filename = secure_filename(file.filename)
#     file_path = os.path.join(upload_path, filename)
#     file.save(file_path)
    
#     try:
#         # Get video duration
#         duration = round((get_video_duration(file_path))/60,2)
#         if duration == 0:
#             return jsonify({'error': 'Could not process video file. Please try another format.'}), 400
        
#         # Calculate segments
#         segment_duration = 120  # 2 minutes
#         segment_count = max(1, int(duration / segment_duration) + (1 if duration % segment_duration > 0 else 0))
        
#         # Get AI analysis
#         video_info = {
#             'duration': duration,
#             'segment_count': segment_count,
#             'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2)
#         }
        
#         ai_analysis = ai_service.analyze_video_content(video_info)
        
#         # Split video
#         segments_dir = os.path.join(app.config['TEMP_FOLDER'], session_id)
#         success, segments = split_video_optimized(file_path, segments_dir, segment_duration)
        
#         if not success:
#             return jsonify({'error': f'Video processing failed: {segments}'}), 400
        
#         # Generate segment metadata
#         segment_metadata = ai_service.generate_segment_metadata(segments)
        
#         # Prepare final metadata
#         final_metadata = {
#             'original_video': filename,
#             'total_duration': duration,
#             'segment_count': len(segments),
#             'ai_analysis': ai_analysis,
#             'segments_metadata': segment_metadata,
#             'processing_time': datetime.now().isoformat(),
#             'ai_generated': bool(GOOGLE_API_KEY)
#         }
        
#         # Create ZIP with metadata
#         zip_filename = f'segmented_videos_{session_id}.zip'
#         zip_path = os.path.join(app.config['TEMP_FOLDER'], zip_filename)
        
#         if create_zip_with_metadata(segments_dir, zip_path, final_metadata):
#             return jsonify({
#                 'success': True,
#                 'session_id': session_id,
#                 'zip_filename': zip_filename,
#                 'segment_count': len(segments),
#                 'total_duration': f"{duration:.2f} Minutes",
#                 'ai_analysis': ai_analysis,
#                 'ai_enabled': bool(GOOGLE_API_KEY),
#                 'file_size': video_info['file_size_mb']
#             })
#         else:
#             return jsonify({'error': 'Failed to create download package'}), 500
        
#     except Exception as e:
#         print(f"Upload error: {e}")
#         return jsonify({'error': f'Processing error: {str(e)}'}), 500

# @app.route('/download/<filename>')
# def download_file(filename):
#     """Download the segmented videos ZIP"""
#     try:
#         file_path = os.path.join(app.config['TEMP_FOLDER'], filename)
#         if os.path.exists(file_path):
#             download_name = f"ai_segmented_videos_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
#             return send_file(file_path, as_attachment=True, download_name=download_name)
#         else:
#             return jsonify({'error': 'File not found or expired'}), 404
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/status')
# def api_status():
#     """API status endpoint"""
#     return jsonify({
#         'status': 'operational',
#         'ai_enabled': bool(GOOGLE_API_KEY),
#         'timestamp': datetime.now().isoformat()
#     })

# # Background cleanup thread
# def start_cleanup_thread():
#     def cleanup_loop():
#         while True:
#             cleanup_old_files()
#             time.sleep(3600)  # Run every hour
    
#     thread = threading.Thread(target=cleanup_loop, daemon=True)
#     thread.start()

# if __name__ == '__main__':
#     start_cleanup_thread()
#     print("🔮 Video AI Splitter Started!")
#     print(f"🤖 AI Features: {'ENABLED' if GOOGLE_API_KEY else 'DISABLED'}")
#     print("🌐 Server running on http://localhost:5000")
#     app.run(debug=True, host='0.0.0.0', port=5000)




############################################################################################################################################################




from flask import Flask, render_template, request, send_file, jsonify, session
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
import boto3
from botocore.exceptions import ClientError
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit for metadata
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TEMP_FOLDER'] = 'temp'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

# Configure Google AI Studio (Gemini API)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET')

# Initialize S3 client
s3_client = None
if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET]):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v'}

class GoogleAIService:
    def __init__(self):
        self.model = None
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize Gemini model"""
        try:
            if GOOGLE_API_KEY:
                self.model = genai.GenerativeModel('gemini-pro')
                return True
            return False
        except Exception as e:
            print(f"AI Model initialization failed: {e}")
            return False
    
    def analyze_video_content(self, video_info):
        """Use Gemini AI to analyze video and suggest segmentation"""
        try:
            if not self.model:
                return self.get_fallback_analysis()
            
            prompt = f"""
            Analyze this video information and provide:
            1. A creative title for the video
            2. Suggested segment titles for {video_info['segment_count']} segments
            3. Optimal segmentation strategy
            4. Brief content description
            
            Video Details:
            - Duration: {video_info['duration']} seconds
            - Estimated segments: {video_info['segment_count']}
            - File size: {video_info['file_size_mb']} MB
            
            Respond in JSON format:
            {{
                "video_title": "creative title",
                "segments": ["Segment 1 title", "Segment 2 title", ...],
                "strategy": "segmentation strategy",
                "description": "content description"
            }}
            """
            
            response = self.model.generate_content(prompt)
            return self.parse_ai_response(response.text)
            
        except Exception as e:
            print(f"AI Analysis error: {e}")
            return self.get_fallback_analysis(video_info['segment_count'])
    
    def parse_ai_response(self, response_text):
        """Parse AI response and extract JSON"""
        try:
            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except:
            pass
        
        return self.get_fallback_analysis(3)
    
    def get_fallback_analysis(self, segment_count=3):
        """Fallback analysis when AI is unavailable"""
        return {
            "video_title": "Your Video Content",
            "segments": [f"Part {i+1}: Engaging Content" for i in range(segment_count)],
            "strategy": "Optimal 2-minute segments for viewer engagement",
            "description": "Video content ready for segmentation"
        }
    
    def generate_segment_metadata(self, segments_info):
        """Generate metadata for each segment using AI"""
        try:
            if not self.model:
                return []
            
            prompt = f"""
            Generate engaging titles and descriptions for {len(segments_info)} video segments.
            Each segment is approximately 2 minutes long.
            
            Respond in JSON format:
            {{
                "segments": [
                    {{
                        "title": "creative title for segment 1",
                        "description": "engaging description",
                        "duration": "2:00"
                    }},
                    ...
                ]
            }}
            """
            
            response = self.model.generate_content(prompt)
            return self.parse_segment_metadata(response.text)
            
        except Exception as e:
            print(f"Segment metadata error: {e}")
            return []

    def parse_segment_metadata(self, response_text):
        """Parse segment metadata from AI response"""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
                data = json.loads(json_str)
                return data.get('segments', [])
        except:
            pass
        return []

# Initialize AI Service
ai_service = GoogleAIService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_duration(file_path):
    """Get video duration using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 
            'format=duration', '-of', 
            'default=noprint_wrappers=1:nokey=1', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except:
        return 0

def split_video_optimized(input_path, output_dir, segment_duration=120):
    """Optimized video splitting with ffmpeg"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Use fast copying without re-encoding
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c', 'copy',  # No re-encoding for speed
            '-map', '0',
            '-segment_time', str(segment_duration),
            '-f', 'segment',
            '-reset_timestamps', '1',
            '-y',  # Overwrite output files
            os.path.join(output_dir, 'segment_%03d.mp4')
        ]
        
        # Run with timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            segments = [f for f in os.listdir(output_dir) if f.startswith('segment_')]
            return True, sorted(segments)
        else:
            return False, f"FFmpeg error: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Processing timeout"
    except Exception as e:
        return False, str(e)

def create_zip_with_metadata(source_dir, zip_path, metadata):
    """Create ZIP file with AI-generated metadata"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all video segments
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.startswith('segment_'):
                        file_path = os.path.join(root, file)
                        arcname = file  # Keep original filename
                        zipf.write(file_path, arcname)
            
            # Add metadata file
            metadata_file = "segmentation_metadata.json"
            metadata_path = os.path.join(source_dir, metadata_file)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            zipf.write(metadata_path, metadata_file)
            
        return True
    except Exception as e:
        print(f"ZIP creation error: {e}")
        return False

def cleanup_old_files():
    """Cleanup files older than 1 hour"""
    try:
        current_time = datetime.now()
        for folder in [app.config['UPLOAD_FOLDER'], app.config['TEMP_FOLDER']]:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        if (current_time - file_time).total_seconds() > 3600:
                            os.remove(file_path)
                    elif os.path.isdir(file_path):
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        if (current_time - file_time).total_seconds() > 3600:
                            shutil.rmtree(file_path)
    except Exception as e:
        print(f"Cleanup error: {e}")

def generate_presigned_url(object_name, expiration=3600):
    """Generate a presigned URL for S3 upload"""
    if not s3_client:
        return None
    
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': object_name,
                'ContentType': 'video/mp4'
            },
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None

def download_from_s3(object_name, local_path):
    """Download file from S3"""
    if not s3_client:
        return False
    
    try:
        s3_client.download_file(S3_BUCKET, object_name, local_path)
        return True
    except ClientError as e:
        print(f"Error downloading from S3: {e}")
        return False

def upload_to_s3(local_path, object_name):
    """Upload file to S3"""
    if not s3_client:
        return False
    
    try:
        s3_client.upload_file(local_path, S3_BUCKET, object_name)
        return True
    except ClientError as e:
        print(f"Error uploading to S3: {e}")
        return False

def generate_presigned_download_url(object_name, expiration=3600):
    """Generate a presigned URL for S3 download"""
    if not s3_client:
        return None
    
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': object_name
            },
            ExpiresIn=expiration
        )
        return response
    except ClientError as e:
        print(f"Error generating download URL: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html', ai_available=bool(GOOGLE_API_KEY), s3_available=bool(s3_client))

@app.route('/generate_presigned_url', methods=['POST'])
def generate_presigned_url_route():
    """Generate presigned URL for direct S3 upload"""
    if not s3_client:
        return jsonify({'error': 'S3 storage not configured'}), 500
    
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'Filename required'}), 400
    
    if not allowed_file(filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Generate unique object name
    session_id = str(uuid.uuid4())
    object_name = f"uploads/{session_id}/{secure_filename(filename)}"
    
    presigned_url = generate_presigned_url(object_name)
    
    if presigned_url:
        return jsonify({
            'presigned_url': presigned_url,
            'object_name': object_name,
            'session_id': session_id
        })
    else:
        return jsonify({'error': 'Failed to generate upload URL'}), 500

@app.route('/process_video', methods=['POST'])
def process_video():
    """Process video after S3 upload"""
    if not s3_client:
        return jsonify({'error': 'S3 storage not configured'}), 500
    
    data = request.get_json()
    object_name = data.get('object_name')
    session_id = data.get('session_id')
    
    if not object_name or not session_id:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    try:
        # Download video from S3
        download_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_video.mp4")
        if not download_from_s3(object_name, download_path):
            return jsonify({'error': 'Failed to download video from storage'}), 500
        
        # Get video duration
        duration = get_video_duration(download_path)
        if duration == 0:
            return jsonify({'error': 'Could not process video file'}), 400
        
        # Calculate segments
        segment_duration = 120  # 2 minutes
        segment_count = max(1, int(duration / segment_duration) + (1 if duration % segment_duration > 0 else 0))
        
        # Get AI analysis
        video_info = {
            'duration': duration,
            'segment_count': segment_count,
            'file_size_mb': round(os.path.getsize(download_path) / (1024 * 1024), 2)
        }
        
        ai_analysis = ai_service.analyze_video_content(video_info)
        
        # Split video
        segments_dir = os.path.join(app.config['TEMP_FOLDER'], session_id)
        success, segments = split_video_optimized(download_path, segments_dir, segment_duration)
        
        if not success:
            return jsonify({'error': f'Video processing failed: {segments}'}), 400
        
        # Generate segment metadata
        segment_metadata = ai_service.generate_segment_metadata(segments)
        
        # Prepare final metadata
        final_metadata = {
            'original_video': object_name.split('/')[-1],
            'total_duration': duration,
            'segment_count': len(segments),
            'ai_analysis': ai_analysis,
            'segments_metadata': segment_metadata,
            'processing_time': datetime.now().isoformat(),
            'ai_generated': bool(GOOGLE_API_KEY)
        }
        
        # Create ZIP with metadata
        zip_filename = f'segmented_videos_{session_id}.zip'
        zip_path = os.path.join(app.config['TEMP_FOLDER'], zip_filename)
        
        if create_zip_with_metadata(segments_dir, zip_path, final_metadata):
            # Upload ZIP to S3
            zip_object_name = f"results/{session_id}/{zip_filename}"
            if upload_to_s3(zip_path, zip_object_name):
                # Generate download URL
                download_url = generate_presigned_download_url(zip_object_name)
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'zip_filename': zip_filename,
                    'download_url': download_url,
                    'segment_count': len(segments),
                    'total_duration': f"{duration:.2f} Minutes",
                    'ai_analysis': ai_analysis,
                    'ai_enabled': bool(GOOGLE_API_KEY),
                    'file_size': video_info['file_size_mb']
                })
            else:
                return jsonify({'error': 'Failed to upload result to storage'}), 500
        else:
            return jsonify({'error': 'Failed to create download package'}), 500
        
    except Exception as e:
        print(f"Processing error: {e}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_video():
    """Legacy upload endpoint - now uses S3 if available"""
    if s3_client:
        # Use S3 flow
        return process_video_direct()
    else:
        # Fallback to local processing
        return upload_video_local()

def upload_video_local():
    """Local upload processing (fallback)"""
    if 'video' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Supported: MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V'}), 400
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    try:
        # Get video duration
        duration = get_video_duration(file_path)
        if duration == 0:
            return jsonify({'error': 'Could not process video file. Please try another format.'}), 400
        
        # Calculate segments
        segment_duration = 120  # 2 minutes
        segment_count = max(1, int(duration / segment_duration) + (1 if duration % segment_duration > 0 else 0))
        
        # Get AI analysis
        video_info = {
            'duration': duration,
            'segment_count': segment_count,
            'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2)
        }
        
        ai_analysis = ai_service.analyze_video_content(video_info)
        
        # Split video
        segments_dir = os.path.join(app.config['TEMP_FOLDER'], session_id)
        success, segments = split_video_optimized(file_path, segments_dir, segment_duration)
        
        if not success:
            return jsonify({'error': f'Video processing failed: {segments}'}), 400
        
        # Generate segment metadata
        segment_metadata = ai_service.generate_segment_metadata(segments)
        
        # Prepare final metadata
        final_metadata = {
            'original_video': filename,
            'total_duration': duration,
            'segment_count': len(segments),
            'ai_analysis': ai_analysis,
            'segments_metadata': segment_metadata,
            'processing_time': datetime.now().isoformat(),
            'ai_generated': bool(GOOGLE_API_KEY)
        }
        
        # Create ZIP with metadata
        zip_filename = f'segmented_videos_{session_id}.zip'
        zip_path = os.path.join(app.config['TEMP_FOLDER'], zip_filename)
        
        if create_zip_with_metadata(segments_dir, zip_path, final_metadata):
            return jsonify({
                'success': True,
                'session_id': session_id,
                'zip_filename': zip_filename,
                'segment_count': len(segments),
                'total_duration': f"{duration:.2f} Minutes",
                'ai_analysis': ai_analysis,
                'ai_enabled': bool(GOOGLE_API_KEY),
                'file_size': video_info['file_size_mb']
            })
        else:
            return jsonify({'error': 'Failed to create download package'}), 500
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Processing error: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download the segmented videos ZIP"""
    try:
        file_path = os.path.join(app.config['TEMP_FOLDER'], filename)
        if os.path.exists(file_path):
            download_name = f"ai_segmented_videos_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
            return send_file(file_path, as_attachment=True, download_name=download_name)
        else:
            return jsonify({'error': 'File not found or expired'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'operational',
        'ai_enabled': bool(GOOGLE_API_KEY),
        's3_enabled': bool(s3_client),
        'timestamp': datetime.now().isoformat()
    })

# Background cleanup thread
def start_cleanup_thread():
    def cleanup_loop():
        while True:
            cleanup_old_files()
            time.sleep(3600)  # Run every hour
    
    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()

if __name__ == '__main__':
    start_cleanup_thread()
    print("🔮 Video AI Splitter Started!")
    print(f"🤖 AI Features: {'ENABLED' if GOOGLE_API_KEY else 'DISABLED'}")
    print(f"☁️  S3 Storage: {'ENABLED' if s3_client else 'DISABLED'}")
    print("🌐 Server running on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)



