import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import azure.cognitiveservices.speech as speechsdk
import tempfile

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'mysecretkey')  # Secret key for session management

# Azure Speech API credentials
SPEECH_KEY = os.getenv('SPEECH_KEY')
SPEECH_REGION = os.getenv('SPEECH_REGION')
ENDPOINT_ID = os.getenv('ENDPOINT_ID')
VOICE_NAME = os.getenv('VOICE_NAME')
OUTPUT_FORMAT = speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3

# Directory to store audio files
AUDIO_DIR = '/home/tranpham/WebAiText2Speech/audio_files'
os.makedirs(AUDIO_DIR, exist_ok=True)

# Dummy credentials for login (replace with a more secure system in production)
USER_CREDENTIALS = {
    'admin': 'password123'
}

@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html')  # Show main chat page if logged in
    return redirect(url_for('login'))  # Redirect to login if not logged in

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session['username'] = username  # Set session on successful login
            return redirect(url_for('home'))  # Redirect to the home page
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')  # Display login form

@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear the session
    return redirect(url_for('login'))

@app.route('/synthesize', methods=['POST'])
def synthesize():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    text = request.form['text']  # Get the text from the form

    # Set up Azure Speech configuration
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.endpoint_id = ENDPOINT_ID
    speech_config.speech_synthesis_voice_name = VOICE_NAME
    speech_config.set_speech_synthesis_output_format(OUTPUT_FORMAT)

    # Create a temporary file in the specified directory
    audio_filename = f"{text[:10]}_{os.urandom(4).hex()}.mp3"  # Generate a unique filename based on text
    temp_file_path = os.path.join(AUDIO_DIR, audio_filename)
    print(f"Audio file will be saved to: {temp_file_path}")

    audio_output = speechsdk.audio.AudioOutputConfig(filename=temp_file_path)
    # Create a speech synthesizer
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output)

    # Synthesize speech
    try:
        result = synthesizer.speak_text_async(text).get()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return jsonify({"status": "success", "audio_url":f"/{audio_filename}"})  # Return URL to audio file
    else:
        print(f"Synthesis failed: {result.reason}")
        return jsonify({"status": "error", "message": result.reason})

@app.route('/audio/<path:filename>', methods=['GET'])
def play_audio(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    return send_file(os.path.join(AUDIO_DIR, filename))

if __name__ == '__main__':
    app.run(debug=True)
