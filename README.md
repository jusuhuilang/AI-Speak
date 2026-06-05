# AI 英语口语陪练 (AI-Speak)

> 一个基于 DeepSeek + Edge TTS + Gradio 的英语口语练习工具，支持点餐场景对话、语音输入、多模态提示、难度自适应和课后总结。

## Demo 视频
[视频链接（录制后填入）](https://www.bilibili.com/xxx)

## 原创功能
- **多模态情感提示**：根据用户语音语速、停顿、音量自动弹出菜单图片，降低焦虑。
- **难度自适应**：根据连续5句正确率动态调整 AI 回复语速和句式复杂度。
- **课后量化报告**：生成雷达图，展示流利度、词汇、语法、发音得分及错误分析。

## 技术栈
- 大语言模型：DeepSeek API
- 语音识别：SpeechRecognition (Google Web Speech API)
- 语音合成：Edge TTS
- 前端界面：Gradio
- 音频分析：Librosa
- 代码托管：GitHub

## 第三方库引用
- openai, gradio, edge-tts, speechrecognition, librosa, numpy, matplotlib

## 本地运行指南
1. 克隆仓库：`git clone https://github.com/jusuhuilang/AI-Speak.git`
2. 进入目录：`cd AI-Speak`
3. 创建虚拟环境：`python -m venv venv`
4. 激活虚拟环境：
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
5. 安装依赖：`pip install -r requirements.txt`
6. 设置 DeepSeek API Key 环境变量：
   - Windows PowerShell: `$env:DEEPSEEK_API_KEY="sk-你的key"`
7. 运行：`python app_full.py`
8. 浏览器打开 `http://127.0.0.1:7860`

## 项目结构