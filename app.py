import os
from flask import Flask, render_template, request, jsonify, send_file
import azure.cognitiveservices.speech as speechsdk
import tempfile

app = Flask(__name__)

# Azure Speech API credentials
SPEECH_KEY = 'df6e49cb8a80431886c95fc93b5c4be2'
SPEECH_REGION = 'southeastasia'
ENDPOINT_ID = 'bb4fe2ad-2866-42f5-9205-769f5349a4e3'
VOICE_NAME = "Haindh Voice DemoNeural"
OUTPUT_FORMAT = speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3

# Directory to store audio files
AUDIO_DIR = '/home/tranpham/WebAiText2Speech/audio_files'
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
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
        return jsonify({"status": "success", "audio_url":f"/{audio_filename}"})  # Return URL to audio file
    else:
        print(f"Synthesis failed: {result.reason}")
        return jsonify({"status": "error", "message": result.reason})

@app.route('/audio/<path:filename>', methods=['GET'])
def play_audio(filename):
    return send_file(os.path.join(AUDIO_DIR, filename))
if __name__ == '__main__':
    app.run(debug=True)