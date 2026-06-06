import gradio as gr
from config import SYSTEM_PROMPT
from tts import text_to_speech_sync
from asr import transcribe_audio
from utils import chat_with_deepseek

# ========== Gradio 界面 ==========
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
        img_url = "https://picsum.photos/id/104/300/200"
        return gr.update(visible=True, value=img_url)

    low_confidence_btn.click(show_menu_image, outputs=menu_img)

    def clear_all():
        return [], [], gr.update(visible=False), None, ""

    clear_btn.click(clear_all, outputs=[state, chatbot, menu_img, audio_output, text_input])
    demo.load(lambda: [], outputs=state)

if __name__ == "__main__":
    demo.launch()