import os

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    # 测试时可临时填写，提交前务必改为环境变量
    DEEPSEEK_API_KEY = "sk-你的真实key"  # 仅本地测试用

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