# 🎥 Video Subtitle Generator

## 📥 Installation & Setup

### 1️. Clone the Repository
```
mkdir video-subtitle-generator
cd video-subtitle-generator
git clone https://github.com/eeswarprasanth/video_captions.git
```

## 2. Create a Virtual Environment
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## 3️. Install Required Dependencies
```
pip install -r requirements.txt
```

## 4️. Install and Configure FFmpeg  
FFmpeg is required for **audio extraction** and **adding subtitles** to videos.

## Windows  
1. Download the latest FFmpeg build from:  
   👉 [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)  
2. Extract the downloaded ZIP file.  
3. Navigate to the **bin** directory and copy the path.  
4. Add the copied path to the **System Environment Variables**:
   - Search for **"Environment Variables"** in Windows.
   - Edit the `Path` variable under **"System Variables"**.
   - Click **New** and paste the copied path.  
5. Verify installation:
```
   ffmpeg -version
```

## Mac/Linux
Install FFmpeg using Homebrew or APT:

```
# macOS (Homebrew)
brew install ffmpeg
```
## Ubuntu (APT)
```
sudo apt update && sudo apt install ffmpeg
```

## 5. Update FFMPEG_PATH in app.py
Replace the path with your system’s FFmpeg binary location:

```
FFMPEG_PATH = r"C:\\path\\to\\ffmpeg.exe"  # Windows
# FFMPEG_PATH = "/usr/bin/ffmpeg"  # Linux/macOS
```

## 6. Run the Application
```
python app.py
```

The application will start at:

```
http://127.0.0.1:5000
```

## 7. Usage Guide
1. **Go to the Upload Page**: [http://127.0.0.1:5000/upload](http://127.0.0.1:5000/upload)  
2. **Upload a Video** (MP4, MOV, MKV).  
3. **Wait for processing** (transcription, translation, and subtitle embedding).  
4. **View processed videos** at [http://127.0.0.1:5000/videos](http://127.0.0.1:5000/videos).  

---

## 8. Folder Structure
```
video-subtitle-generator/
│── uploads/                 # Processed videos & subtitles
│── templates/
│   ├── upload.html
│   ├── videos.html
│── app.py                   # Main Flask app
│── requirements.txt          # Dependencies
│── README.md                 # Documentation
```