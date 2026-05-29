# -*- coding: utf-8 -*-
"""词典加载和查询引擎"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.core.mdict_reader import (
    MDictInfo, SimpleWordListImporter, create_sample_word_list,
    MDXReader, HAS_READMDICT
)


class WordEntry:
    """单词词条"""

    def __init__(self, word: str, phonetic: str = "", definition: str = ""):
        self.word = word
        self.phonetic = phonetic
        self.definition = definition

    def __repr__(self):
        return f"WordEntry('{self.word}', '{self.phonetic}')"


class DictionaryLoader:
    """词典加载器 - 支持多种格式"""

    def __init__(self, dict_dir: str = None):
        if dict_dir is None:
            self.dict_dir = Path(__file__).parent.parent.parent / "dict_file"
        else:
            self.dict_dir = Path(dict_dir)
        self._words: Dict[str, WordEntry] = {}
        self._word_list: List[str] = []
        self._mdx_reader: Optional[MDXReader] = None

    def load_json(self, filename: str = "sample.json") -> int:
        """加载JSON格式词典"""
        filepath = self.dict_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"词典文件不存在: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for word, content in data.items():
            entry = WordEntry(
                word=word.lower(),
                phonetic=content.get("phonetic", ""),
                definition=content.get("definition", "")
            )
            self._words[word.lower()] = entry
            self._word_list.append(word.lower())
            count += 1

        return count

    def load_mdict(self, filename: str = None) -> int:
        """加载MDict格式词典 (.mdx)"""
        if not HAS_READMDICT:
            print("警告: 未安装 readmdict，无法加载 MDX 词典")
            print("请安装: pip install readmdict python-lzo")
            return 0

        if filename is None:
            # 查找第一个.mdx文件
            mdx_files = list(self.dict_dir.glob("*.mdx"))
            if not mdx_files:
                return 0
            mdx_file = mdx_files[0]
        else:
            mdx_file = self.dict_dir / filename

        if not mdx_file.exists():
            return 0

        # 查找对应的 MDD 文件
        mdd_file = mdx_file.with_suffix('.mdd')
        if not mdd_file.exists():
            mdd_file = None

        try:
            # 使用 MDXReader 加载
            self._mdx_reader = MDXReader(str(mdx_file), str(mdd_file) if mdd_file else None)

            # 获取单词列表（用于模糊匹配）
            # 限制数量避免内存占用过大
            self._word_list = self._mdx_reader.get_word_list()

            return self._mdx_reader.word_count

        except Exception as e:
            print(f"加载 MDX 文件失败: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def load_from_txt(self, filename: str) -> int:
        """从文本文件导入单词列表"""
        filepath = self.dict_dir / filename
        if not filepath.exists():
            print(f"文件不存在: {filepath}")
            return 0

        print(f"正在导入: {filepath.name}...")
        words_dict, word_list = SimpleWordListImporter.import_from_txt(str(filepath))

        count = 0
        for word, data in words_dict.items():
            if word not in self._words:
                entry = WordEntry(
                    word=word,
                    phonetic=data.get("phonetic", ""),
                    definition=data.get("definition", "")
                )
                self._words[word] = entry
                self._word_list.append(word)
                count += 1

        print(f"导入完成，共 {count} 个单词")
        return count

    def load_all(self) -> int:
        """加载dict_file目录下所有支持的词典文件"""
        total = 0

        # 优先加载 MDX 格式（如果存在）
        mdx_files = list(self.dict_dir.glob("*.mdx"))
        if mdx_files:
            try:
                count = self.load_mdict(mdx_files[0].name)
                if count > 0:
                    total = count
                    print(f"已加载 MDX 词典: {mdx_files[0].name}")
            except Exception as e:
                print(f"加载 MDX 失败: {e}")

        # 如果没有 MDX，加载 JSON 格式
        if total == 0:
            for file in self.dict_dir.glob("*.json"):
                try:
                    total += self.load_json(file.name)
                except Exception as e:
                    print(f"加载 {file.name} 失败: {e}")

        return total

    @property
    def words(self) -> Dict[str, WordEntry]:
        """获取所有单词字典"""
        return self._words

    @property
    def word_list(self) -> List[str]:
        """获取单词列表（用于模糊匹配）"""
        return self._word_list

    @property
    def mdx_reader(self) -> Optional[MDXReader]:
        """获取 MDX 读取器"""
        return self._mdx_reader

    def __len__(self):
        return len(self._word_list)


class DictionaryQuery:
    """词典查询器"""

    def __init__(self, loader: DictionaryLoader):
        self.loader = loader

    def lookup(self, word: str) -> Optional[WordEntry]:
        """查询单词"""
        # 先从 MDX 读取器查询
        if self.loader._mdx_reader:
            content = self.loader._mdx_reader.lookup(word)
            if content:
                return WordEntry(word=word, definition=content)

        # 从内存中的词典查询
        return self.loader.words.get(word.lower())

    def lookup_exact(self, word: str) -> Tuple[bool, Optional[WordEntry]]:
        """精确查询，返回(是否找到, 词条)"""
        entry = self.lookup(word)
        return (entry is not None, entry)

    def get_definition_html(self, word: str) -> str:
        """获取单词的HTML格式释义"""
        entry = self.lookup(word)

        if not entry:
            return f'<h2 style="color: #e74c3c;">未找到单词: {word}</h2>'

        # 如果是从 MDX 获取的 HTML，需要清理
        if self.loader._mdx_reader:
            content = self.loader._mdx_reader.get_definition_html(word)
            if content:
                # 包装 MDX 的 HTML 内容
                html = f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 10px;">
                    <h1 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 24px;">
                        {word.capitalize()}
                    </h1>
                    <div style="border-top: 1px solid #ecf0f1; padding-top: 10px; font-size: 14px; line-height: 1.6;">
                        {content}
                    </div>
                </div>
                """
                return html

        # 从内存词典获取的格式
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; padding: 10px;">
            <h1 style="margin: 0 0 5px 0; color: #2c3e50; font-size: 28px;">
                {entry.word.capitalize()}
            </h1>
            <p style="margin: 0 0 15px 0; color: #7f8c8d; font-size: 16px; font-style: italic;">
                {entry.phonetic}
            </p>
            <div style="border-top: 1px solid #ecf0f1; padding-top: 15px;">
                <p style="margin: 0; color: #34495e; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">
{entry.definition}
                </p>
            </div>
        </div>
        """
        return html
