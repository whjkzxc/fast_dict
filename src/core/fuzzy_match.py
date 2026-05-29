# -*- coding: utf-8 -*-
"""拼写相近词匹配算法"""
from typing import List, Tuple
import difflib


class FuzzyMatcher:
    """模糊匹配器 - 使用difflib进行拼写相似度计算"""

    def __init__(self, word_list: List[str]):
        self.word_list = word_list
        self.suggestions_cache = {}
        # 使用 SequenceMatcher 进行快速匹配
        self._seq_matcher = difflib.SequenceMatcher

    def suggest(self, input_word: str, limit: int = 10) -> List[Tuple[str, int]]:
        """
        获取拼写相近的单词建议

        Args:
            input_word: 用户输入的单词
            limit: 返回建议数量

        Returns:
            List[(单词, 相似度分数)]
        """
        if not input_word or not self.word_list:
            return []

        input_word = input_word.lower().strip()

        # 使用缓存
        cache_key = f"{input_word}_{limit}"
        if cache_key in self.suggestions_cache:
            return self.suggestions_cache[cache_key]

        # 使用difflib进行模糊匹配
        # get_close_matches 返回最相似的n个结果
        close_matches = difflib.get_close_matches(
            input_word,
            self.word_list,
            n=limit,
            cutoff=0.3
        )

        # 计算每个匹配的相似度分数
        results = []
        for word in close_matches:
            # 使用 SequenceMatcher 计算相似度 (0-100)
            matcher = self._seq_matcher(None, input_word, word)
            ratio = matcher.ratio()
            score = int(ratio * 100)
            results.append((word, score))

        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)

        # 过滤掉相似度太低的
        filtered = [(word, score) for word, score in results if score >= 40]

        self.suggestions_cache[cache_key] = filtered
        return filtered

    def suggest_top_n(self, input_word: str, n: int = 10) -> List[str]:
        """获取前N个建议单词（只返回单词）"""
        suggestions = self.suggest(input_word, limit=n)
        return [word for word, _ in suggestions]

    def clear_cache(self):
        """清除缓存"""
        self.suggestions_cache.clear()

    def update_word_list(self, word_list: List[str]):
        """更新单词列表"""
        self.word_list = word_list
        self.clear_cache()
