import gradio as gr
from config import CONFIDENCE_THRESHOLD, HINT_IMAGE_URL, PROMPT_EASY, PROMPT_MEDIUM, PROMPT_HARD
from tts import text_to_speech_sync
from asr import transcribe_audio
from utils import chat_with_deepseek
from grammar import check_grammar

# ========== 动态难度选择函数 ==========
def get_dynamic_prompt(grammar_records, last_n=5):
    """
    根据最近 last_n 条语法检查记录，返回合适的 System Prompt
    grammar_records: 列表，每个元素是 {"text": ..., "errors": [...]}
    """
    if not grammar_records:
        return PROMPT_MEDIUM   # 初始中等

    # 取最近 last_n 条（或全部）
    recent = grammar_records[-last_n:] if len(grammar_records) >= last_n else grammar_records
    total = len(recent)
    if total == 0:
        return PROMPT_MEDIUM

    # 计算正确次数（无错误视为正确）
    correct = sum(1 for record in recent if not record.get("errors"))
    accuracy = correct / total

    if accuracy < 0.4:
        return PROMPT_EASY
    elif accuracy < 0.7:
        return PROMPT_MEDIUM
    else:
        return PROMPT_HARD

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
        clear_btn = gr.Button("清除对话历史")

    menu_img = gr.Image(value=None, label="🗺️ 出行提示", visible=False)
    audio_output = gr.Audio(label="AI 语音回复", autoplay=True, visible=True)
    state = gr.State([])           # 对话历史
    grammar_state = gr.State([])   # 语法错误记录

    def send_message(user_text, history, grammar_records):
        if not user_text.strip():
            return "", history, history, grammar_records, gr.update(visible=False), None

        # 语法检查并记录
        errors = check_grammar(user_text)
        if errors:
            grammar_records.append({
                "text": user_text,
                "errors": errors
            })

        history.append({"role": "user", "content": user_text})

        # 动态生成 System Prompt
        dynamic_prompt = get_dynamic_prompt(grammar_records)
        messages_for_api = [{"role": "system", "content": dynamic_prompt}]
        for msg in history:
            if msg["role"] != "system":
                messages_for_api.append(msg)

        assistant_reply = chat_with_deepseek(messages_for_api)
        history.append({"role": "assistant", "content": assistant_reply})
        audio_path = text_to_speech_sync(assistant_reply)
        return "", history, history, grammar_records, gr.update(visible=False), audio_path

    def process_voice(audio_file, history, grammar_records):
        print(f"=== 收到音频文件: {audio_file} ===")
        if audio_file is None:
            return "", history, history, grammar_records, gr.update(visible=False), None

        # 语音识别 + 获取信心度特征
        user_text, features = transcribe_audio(audio_file, return_features=True)
        confidence = features.get("confidence", 0.0)
        print(f"识别文本: {user_text}")
        print(f"信心度: {confidence}")
        print(f"特征: {features}")

        # 根据信心度决定是否弹出提示图片
        if confidence < CONFIDENCE_THRESHOLD and user_text not in ["无法识别", "识别错误"] and not user_text.startswith("识别错误"):
            menu_update = gr.update(visible=True, value=HINT_IMAGE_URL)
        else:
            menu_update = gr.update(visible=False)

        # 处理识别失败的情况
        if not user_text or "无法" in user_text or "错误" in user_text:
            history.append({"role": "user", "content": f"[语音] {user_text}"})
            assistant_reply = "Sorry, I didn't catch that. Could you please repeat?"
            history.append({"role": "assistant", "content": assistant_reply})
            audio_path = text_to_speech_sync(assistant_reply)
            return "", history, history, grammar_records, menu_update, audio_path

        # 语法检查并记录（仅对识别成功的文本）
        errors = check_grammar(user_text)
        if errors:
            grammar_records.append({
                "text": user_text,
                "errors": errors
            })

        # 正常识别，进行对话
        history.append({"role": "user", "content": user_text})

        # 动态生成 System Prompt
        dynamic_prompt = get_dynamic_prompt(grammar_records)
        messages_for_api = [{"role": "system", "content": dynamic_prompt}]
        for msg in history:
            if msg["role"] != "system":
                messages_for_api.append(msg)

        assistant_reply = chat_with_deepseek(messages_for_api)
        history.append({"role": "assistant", "content": assistant_reply})
        audio_path = text_to_speech_sync(assistant_reply)
        return "", history, history, grammar_records, menu_update, audio_path

    # 绑定事件
    send_text_btn.click(
        send_message,
        inputs=[text_input, state, grammar_state],
        outputs=[text_input, state, chatbot, grammar_state, menu_img, audio_output]
    )

    send_voice_btn.click(
        process_voice,
        inputs=[audio_input, state, grammar_state],
        outputs=[text_input, state, chatbot, grammar_state, menu_img, audio_output]
    )

    def clear_all():
        return [], [], [], gr.update(visible=False), None, ""

    clear_btn.click(
        clear_all,
        outputs=[state, chatbot, grammar_state, menu_img, audio_output, text_input]
    )
    demo.load(lambda: ([], []), outputs=[state, grammar_state])

if __name__ == "__main__":
    demo.launch()