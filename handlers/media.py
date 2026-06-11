"""語音相關: 語音轉文字、語音翻譯"""

import requests
from openai import OpenAI
from pydub import AudioSegment
import google.cloud.texttospeech as tts

from config import ACCESS_TOKEN, OPENAI_TOKEN
import gcs


def speech_to_text(message_id) -> str:
    """LINE 語音訊息轉文字"""
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    req = requests.get(f'https://api-data.line.me/v2/bot/message/{message_id}/content', headers=headers)
    with open("temp.wav", "wb") as f:
        f.write(req.content)
    with open("temp.wav", "rb") as f:
        openai_client = OpenAI(api_key=OPENAI_TOKEN)
        transcript = openai_client.audio.transcriptions.create(model="whisper-1", file=f)
    return transcript.text


def interpretation(orig_txt: str, tk):
    """語音翻譯（翻成繁體中文 + TTS）"""
    openai_client = OpenAI(api_key=OPENAI_TOKEN)
    completion = openai_client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": "請將以下文字翻譯成繁體中文。\n" + orig_txt}]
    )
    msg = completion.choices[0].message.content
    audio_duration = _text_to_speech("cmn-TW-Wavenet-C", msg)
    gcs.upload_blob("asia.artifacts.watermelon-368305.appspot.com", "./text-to-speech.wav", f'text-to-speech/text-to-speech{tk}.wav')
    gcs.make_blob_public("asia.artifacts.watermelon-368305.appspot.com", f'text-to-speech/text-to-speech{tk}.wav')
    reply_msg = (
        {"type": "text", "text": msg},
        {'type': 'audio', 'originalContentUrl': f'https://storage.googleapis.com/asia.artifacts.watermelon-368305.appspot.com/text-to-speech/text-to-speech{tk}.wav', 'duration': audio_duration},
    )
    return reply_msg


def _text_to_speech(voice_name: str, text: str) -> int:
    """Google Cloud TTS，回傳音訊長度(ms)"""
    language_code = "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(language_code=language_code, name=voice_name)
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(input=text_input, voice=voice_params, audio_config=audio_config)

    filename = "text-to-speech.wav"
    with open(filename, "wb") as out:
        out.write(response.audio_content)

    audio = AudioSegment.from_file(filename, format="wav")
    return len(audio)
