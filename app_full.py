import os
import asyncio
import tempfile
import numpy as np
import librosa
from openai import OpenAI
import gradio as gr
import edge_tts

# ========== 配置 ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("请先设置环境变量 DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

SYSTEM_PROMPT = (
    "You are a friendly restaurant waiter. "
    "Only answer questions related to ordering food. "
    "Keep your responses short (1-2 sentences). "
    "Ask the user what they would like to order. "
    "After 5 rounds of conversation, say 'Thank you for dining with us, goodbye!' to end the conversation."
)

# ========== TTS ==========
async def _text_to_speech(text: str, voice: str = "en-US-JennyNeural"):
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        tmp_path = tmp_file.name
    await communicate.save(tmp_path)
    return tmp_path

def text_to_speech_sync(text: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_text_to_speech(text))
    finally:
        loop.close()

# ========== 对话函数 ==========
def chat_with_deepseek(messages):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ API 错误: {str(e)}"

# ========== Gradio 界面 ==========
custom_css = """
#menu-img {
    border: 2px solid #ff9900;
    border-radius: 10px;
    padding: 5px;
    background-color: #fff8e7;
}
"""

# 注意：theme 和 css 参数移到了 launch() 中
with gr.Blocks(title="AI 英语口语陪练 - 点餐场景") as demo:
    gr.Markdown("# 🍽️ AI 英语口语陪练（点餐场景）")
    gr.Markdown("在下方文本框中用英语点餐，AI 服务员会回复并朗读。点击「模拟犹豫」按钮可查看多模态图片提示。")
    
    # 聊天区域
    chatbot = gr.Chatbot(label="对话记录", height=400)
    
    # 文本输入
    text_input = gr.Textbox(label="你的英语句子", placeholder="例如: I want a burger", lines=2)
    
    # 按钮行
    with gr.Row():
        send_btn = gr.Button("发送", variant="primary")
        low_confidence_btn = gr.Button("😟 模拟犹豫 (显示菜单图片)")
        clear_btn = gr.Button("清除对话历史")
    
    # 多模态图片显示区域（初始隐藏）
    menu_img = gr.Image(value=None, label="🍔 菜单提示", visible=False, elem_id="menu-img")
    
    # 音频输出
    audio_output = gr.Audio(label="AI 语音回复", autoplay=True, visible=True)
    
    # 状态存储对话历史
    state = gr.State([])   # 格式: [{"role": "user", "content": ...}, {"role": "assistant", ...}]
    
    # 发送消息
    def user_send(message, history):
        if not message.strip():
            return "", history, history, False, None
        # 添加用户消息
        history.append({"role": "user", "content": message})
        # 构建 API 消息（包含 system prompt）
        messages_for_api = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history:
            if msg["role"] != "system":
                messages_for_api.append(msg)
        assistant_reply = chat_with_deepseek(messages_for_api)
        history.append({"role": "assistant", "content": assistant_reply})
        # 生成语音
        audio_path = text_to_speech_sync(assistant_reply)
        # 重置图片隐藏
        return "", history, history, False, audio_path
    
    send_btn.click(
        user_send,
        inputs=[text_input, state],
        outputs=[text_input, state, chatbot, menu_img, audio_output]
    )
    
    # 模拟犹豫：显示菜单图片
    def show_menu_image():
        # 使用一个在线汉堡图片示例（你也可以改成本地图片路径）
        menu_img_url = "https://cdn.pixabay.com/photo/2017/08/01/05/43/food-2563543_1280.jpg"
        return gr.update(visible=True, value=menu_img_url)
    
    low_confidence_btn.click(
        show_menu_image,
        outputs=menu_img
    )
    
    # 清除历史
    def clear_all():
        return [], [], None, False, ""
    
    clear_btn.click(
        clear_all,
        outputs=[state, chatbot, audio_output, menu_img, text_input]
    )
    
    # 初始化状态
    demo.load(lambda: [], outputs=state)

if __name__ == "__main__":
    # 将 theme 和 css 放在 launch() 中
    demo.launch(theme=gr.themes.Soft(), css=custom_css)