# asr.py (修改后)
import json
import wave
from vosk import Model, KaldiRecognizer
from config import VOSK_MODEL_PATH
from emotion import analyze_confidence  # 新增

# 加载模型（全局只加载一次）
model = Model(VOSK_MODEL_PATH)

def transcribe_audio(audio_file_path, return_features=False):
    """
    语音识别
    :param audio_file_path: wav 音频文件路径
    :param return_features: 是否返回音频特征字典
    :return: 如果 return_features=False，返回识别文本字符串；否则返回 (text, features_dict)
    """
    if not audio_file_path:
        if return_features:
            return "", {}
        else:
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
        text = result if result else "无法识别"
        
        # 如果需要返回特征
        if return_features:
            features = analyze_confidence(audio_file_path)
            return text, features
        else:
            return text
    except Exception as e:
        error_msg = f"识别错误: {str(e)}"
        if return_features:
            return error_msg, {}
        else:
            return error_msg