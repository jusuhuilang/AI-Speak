import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import os
from config import CONFIDENCE_THRESHOLD, PROMPT_EASY, PROMPT_MEDIUM, PROMPT_HARD
from config import SCENE_KEYWORDS, HINT_IMAGE_MAP
from tts import text_to_speech_sync
from asr import transcribe_audio
from utils import chat_with_deepseek
from grammar import check_grammar

# ========== 动态难度选择函数 ==========
def get_dynamic_prompt(grammar_records, last_n=5):
    if not grammar_records:
        return PROMPT_MEDIUM
    recent = grammar_records[-last_n:] if len(grammar_records) >= last_n else grammar_records
    total = len(recent)
    if total == 0:
        return PROMPT_MEDIUM
    correct = sum(1 for record in recent if not record.get("errors"))
    accuracy = correct / total
    if accuracy < 0.4:
        return PROMPT_EASY
    elif accuracy < 0.7:
        return PROMPT_MEDIUM
    else:
        return PROMPT_HARD

# ========== 场景图片选择函数 ==========
def get_scene_image(history):
    recent_user_msgs = [msg["content"] for msg in history[-3:] if msg["role"] == "user"]
    all_text = " ".join(recent_user_msgs).lower()
    for scene, keywords in SCENE_KEYWORDS.items():
        for kw in keywords:
            if kw in all_text:
                return HINT_IMAGE_MAP[scene]
    return HINT_IMAGE_MAP["general"]

# ========== 生成报告函数（使用临时文件，返回 Markdown 文本） ==========
def generate_report(history, grammar_records, confidence_records):
    print("生成报告...")
    # 计算各项指标
    fluency = np.mean(confidence_records) if confidence_records else 0.5
    user_messages = [msg["content"] for msg in history if msg["role"] == "user" and not msg["content"].startswith("[语音]")]
    avg_len = np.mean([len(msg.split()) for msg in user_messages]) if user_messages else 0
    vocabulary = min(1.0, avg_len / 20.0)
    total_sentences = len(grammar_records)
    error_sentences = sum(1 for r in grammar_records if r.get("errors"))
    grammar_score = 1.0 - (error_sentences / total_sentences) if total_sentences > 0 else 0.5
    pronunciation = fluency

    scores = [fluency, vocabulary, grammar_score, pronunciation]
    labels = ['Fluency', 'Vocabulary', 'Grammar', 'Pronunciation']

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    scores += scores[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    ax.fill(angles, scores, color='skyblue', alpha=0.4)
    ax.plot(angles, scores, color='blue', linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("User Performance", size=14, pad=20)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
        plt.savefig(tmpfile.name, format='png', bbox_inches='tight')
        tmp_path = tmpfile.name
    plt.close(fig)

    # 高频错误统计
    error_counts = {}
    for record in grammar_records:
        for err in record.get("errors", []):
            msg = err.get("message", "Unknown error")
            error_counts[msg] = error_counts.get(msg, 0) + 1
    if error_counts:
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        error_text = "**高频错误建议：**\n" + "\n".join([f"- {msg} (出现 {count} 次)" for msg, count in sorted_errors])
    else:
        error_text = "太棒了！没有发现语法错误，继续保持！"

    print("报告生成完成，错误文本:", error_text)
    return gr.update(visible=True, value=tmp_path), gr.update(visible=True, value=error_text)

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
        report_btn = gr.Button("📊 生成总结报告", variant="primary")

    menu_img = gr.Image(value=None, label="🗺️ 出行提示", visible=False, height=500, width=600)
    audio_output = gr.Audio(label="AI 语音回复", autoplay=True, visible=True)
    report_img = gr.Image(label="能力雷达图", visible=False)
    # 关键修改：将 Textbox 改为 Markdown，避免加载问题
    report_text = gr.Markdown(label="语法错误总结", visible=False)

    state = gr.State([])           # 对话历史
    grammar_state = gr.State([])   # 语法错误记录
    confidence_state = gr.State([]) # 信心度记录（流利度）

    def send_message(user_text, history, grammar_records, confidence_records):
        if not user_text.strip():
            return "", history, history, grammar_records, confidence_records, gr.update(visible=False), None

        errors = check_grammar(user_text)
        if errors:
            grammar_records.append({"text": user_text, "errors": errors})
        confidence_records.append(0.8)

        history.append({"role": "user", "content": user_text})
        dynamic_prompt = get_dynamic_prompt(grammar_records)
        messages_for_api = [{"role": "system", "content": dynamic_prompt}]
        for msg in history:
            if msg["role"] != "system":
                messages_for_api.append(msg)
        assistant_reply = chat_with_deepseek(messages_for_api)
        history.append({"role": "assistant", "content": assistant_reply})
        audio_path = text_to_speech_sync(assistant_reply)
        return "", history, history, grammar_records, confidence_records, gr.update(visible=False), audio_path

    def process_voice(audio_file, history, grammar_records, confidence_records):
        print(f"=== 收到音频文件: {audio_file} ===")
        if audio_file is None:
            return "", history, history, grammar_records, confidence_records, gr.update(visible=False), None

        user_text, features = transcribe_audio(audio_file, return_features=True)
        confidence = features.get("confidence", 0.0)
        print(f"识别文本: {user_text}")
        print(f"信心度: {confidence}")
        print(f"特征: {features}")

        if confidence < CONFIDENCE_THRESHOLD and user_text not in ["无法识别", "识别错误"] and not user_text.startswith("识别错误"):
            image_path = get_scene_image(history)
            menu_update = gr.update(visible=True, value=image_path)
        else:
            menu_update = gr.update(visible=False)

        if not user_text or "无法" in user_text or "错误" in user_text:
            history.append({"role": "user", "content": f"[语音] {user_text}"})
            assistant_reply = "Sorry, I didn't catch that. Could you please repeat?"
            history.append({"role": "assistant", "content": assistant_reply})
            audio_path = text_to_speech_sync(assistant_reply)
            return "", history, history, grammar_records, confidence_records, menu_update, audio_path

        confidence_records.append(confidence)

        errors = check_grammar(user_text)
        if errors:
            grammar_records.append({"text": user_text, "errors": errors})

        history.append({"role": "user", "content": user_text})
        dynamic_prompt = get_dynamic_prompt(grammar_records)
        messages_for_api = [{"role": "system", "content": dynamic_prompt}]
        for msg in history:
            if msg["role"] != "system":
                messages_for_api.append(msg)
        assistant_reply = chat_with_deepseek(messages_for_api)
        history.append({"role": "assistant", "content": assistant_reply})
        audio_path = text_to_speech_sync(assistant_reply)
        return "", history, history, grammar_records, confidence_records, menu_update, audio_path

    # 清除所有状态：注意返回顺序与 outputs 一致
    def clear_all():
        return ([], [], [], [], 
                gr.update(visible=False), None, "", 
                gr.update(visible=False), gr.update(visible=False, value=""))

    def on_report_click(history, grammar_records, confidence_records):
        img_update, text_update = generate_report(history, grammar_records, confidence_records)
        return img_update, text_update

    # 绑定事件
    send_text_btn.click(
        send_message,
        inputs=[text_input, state, grammar_state, confidence_state],
        outputs=[text_input, state, chatbot, grammar_state, confidence_state, menu_img, audio_output]
    )

    send_voice_btn.click(
        process_voice,
        inputs=[audio_input, state, grammar_state, confidence_state],
        outputs=[text_input, state, chatbot, grammar_state, confidence_state, menu_img, audio_output]
    )

    clear_btn.click(
        clear_all,
        outputs=[state, chatbot, grammar_state, confidence_state, menu_img, audio_output, text_input, report_img, report_text]
    )

    report_btn.click(
        on_report_click,
        inputs=[state, grammar_state, confidence_state],
        outputs=[report_img, report_text]
    )

    demo.load(lambda: ([], [], []), outputs=[state, grammar_state, confidence_state])

if __name__ == "__main__":
    demo.launch()