import librosa
import numpy as np

def analyze_confidence(audio_path: str, sample_rate: int = 16000) -> dict:
    """
    分析音频，返回信心度相关的指标和总体信心分数(0~1)
    指标：语速(字/秒)、停顿占比、平均音量(dB)
    """
    y, sr = librosa.load(audio_path, sr=sample_rate)
    
    # 1. 语速：通过过零率估算 (粗略，但足够用于判断快慢)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True)
    if len(onset_frames) < 2:
        speaking_rate = 0.0
    else:
        # 以音素起点数量代替音节，简单估算每秒发音单元数
        duration = len(y) / sr
        speaking_rate = len(onset_frames) / duration   # 单位：个/秒
    
    # 2. 停顿占比：能量低于阈值的帧比例
    energy = librosa.feature.rms(y=y)[0]
    threshold = np.percentile(energy, 20)  # 最低20%能量视为静音或停顿
    pause_frames = (energy < threshold).sum()
    total_frames = len(energy)
    pause_ratio = pause_frames / total_frames if total_frames > 0 else 0
    
    # 3. 平均音量 (dB)
    rms = np.sqrt(np.mean(y**2))
    volume_db = 20 * np.log10(rms + 1e-6)
    
    # 4. 综合信心度打分 (经验公式，可调)
    # 语速慢 -> 低分，停顿多 -> 低分，音量小 -> 低分
    rate_score = min(1.0, speaking_rate / 5.0)     # 假设正常语速约4~5个发音单元/秒
    pause_score = 1.0 - min(1.0, pause_ratio / 0.4) # 停顿超过40%则0分
    volume_score = min(1.0, (volume_db + 60) / 50)   # 范围-60~0dB映射到0~1
    confidence = np.clip(0.2 * rate_score + 0.4 * pause_score + 0.4 * volume_score, 0, 1)
    
    return {
        "speaking_rate": speaking_rate,
        "pause_ratio": pause_ratio,
        "volume_db": volume_db,
        "confidence": confidence
    }