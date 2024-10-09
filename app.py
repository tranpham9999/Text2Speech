import os
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
import azure.cognitiveservices.speech as speechsdk
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import tempfile

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model (for demonstration)
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Hardcoded user (in a real app, use a database)
users = {
    '1': User('1', 'admin', generate_password_hash('password123'))  # Username: admin, Password: password123
}

# Azure Speech API credentials
SPEECH_KEY = os.getenv('SPEECH_KEY')
SPEECH_REGION = os.getenv('SPEECH_REGION')
ENDPOINT_ID = os.getenv('ENDPOINT_ID')
VOICE_NAME = os.getenv('VOICE_NAME')
OUTPUT_FORMAT = speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3

# Directory to store audio files
AUDIO_DIR = '/home/tranpham/WebAiText2Speech/audio_files'
os.makedirs(AUDIO_DIR, exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple authentication check
        user = next((u for u in users.values() if u.username == username), None)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
@login_required
def synthesize():
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
        return jsonify({"status": "success", "audio_url": f"/audio/{audio_filename}"})  # Return URL to audio file
    else:
        print(f"Synthesis failed: {result.reason}")
        return jsonify({"status": "error", "message": result.reason})

@app.route('/audio/<path:filename>', methods=['GET'])
@login_required
def play_audio(filename):
    return send_file(os.path.join(AUDIO_DIR, filename))

if __name__ == '__main__':
    app.run(debug=True)
