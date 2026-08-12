# Local Qwen Assistant

在 macOS 上通过 Ollama 和 Python 运行本地 Qwen3.5 助手。

## 功能

- 本地运行，不消耗 API 积分
- 网页聊天界面和终端聊天界面
- 上传一个或多个 PDF 后进行总结和问答
- 回答论文问题时提示文件名和页码
- 默认关闭深度思考，提高日常问答速度
- PDF、聊天内容和模型文件均不上传到 GitHub

## 准备

1. 安装并打开 [Ollama](https://ollama.com/download/mac)。
2. 下载 Qwen3.5：

```bash
ollama pull qwen3.5:9b
```

3. 确认 Python 3 已安装：

```bash
python3 --version
```

## 网页版（推荐）

首次使用：

```bash
git clone https://github.com/lishengwang92-droid/local-qwen-assistant.git
cd local-qwen-assistant
python3 -m pip install -r requirements.txt
python3 -m streamlit run web_app.py
```

浏览器会自动打开本地网页。上传 PDF 后，可以询问研究目的、研究方法、主要结果、结论和局限性。

如果仓库已经下载过，只需：

```bash
cd ~/local-qwen-assistant
git pull
python3 -m pip install -r requirements.txt
python3 -m streamlit run web_app.py
```

## 终端版

```bash
cd ~/local-qwen-assistant
python3 chat.py
```

终端命令：

- `/think`：开启或关闭深度思考
- `/clear`：清空当前对话
- `/exit`：退出程序

## 隐私与限制

- Ollama 的本地 API 默认运行在 `http://localhost:11434`。
- 上传的 PDF 只在当前程序内存中读取，不写入仓库。
- 扫描版 PDF 如果没有可提取文字，需要先进行 OCR。
- 当前版本采用轻量文本检索，适合个人论文阅读；重要结论仍需回到原文核对。
