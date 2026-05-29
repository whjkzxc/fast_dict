# -*- coding: utf-8 -*-
"""大模型查询模块 - 当词典无匹配时调用LLM获取解释"""
import json
from pathlib import Path

from openai import OpenAI


def load_api_config() -> dict:
    """从 model_api.json 加载模型接入配置"""
    config_path = Path(__file__).parent.parent.parent / "model_api.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def query_llm(word: str) -> str:
    """调用大模型获取单词/短语的简短解释（150字以内）"""
    config = load_api_config()

    client = OpenAI(
        api_key=config["api_key"],
        base_url=config["api_base"],
    )

    response = client.chat.completions.create(
        model=config["model"],
        messages=[
            {
                "role": "system",
                "content": "你是一个简洁的词典助手。用户会给你一个单词或短语，请用中文给出简短的解释，包括词性、基本释义和常见用法。回复严格控制在150个汉字以内，不要有多余的寒暄。回复内容不使用任何markdown标记。",
            },
            {
                "role": "user",
                "content": word,
            },
        ],
        max_tokens=2048,
        extra_body={"thinking": {"type": "disabled"}},
    )

    return response.choices[0].message.content.strip()
