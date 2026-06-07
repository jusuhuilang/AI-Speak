# ✈️ AI 英语口语陪练 - 出行助手

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Gradio](https://img.shields.io/badge/Gradio-6.16.0-orange)](https://gradio.app/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> 基于大语言模型的智能英语陪练应用，专为旅行场景设计。支持语音对话、自动情感识别、难度自适应和课后总结报告，帮助用户在机场、酒店、交通等场景中自信开口说英语。

## 🎥 演示视频

[![观看Demo](https://img.shields.io/badge/▶️-点击观看%20Demo-ff69b4)](https://b23.tv/nQoxFXZ)

> 3分钟快速了解所有功能：文字对话、语音识别、自动弹图、难度自适应、雷达图报告。

## ✨ 主要功能

| 模块 | 说明 |
|------|------|
| 🗣️ **语音对话** | 使用 Vosk 离线英文语音识别（40MB 模型），隐私安全 |
| 🤖 **大模型对话** | 集成 DeepSeek API，针对出行场景优化 System Prompt |
| 🔊 **语音合成** | Edge TTS 实时播放 AI 回复语音 |
| 😟 **自动情感识别** | 分析用户录音的语速、停顿、音量，低信心时自动弹出场景提示图片 |
| 🎯 **难度自适应** | 基于最近5次语法正确率动态调整 AI 回复难度（简单/普通/挑战） |
| 📊 **课后总结报告** | 生成雷达图（流利度、词汇、语法、发音） + 高频错误列表 |
| 💬 **文字/语音混合输入** | 支持键盘打字或麦克风录音，自由切换 |
| 🗂️ **对话历史管理** | 一键清除历史，重新开始 |

## 📸 界面预览

（可在此处插入一张应用截图，例如 `assets/screenshot.png`）

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/jusuhuilang/AI-Speak.git
cd AI-Speak
2. 创建并激活虚拟环境（推荐）
Windows:

bash
python -m venv venv
venv\Scripts\activate
Linux / Mac:

bash
python3 -m venv venv
source venv/bin/activate
3. 安装依赖
bash
pip install -r requirements.txt
首次运行时会自动下载 Vosk 英文模型（约 40MB）。如果网络不稳定，也可手动下载并放入项目目录。

4. 配置 API 密钥
本项目需要 DeepSeek API 密钥。请通过环境变量设置，不要硬编码在代码中。

Windows (PowerShell):

powershell
$env:DEEPSEEK_API_KEY="your-api-key"
Linux / Mac:

bash
export DEEPSEEK_API_KEY="your-api-key"
5. 运行应用
bash
python main.py
浏览器会自动打开 http://127.0.0.1:7860。

🧩 项目结构
text
AI-Speak/
├── main.py               # Gradio 主界面，整合所有功能
├── config.py             # 配置文件（API Key、提示词、阈值、场景关键词）
├── utils.py              # DeepSeek API 调用封装
├── asr.py                # Vosk 语音识别（返回文本 + 音频特征）
├── tts.py                # Edge TTS 语音合成
├── emotion.py            # 音频信心度分析（语速、停顿、音量）
├── grammar.py            # 语法检查接口（模拟 / 可替换为真实 LanguageTool）
├── assets/               # 场景提示图片（机场、酒店、交通、通用）
├── requirements.txt
└── README.md
⚙️ 配置说明
所有重要配置都在 config.py 中：

DEEPSEEK_API_KEY：从环境变量读取

SYSTEM_PROMPT：默认出行助手提示词（可在难度自适应中覆盖）

CONFIDENCE_THRESHOLD：自动弹图阈值（默认 0.4）

SCENE_KEYWORDS / HINT_IMAGE_MAP：场景关键词与图片路径映射

PROMPT_EASY / MEDIUM / HARD：难度自适应对应的系统提示词

🧪 测试与演示
文字对话 + 语法记录
输入：I go to the airport yesterday.
AI 正常回复，同时后台记录该语法错误，后续可在总结报告中查看。

语音 + 自动情感识别
点击麦克风，故意慢速、犹豫地说 I... um... hotel...
系统会自动分析语速、停顿、音量，当信心度低于阈值时，弹出一张酒店场景的提示图片。

难度自适应
连续发送多个正确句子（正确率高），AI 回复更自然、开放；
连续发送多个错误句子（正确率低），AI 回复会简化为短句、多问 Yes/No 问题。

课后总结报告
对话结束后，点击“生成总结报告”，显示雷达图和高频语法错误列表。

📝 已知问题与未来计划
语法检查：因网络限制，当前使用模拟版本（随机返回错误）。项目已预留接口，只需替换 grammar.py 中的 check_grammar 函数即可接入真实 LanguageTool（本地或 API）。

实时流式弹图：当前为录音结束后分析。未来可升级为流式 VAD 实现说话过程中实时提示。

发音评分：目前用信心度代替，后续可接入开源发音评测模型。

🤝 贡献
欢迎提交 Issue 和 Pull Request。请遵守以下规范：

每个功能单独 PR

Commit 消息格式：feat: xxx / fix: xxx

每日至少一次 commit

不硬编码密钥

📄 开源协议
本项目使用 MIT License。

祝你口语练习愉快！
If you have any questions, feel free to open an issue.