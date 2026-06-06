# grammar.py - 模拟语法检查（跳过真实检查）
import random

def check_grammar(text: str) -> list:
    """模拟语法检查，随机返回错误（用于跳过网络问题）"""
    if not text or not isinstance(text, str):
        return []
    # 模拟 30% 的概率出现一个语法错误
    if random.random() < 0.3:
        return [{
            "message": "动词时态可能不正确（模拟）",
            "replacements": ["went"],
            "context": text,
            "offset": 2
        }]
    return []