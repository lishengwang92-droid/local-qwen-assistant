# Local Qwen Assistant

在 macOS 上通过 Ollama 和 Python 运行本地 Qwen3.5 聊天助手。

## 功能

- 本地运行，不消耗 API 积分
- 默认关闭深度思考，提高日常问答速度
- 保留当前会话上下文
- 不上传模型文件、聊天内容或 API 密钥
- 仅使用 Python 标准库，无需安装第三方依赖

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

## 运行

克隆仓库并启动：

```bash
git clone https://github.com/lishengwang92-droid/local-qwen-assistant.git
cd local-qwen-assistant
python3 chat.py
```

## 聊天命令

- `/think`：开启或关闭深度思考
- `/clear`：清空当前对话
- `/exit`：退出程序

Ollama 的本地 API 默认运行在 `http://localhost:11434`。
