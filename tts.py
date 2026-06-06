import asyncio
import tempfile
import edge_tts

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