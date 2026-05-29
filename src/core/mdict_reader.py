# -*- coding: utf-8 -*-
"""MDict 词典文件读取器 (处理加密文件)"""
import struct
import json
import re
import html
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from readmdict import MDX, MDD
    HAS_READMDICT = True
except ImportError:
    HAS_READMDICT = False


class MDictInfo:
    """MDict文件信息"""

    @staticmethod
    def check_encrypted(mdx_path: str) -> Tuple[bool, str, int]:
        """
        检查MDX文件是否加密
        返回: (是否加密, 词典名称, 词条数量)
        """
        try:
            with open(mdx_path, 'rb') as f:
                # 读取头部大小 (大端序)
                header_size = struct.unpack('>I', f.read(4))[0]

                # 读取头部
                header_data = f.read(header_size)
                header_text = header_data.decode('utf-16-le', errors='ignore')

                # 解析信息
                title = "Unknown"
                encrypted = False
                key_count = 0

                # 从XML格式的头部提取信息
                title_match = re.search(r'Title=["\']([^"\']+)["\']', header_text)
                if title_match:
                    title = title_match.group(1)

                enc_match = re.search(r'Encrypted=["\']?(\d+)["\']?', header_text)
                if enc_match:
                    encrypted = int(enc_match.group(1)) > 0

                key_count_match = re.search(r'KeyCount=["\']?(\d+)["\']?', header_text)
                if key_count_match:
                    key_count = int(key_count_match.group(1))

                return encrypted, title, key_count

        except Exception as e:
            print(f"检查MDX文件出错: {e}")
            return True, "Error", 0


class MDXReader:
    """MDX 词典读取器"""

    def __init__(self, mdx_path: str, mdd_path: str = None):
        if not HAS_READMDICT:
            raise ImportError("请先安装 readmdict: pip install readmdict python-lzo")

        self.mdx_path = Path(mdx_path)
        self.mdd_path = Path(mdd_path) if mdd_path else None

        # 加载 MDX
        print(f"正在加载 MDX 文件: {self.mdx_path.name}")
        self.mdx = MDX(str(self.mdx_path))
        print(f"加载完成，共 {len(self.mdx)} 个词条")

        # 构建快速查找索引
        print("正在构建索引...")
        self._index = {}
        for key, value in self.mdx.items():
            if isinstance(key, bytes):
                try:
                    word = key.decode('utf-8')
                except UnicodeDecodeError:
                    continue
            else:
                word = str(key)
            self._index[word.lower()] = value
        print(f"索引构建完成")

        # 加载 MDD (资源文件，如图片、音频等)
        self.mdd = None
        if self.mdd_path and self.mdd_path.exists():
            print(f"正在加载 MDD 文件: {self.mdd_path.name}")
            self.mdd = MDD(str(self.mdd_path))
            print(f"MDD 加载完成")

    @property
    def word_count(self) -> int:
        """获取词条数量"""
        return len(self.mdx)

    def get_word_list(self, limit: int = None) -> List[str]:
        """获取单词列表"""
        words = list(self._index.keys())
        if limit:
            return words[:limit]
        return words

    def lookup(self, word: str) -> Optional[str]:
        """查询单词，返回 HTML 格式的释义"""
        word_lower = word.lower()

        # 使用索引快速查找
        if word_lower in self._index:
            value = self._index[word_lower]
            if isinstance(value, bytes):
                try:
                    return value.decode('utf-8')
                except UnicodeDecodeError:
                    return value.decode('utf-8', errors='ignore')
            return str(value)
        return None

    def get_definition_html(self, word: str) -> str:
        """获取单词的格式化 HTML 释义"""
        content = self.lookup(word)
        if not content:
            return None

        # 清理BOM字符和特殊控制字符（这些会导致显示异常）
        content = content.replace('﻿', '')  # UTF-8 BOM
        # 移除其他控制字符（保留换行和制表符）
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')

        # 清理 HTML，使其适合在 QLabel 中显示
        # 移除XML声明和DOCTYPE
        content = re.sub(r'<\?xml[^>]*>', '', content)
        content = re.sub(r'<!DOCTYPE[^>]*>', '', content)
        content = re.sub(r'<!ENTITY[^>]*>', '', content)

        # 移除 <html> 和 <body> 标签（保留内容）
        content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</html>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
        content = re.sub(r'</body>', '', content, flags=re.IGNORECASE)

        # 移除 <head> 标签及其内容
        content = re.sub(r'<head>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # 移除 script 标签
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # 移除 style 标签
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # 将自定义标签映射到标准 HTML 标签
        tag_mapping = {
            # 单词和音标相关
            'h': 'b',           # 单词本身加粗
            'pos': 'i',         # 词性斜体
            'phon': 'span',     # 音标
            'phon-blk': 'span',
            'pron-g': 'span',
            'pron-g-blk': 'span',
            'pron-gs': 'span',
            'v': 'span',        # 变形形式

            # 例句相关
            'x': 'span',        # 例句
            'rx': 'span',       # 例句块
            'rx-g': 'div',      # 例句组
            'xr-g': 'div',
            'sn-g': 'div',
            'sn-blk': 'div',

            # 释义相关
            'def': 'div',       # 释义
            'res-g': 'div',

            # 其他容器标签
            'unbox': 'div',     # 信息框
            'body': 'div',
            'title': 'b',
            'ul': 'ul',
            'li': 'li',
            'und': 'li',

            # 强调和标签
            'eb': 'b',          # 英语单词加粗
            'reg': 'i',         # 注册词斜体
            'gl': 'i',          # 释义斜体
            'cl': 'span',

            # 分隔符和符号
            'chnsep': 'span',   # 中英文分隔符
            'chn': 'span',      # 中文
            'xsymb': 'span',    # 符号
            'arrow': 'span',    # 箭头
            'fthzmark': '',     # 非特殊字符标记（移除）

            # 变形和形式
            'if': 'i',          # 不规则变形
            'infl': 'i',
            'form': 'i',

            # 地区和标签
            'geo': 'span',      # 地区标签
            'brelabel': 'span', # 英式标签
            'namelabel': 'span', # 名称标签
            'vgslabel': 'span',
            'q': 'span',
        }

        # 先处理需要特殊处理的标签
        # 将 entry:// 链接保留（词汇链接）
        # 将 snd:// 链接转换为纯文本图标

        # 移除所有自定义标签（保留内容）
        all_custom_tags = [
            'h-g', 'top-g', 'hkey', 'infl', 'v-gs-blk', 'v-gs', 'v-g-blk', 'v-g',
            'v-blk', 'label-g-blk', 'label-g', 'geo-blk', 'vgslabel',
            'symbol', 'pron-gs', 'audio-ams-liju', 'x-g-blk', 'x-gs',
            'sn-gs', 'sn-g', 'xr-gs', 'xrlabel', 'xr-g-blk', 'xr-g',
            'xh-blk', 'xh', 'licontent', 'pos-g', 'pos-blk', 'res-g', 'if-gs-blk',
            'if-gs', 'if-g-blk', 'if-g', 'if-blk', 'ptl', 'namelabel',
            'audio-gb', 'audio-us', 'audio-gbs-liju', 'audio-uss-liju', 'audio-brs-liju',
            'gl-blk', 'reg-blk', 'cl-blk', 'titled',
            # 可能影响显示的其他标签
            'entry', 'entry-card', 'card-content'
        ]

        # 移除不需要映射的标签
        for tag in all_custom_tags:
            content = re.sub(r'<' + tag + r'[^>]*>', '', content)
            content = re.sub(r'</' + tag + r'>', '', content)

        # 应用标签映射
        for custom_tag, html_tag in tag_mapping.items():
            if html_tag:  # 非空才替换
                # 开标签
                content = re.sub(r'<' + custom_tag + r'(\s+[^>]*)>', r'<' + html_tag + r'\1>', content)
                content = re.sub(r'<' + custom_tag + r'>', r'<' + html_tag + r'>', content)
                # 闭标签
                content = re.sub(r'</' + custom_tag + r'>', r'</' + html_tag + r'>', content)
            else:
                # 空映射表示移除标签但保留内容
                content = re.sub(r'<' + custom_tag + r'[^>]*>', '', content)
                content = re.sub(r'</' + custom_tag + r'>', '', content)

        # 处理 xhtml: 命名空间标签
        content = re.sub(r'<xhtml:a(\s+[^>]*)>', r'<a\1>', content)
        content = re.sub(r'</xhtml:a>', r'</a>', content)
        content = re.sub(r'<xhtml:br\s*/>', r'<br/>', content)
        content = re.sub(r'</xhtml:[^>]+>', '', content)

        # 处理自闭合音频标签
        content = re.sub(r'<audio[^>]*/>', '', content)
        content = re.sub(r'<audio[^>]*>', '', content)
        content = re.sub(r'</audio>', '', content)

        # 移除特殊符号链接
        content = re.sub(r'<a href="help:[^"]*">[^<]*</a>', '', content)
        content = re.sub(r'<a href="helpg:[^"]*">[^<]*</a>', '', content)
        content = re.sub(r'<a href="helpxr:[^"]*">[^<]*</a>', '', content)

        # 保留 snd:// 链接的音频图标
        content = re.sub(r'<a href="snd://[^"]*">(🔊|▶|▶️)</a>', r'\1', content)

        # 移除多余的 </a> 标签（由于其他标签移除导致的孤立闭标签）
        # 统计 <a 和 </a> 的数量，移除多余的 </a>
        open_a = len(re.findall(r'<a\s', content))
        close_a = len(re.findall(r'</a>', content))
        if close_a > open_a:
            # 从后往前移除多余的 </a>
            diff = close_a - open_a
            for _ in range(diff):
                content = re.sub(r'</a>', '', content, count=1)

        # 清理空标签
        content = re.sub(r'<div>\s*</div>', '', content)

        return content

    def fuzzy_search(self, prefix: str, limit: int = 10) -> List[str]:
        """前缀模糊搜索"""
        results = []
        prefix_lower = prefix.lower()

        for word in self._index.keys():
            if word.startswith(prefix_lower):
                results.append(word)
                if len(results) >= limit:
                    break

        return results


class SimpleWordListImporter:
    """简单单词列表导入器"""

    @staticmethod
    def import_from_txt(txt_path: str) -> Tuple[Dict[str, Dict], List[str]]:
        """
        从文本文件导入单词列表
        格式: 每行一个单词，或 "单词 音标 释义"
        """
        words_dict = {}
        word_list = []

        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # 支持多种格式
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        word = parts[0].lower()
                        phonetic = parts[1]
                        definition = parts[2]
                    elif len(parts) == 2:
                        word = parts[0].lower()
                        phonetic = parts[1]
                        definition = ""
                    else:
                        word = line.lower()
                        phonetic = ""
                        definition = ""

                    if word and word.isalpha():
                        words_dict[word] = {
                            "phonetic": phonetic,
                            "definition": definition or f"单词: {word}"
                        }
                        word_list.append(word)

            return words_dict, word_list

        except Exception as e:
            print(f"导入文本文件出错: {e}")
            return {}, []

    @staticmethod
    def import_from_json(json_path: str) -> Tuple[Dict[str, Dict], List[str]]:
        """从JSON文件导入"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        words_dict = {}
        word_list = []

        for word, content in data.items():
            word_lower = word.lower()
            if isinstance(content, dict):
                words_dict[word_lower] = {
                    "phonetic": content.get("phonetic", ""),
                    "definition": content.get("definition", "")
                }
            elif isinstance(content, str):
                words_dict[word_lower] = {
                    "phonetic": "",
                    "definition": content
                }
            word_list.append(word_lower)

        return words_dict, word_list


def create_sample_word_list(output_path: str, num_words: int = 1000):
    """创建示例单词列表（用于测试）"""
    common_words = [
        "a", "about", "above", "across", "after", "again", "against", "all", "almost", "alone",
        "along", "already", "also", "although", "always", "among", "an", "and", "another", "any",
        "anyone", "anything", "anywhere", "are", "area", "around", "as", "ask", "at", "away",
        "back", "be", "because", "become", "been", "before", "being", "below", "between", "both",
        "but", "by", "can", "come", "could", "day", "did", "do", "does", "done", "down", "during",
        "each", "early", "either", "end", "enough", "even", "ever", "every", "few", "find", "first",
        "for", "from", "get", "give", "go", "good", "great", "had", "has", "have", "he", "her",
        "here", "him", "his", "how", "if", "in", "into", "is", "it", "its", "just", "know", "last",
        "late", "least", "life", "like", "long", "make", "man", "many", "may", "me", "might",
        "more", "most", "much", "must", "my", "never", "new", "next", "no", "not", "now", "of",
        "off", "often", "old", "on", "once", "one", "only", "or", "other", "our", "out", "over",
        "part", "people", "place", "put", "right", "said", "same", "see", "she", "should", "show",
        "since", "so", "some", "still", "such", "take", "than", "that", "the", "their", "them",
        "then", "there", "these", "they", "thing", "think", "this", "those", "through", "time",
        "to", "today", "too", "two", "under", "up", "use", "very", "want", "way", "we", "well",
        "were", "what", "when", "where", "which", "while", "who", "will", "with", "would", "year",
        "you", "your", "hello", "world", "computer", "software", "program", "language", "python",
        "dictionary", "algorithm", "function", "variable", "constant", "database", "network",
        "internet", "browser", "keyboard", "mouse", "screen", "window", "system", "memory",
        "file", "data", "code", "error", "debug", "compile", "execute", "process", "thread",
        "class", "object", "method", "property", "event", "handler", "callback", "promise",
        "async", "await", "import", "export", "module", "package", "library", "framework"
    ]

    words_dict = {}
    word_list = sorted(set(common_words))

    for w in word_list:
        words_dict[w] = {
            "phonetic": f"/{w}/",
            "definition": f"英语常用词: {w}"
        }

    # 保存为JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(words_dict, f, ensure_ascii=False, indent=2)

    return len(word_list)
