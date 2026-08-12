#!/usr/bin/env python3
"""A small terminal chat client for a local Ollama model."""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

API_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.5"


def chat(messages: list[dict[str, str]], think: bool) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "messages": messages,
            "stream": True,
            "think": think,
            "keep_alive": "10m",
        }
    ).encode("utf-8")

    request = Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    answer = []
    with urlopen(request, timeout=600) as response:
        for raw_line in response:
            if not raw_line.strip():
                continue
            event = json.loads(raw_line)
            content = event.get("message", {}).get("content", "")
            if content:
                print(content, end="", flush=True)
                answer.append(content)
    print()
    return "".join(answer)


def main() -> None:
    messages: list[dict[str, str]] = []
    think = False

    print(f"本地模型：{MODEL}")
    print("命令：/think 开关深度思考，/clear 清空对话，/exit 退出\n")

    while True:
        try:
            prompt = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            return

        if not prompt:
            continue
        if prompt == "/exit":
            print("已退出。")
            return
        if prompt == "/clear":
            messages.clear()
            print("对话已清空。")
            continue
        if prompt == "/think":
            think = not think
            print(f"深度思考：{'开启' if think else '关闭'}")
            continue

        messages.append({"role": "user", "content": prompt})
        print("千问：", end="", flush=True)

        try:
            answer = chat(messages, think)
        except URLError:
            messages.pop()
            print("\n连接不到 Ollama。请先打开 Ollama 应用，然后重试。")
            continue
        except Exception as error:
            messages.pop()
            print(f"\n运行失败：{error}")
            continue

        messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
