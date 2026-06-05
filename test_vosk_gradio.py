import gradio as gr
import json
import wave
from vosk import Model, KaldiRecognizer

# 请确认模型路径正确
MODEL_PATH = "vosk-model-small-en-us-0.15"
model = Model(MODEL_PATH)

def transcribe(audio_file):
    if audio_file is None:
        return "未检测到录音"
    wf = wave.open(audio_file, "rb")
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

demo = gr.Interface(
    fn=transcribe,
    inputs=gr.Audio(sources=["microphone"], type="filepath", label="点击录音"),
    outputs="text",
    title="Vosk 语音识别测试",
    description="说一句英文，测试本地模型是否正常工作"
)

demo.launch()