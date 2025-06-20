import os
import cv2
import ffmpeg
import math
import subprocess
import io
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from contextlib import redirect_stdout
from faster_whisper import WhisperModel
from googletrans import Translator

app = Flask(__name__)
app.secret_key = 'secret-key'
UPLOADS_DIR = 'uploads'
PROCESSED_DIR = 'processed'

if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)
if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)


def extract_audio(input_video, output_audio):
    """Extracts audio from a video file using FFmpeg."""
    ffmpeg.input(input_video).output(output_audio).run(overwrite_output=True)


def transcribe(audio):
    """Transcribes audio using Whisper AI."""
    model = WhisperModel("small", device="cpu")
    segments, info = model.transcribe(audio)
    return "en", list(segments)


def translate_text(text, target_language):
    """Translates text into a target language using Google Translate."""
    translator = Translator()
    return translator.translate(text, dest=target_language).text


def format_time(seconds):
    """Converts time in seconds to SRT time format."""
    hours = math.floor(seconds / 3600)
    minutes = math.floor((seconds % 3600) / 60)
    seconds = math.floor(seconds % 60)
    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def generate_srt(segments, lang, filename):
    """Generates an SRT file from subtitle segments."""
    srt_file = f"{filename}.{lang}.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments):
            f.write(f"{i+1}\n{format_time(segment['start'])} --> {format_time(segment['end'])}\n{segment['text']}\n\n")
    return srt_file

def overlay_subtitles(input_video, srt_file, output_video, output_with_audio, audio_file):
    """Overlays subtitles on video frames using OpenCV and merges original audio using FFmpeg."""
    temp_video = output_video.replace(".mp4", "_temp.mp4")  # Temporary file without audio

    # Process video with OpenCV
    cap = cv2.VideoCapture(input_video)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, cap.get(cv2.CAP_PROP_FPS),
                           (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
    subtitles = parse_srt(srt_file)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        for sub in subtitles:
            if sub["start"] <= current_time <= sub["end"]:
                cv2.putText(frame, sub["text"], (50, int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) - 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                break
        out.write(frame)

    cap.release()
    out.release()

    # Merge original audio using FFmpeg via subprocess
    command = [
        "ffmpeg", "-y", "-i", temp_video, "-i", audio_file,
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0", "-strict", "experimental", output_with_audio
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Remove temporary video file without audio
    os.remove(temp_video)



def parse_srt(srt_file):
    """Parses an SRT file and returns subtitle segments."""
    with open(srt_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    subtitles = []
    entry = {}
    for line in lines:
        line = line.strip()
        if '-->' in line:
            start, end = line.split(' --> ')
            entry = {"start": time_to_seconds(start), "end": time_to_seconds(end)}
        elif line:
            entry["text"] = entry.get("text", "") + " " + line
        else:
            subtitles.append(entry)
            entry = {}
    return subtitles


def time_to_seconds(time_str):
    """Converts SRT time format to seconds."""
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

@app.route('/', methods=['GET', 'POST'])
def upload():
    """Handles video upload and subtitle generation."""
    if request.method == 'POST':
        video = request.files['video']
        if video:
            video_name = os.path.splitext(video.filename)[0]

            # Create directories
            upload_folder = os.path.join(UPLOADS_DIR, video_name)
            processed_folder = os.path.join(PROCESSED_DIR, video_name)
            os.makedirs(upload_folder, exist_ok=True)
            os.makedirs(processed_folder, exist_ok=True)

            # Save original video in uploads/
            video_path = os.path.join(processed_folder, "original.mp4")
            video.save(video_path)

            # Extract audio and save in uploads/
            audio_path = os.path.join(upload_folder, "audio.wav")
            extract_audio(video_path, audio_path)

            # Transcribe audio
            lang, segments = transcribe(audio_path)

            # Save English subtitles in uploads/
            english_srt = generate_srt([{"start": seg.start, "end": seg.end, "text": seg.text} for seg in segments], 'en', os.path.join(upload_folder, "en"))

            # Generate and save translated subtitles in uploads/
            languages = ['fr', 'de']
            subtitle_files = {}
            for lang_code in languages:
                translated_segments = [{"start": seg.start, "end": seg.end, "text": translate_text(seg.text, lang_code)} for seg in segments]
                subtitle_files[lang_code] = generate_srt(translated_segments, lang_code, os.path.join(upload_folder, lang_code))

            # Overlay subtitles and save only processed videos in processed/
            overlay_subtitles(video_path, english_srt, os.path.join(processed_folder, "en.mp4"), os.path.join(processed_folder, "en_audio.mp4"), audio_path)
            overlay_subtitles(video_path, subtitle_files['fr'], os.path.join(processed_folder, "fr.mp4"), os.path.join(processed_folder, "fr_audio.mp4"), audio_path)
            overlay_subtitles(video_path, subtitle_files['de'], os.path.join(processed_folder, "de.mp4"), os.path.join(processed_folder, "de_audio.mp4"), audio_path)

            flash('Processing complete!', 'success')
            return redirect(url_for('videos'))

    return render_template('upload.html')




@app.route('/videos')
def videos():
    video_folders = [f for f in os.listdir(PROCESSED_DIR) if os.path.isdir(os.path.join(PROCESSED_DIR, f))]
    return render_template('videos.html', videos=video_folders)


@app.route('/processed/<path:filename>')
def processed_file(filename):
    return send_from_directory(PROCESSED_DIR, filename)

@app.route('/view_video/<filename>')
def view_video(filename):
    """Displays the four versions of a selected video."""
    return render_template('view_video.html', filename=filename)



if __name__ == '__main__':
    app.run(debug=True)
