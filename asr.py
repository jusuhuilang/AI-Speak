import json
import wave
from vosk import Model, KaldiRecognizer
from config import VOSK_MODEL_PATH

# 加载模型（全局只加载一次）
model = Model(VOSK_MODEL_PATH)

def transcribe_audio(audio_file_path):
    if not audio_file_path:
        return ""
    try:
        wf = wave.open(audio_file_path, "rb")
        rec = KaldiRecognizer(model, wf.getframerate())
        texts = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if 'text' in res and res['text']:
                    texts.append(res['text'])
        final = json.loads(rec.FinalResult())
        if 'text' in final and final['text']:
            texts.append(final['text'])
        result = " ".join(texts).strip()
        return result if result else "无法识别"
    except Exception as e:
        return f"识别错误: {str(e)}"