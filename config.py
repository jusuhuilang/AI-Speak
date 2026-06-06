import os

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


# 系统提示词（出行助手）
SYSTEM_PROMPT = (
    "You are a friendly travel assistant. "
    "Help users with airport procedures (check-in, security, baggage), hotel services (booking, check-in, room service), "
    "and city transportation (subway, bus, taxi, walking directions). "
    "Keep responses short (1-2 sentences). Ask clarifying questions when needed. "
    "After 5 exchanges, say 'Safe travels! Enjoy your trip.' to conclude."
)

# Vosk 模型路径
VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15"

# ========== 自动情感识别配置 ==========
CONFIDENCE_THRESHOLD = 0.3          # 低于此值弹出提示图片
HINT_IMAGE_URL = "https://picsum.photos/id/104/300/200"   # 提示图片URL（可更换）