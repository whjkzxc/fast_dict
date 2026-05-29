# FastDict - 快速单词查询工具

一个基于 PyQt5 的跨平台单词快捷查询工具，支持最小化和前置运行。
（请添加自己的api_key并修改去掉实例文件的_example实现模型接入）

## 功能特性

- **方便快捷**：启动后保持前置，输入单词回车立即显示释义
- **后台运行**: 启动后在系统托盘驻留，不占用任务栏空间
- **跨平台**: 支持 Windows、macOS 和 Linux
- **多格式支持**: JSON 格式，可扩展 MDict 等格式
- **支持第三方MDX词库**：将mdx文件放在dict_file目录下，程序会自动加载。
- **AI 智能解释**：词典中未收录的单词/短语会自动调用大模型生成简短解释

## 安装依赖

### 使用 pip（推荐）
```bash
pip install -r requirements.txt
```

## 使用方法

### 启动程序

**方式一：使用启动脚本**
```bash
./start.sh
```

**方式二：直接运行**
```bash
python3 main.py
# 或
python main.py
```

### 查询单词

1. 程序启动后会最小化到系统托盘
2. 按 Win+空格（或 Ctrl+空格）唤起搜索框
3. 输入要查询的单词，会自动显示相近词建议
4. 选择单词或按回车查看释义
5. 按ESC键关闭查询窗口

### 系统托盘

- **单击托盘图标**: 唤起搜索框
- **右键托盘图标**: 显示菜单
  - 显示搜索
  - 快捷键设置：打开快捷键录制对话框
  - 当前快捷键显示
  - 退出

### 快捷键设置

1. 右键点击托盘图标，选择「快捷键设置」
2. 点击「录制」按钮
3. 按下想要设置的组合键（如 Ctrl+Alt+D）
4. 点击「确定」保存设置

**支持的组合键**：
- 修饰键：Ctrl、Alt、Shift、Win（Meta）
- 字母键：A-Z
- 数字键：0-9
- 功能键：F1-F12
- 特殊键：Space、Tab、Enter 等

配置文件保存在 `~/.fastdict_config.json`

## 自定义词典

### JSON 格式词典

词典文件放在 `dict_file/` 目录下，JSON 格式：

```json
{
  "hello": {
    "phonetic": "/həˈloʊ/",
    "definition": "int. 你好；问候\nn. 问候，招呼"
  },
  "world": {
    "phonetic": "/wɜːrld/",
    "definition": "n. 世界；地球"
  }
}
```

### MDict 格式支持

程序会自动检测 `dict_file/` 目录下的 `.mdx` 文件。

**注意**: 加密的 MDict 文件无法直接解析。你的 `oxfordstu.mdx` 文件已加密。

#### 解密 MDict 文件

如需使用加密的 MDict 文件，可以使用以下工具解密：

1. **MdxBuilder** - https://github.com/xmxmt/mdx-builder
2. **MDict解密工具** - 在线搜索 "MDict decrypt"

解密后，将文件放回 `dict_file/` 目录。

#### 导入其他格式词典

创建一个文本文件（如 `my_words.txt`），每行一个单词：

```
hello /həˈloʊ/ int. 你好
world /wɜːrld/ n. 世界
python /ˈpaɪθɑːn/ n. Python语言
```

然后在代码中调用：
```python
from src.core.dictionary import DictionaryLoader
loader = DictionaryLoader()
loader.load_from_txt('my_words.txt')
```

## 项目结构

```
fast_dict/
├── main.py                 # 程序入口
├── start.sh                # 启动脚本
├── requirements.txt        # 依赖列表
├── model_api.json          # 大模型API配置
├── dict_file/              # 词典文件目录
│   ├── sample.json         # 示例词典
│   └── oxfordstu.mdx       # MDict词典（已加密）
└── src/
    ├── core/               # 核心模块
    │   ├── dictionary.py   # 词典加载和查询
    │   ├── fuzzy_match.py  # 模糊匹配算法
    │   ├── mdict_reader.py # MDict文件读取
    │   ├── llm_query.py    # 大模型查询模块
    │   └── config.py       # 配置管理器
    ├── ui/                 # UI组件
    │   ├── main_window.py  # 主窗口/托盘
    │   ├── search_widget.py # 搜索框
    │   ├── result_label.py # 结果展示
    │   └── hotkey_recorder.py # 快捷键录制组件
    └── hotkey/             # 热键模块
        └── global_hotkey.py # 全局热键监听
```

## AI 智能解释

当词典中未找到匹配词条时，程序会自动通过 OpenAI Compatible API 调用大语言模型，为输入内容生成150字以内的简短中文解释。

### 配置模型

模型接入信息保存在项目根目录的 `model_api.json` 文件中：

```json
{
    "api_base": "https://open.bigmodel.cn/api/paas/v4",
    "model": "glm-4.7-flash",
    "api_key": "your-api-key"
}
```

可修改该文件切换到其他兼容 OpenAI 接口的模型服务（如 OpenAI、DeepSeek 等）。

## 技术栈

- **UI框架**: PyQt5
- **模糊匹配**: Python difflib
- **全局热键**: Qt QShortcut
- **崩溃防护**: 启动时禁用 core dump，防止底层 C 库崩溃时生成巨大转储文件

## 常见问题

### Q: Linux 下快捷键不工作？
A: 需要设置输入设备权限：
```bash
sudo ./setup_input_permissions.sh
# 注销并重新登录使权限生效
```

### Q: MDict 词典无法加载？
A: 检查是否为加密文件。加密的 MDict 需要先解密。

### Q: 默认快捷键与其他软件冲突？
A: 右键托盘图标 → 快捷键设置，录制一个新的组合键。

### Q: 如何清除快捷键？
A: 在快捷键设置对话框中点击「清除」按钮，之后只能通过托盘图标呼出搜索框。

### Q: 快捷键只在应用前台时有效？
A: 这是权限问题。运行 `sudo ./setup_input_permissions.sh` 设置权限。

### Q: 如何添加更多单词？
A: 编辑 `dict_file/sample.json` 或创建新的 JSON 文件。

### Q: 配置文件保存在哪里？
A: 配置保存在 `~/.fastdict_config.json`，可以手动编辑。

## 开发计划

- [ ] 支持灵格斯 LD2/LD3 格式
- [ ] 完善未加密 MDict 解析
- [ ] 添加发音功能（TTS）
- [ ] 添加单词本功能
- [ ] 支持多个词典切换

## 许可证

MIT License
