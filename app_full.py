import os
import asyncio
import tempfile
import json
import wave
from openai import OpenAI
import gradio as gr
import edge_tts
from vosk import Model, KaldiRecognizer

# ========== 1. 配置 DeepSeek ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    # 测试时可临时写入，提交前务必改为环境变量
    DEEPSEEK_API_KEY = "sk-你的真实key"  # 替换成你的 Key

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1",
    timeout=30,
    max_retries=2
)

SYSTEM_PROMPT = (
    "You are a friendly travel assistant. "
    "Help users with airport procedures (check-in, security, baggage), hotel services (booking, check-in, room service), "
    "and city transportation (subway, bus, taxi, walking directions). "
    "Keep responses short (1-2 sentences). Ask clarifying questions when needed. "
    "After 5 exchanges, say 'Safe travels! Enjoy your trip.' to conclude."
)

# ========== 2. TTS (Edge TTS) ==========
async def _text_to_speech(text: str, voice: str = "en-US-JennyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name
    await communicate.save(tmp_path)
    return tmp_path

def text_to_speech_sync(text: str):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_text_to_speech(text))
    except Exception as e:
        print(f"TTS 错误: {e}")
        return None
    finally:
        loop.close()

# ========== 3. Vosk 语音识别 ==========
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"
if not os.path.exists(VOSK_MODEL_PATH):
    raise ValueError(f"找不到 Vosk 模型: {VOSK_MODEL_PATH}，请下载并解压到当前目录")

vosk_model = Model(VOSK_MODEL_PATH)

def transcribe_audio(audio_file_path):
    if not audio_file_path:
        return ""
    try:
        wf = wave.open(audio_file_path, "rb")
        rec = KaldiRecognizer(vosk_model, wf.getframerate())
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

# ========== 4. DeepSeek 对话 ==========
def chat_with_deepseek(messages):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek API 错误: {e}")
        return f"Sorry, I'm having trouble connecting. Please try again later."

# ========== 5. Gradio 界面 ==========
with gr.Blocks(title="AI 英语口语陪练 - 出行助手", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ✈️ AI 英语口语陪练（出行助手）")
    gr.Markdown("通过语音或文字练习机场、酒店、交通场景的英语对话。")
    
    chatbot = gr.Chatbot(label="对话记录", height=400)
    
    with gr.Row():
        audio_input = gr.Audio(sources=["microphone"], type="filepath", label="🎙️ 点击录音")
        text_input = gr.Textbox(label="或直接输入文字", placeholder="例如: How can I get to the airport?", scale=2)
    
    with gr.Row():
        send_voice_btn = gr.Button("发送录音", variant="secondary")
        send_text_btn = gr.Button("发送文字", variant="primary")
        low_confidence_btn = gr.Button("😟 模拟犹豫 (显示菜单图片)")
        clear_btn = gr.Button("清除对话历史")
    
    menu_img = gr.Image(value=None, label="🗺️ 出行提示", visible=False)
    audio_output = gr.Audio(label="AI 语音回复", autoplay=True, visible=True)
    state = gr.State([])  # 对话历史

    def send_message(user_text, history):
        if not user_text.strip():
            return "", history, history, gr.update(visible=False), None
        history.append({"role": "user", "content": user_text})
        messages_for_api = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            if msg["role"] != "system":
                messages_for_api.append(msg)
        assistant_reply = chat_with_deepseek(messages_for_api)
        history.append({"role": "assistant", "content": assistant_reply})
        audio_path = text_to_speech_sync(assistant_reply)
        return "", history, history, gr.update(visible=False), audio_path

    def process_voice(audio_file, history):
        if audio_file is None:
            return "", history, history, gr.update(visible=False), None
        user_text = transcribe_audio(audio_file)
        if not user_text or "无法" in user_text or "错误" in user_text:
            history.append({"role": "user", "content": f"[语音] {user_text}"})
            assistant_reply = "Sorry, I didn't catch that. Could you please repeat?"
            history.append({"role": "assistant", "content": assistant_reply})
            audio_path = text_to_speech_sync(assistant_reply)
            return "", history, history, gr.update(visible=False), audio_path
        return send_message(user_text, history)

    send_text_btn.click(
        send_message,
        inputs=[text_input, state],
        outputs=[text_input, state, chatbot, menu_img, audio_output]
    )
    
    send_voice_btn.click(
        process_voice,
        inputs=[audio_input, state],
        outputs=[text_input, state, chatbot, menu_img, audio_output]
    )

    def show_menu_image():
        # 使用无防盗链的图片
        img_url = "https://picsum.photos/id/104/300/200"
        return gr.update(visible=True, value=img_url)

    low_confidence_btn.click(show_menu_image, outputs=menu_img)

    def clear_all():
        return [], [], gr.update(visible=False), None, ""

    clear_btn.click(clear_all, outputs=[state, chatbot, menu_img, audio_output, text_input])
    demo.load(lambda: [], outputs=state)

if __name__ == "__main__":
    demo.launch()