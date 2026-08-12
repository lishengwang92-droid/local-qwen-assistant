#!/usr/bin/env python3
"""Local Streamlit UI for Qwen3.5 with lightweight PDF question answering."""

from __future__ import annotations

import io
import json
import re
from collections.abc import Iterator
from urllib.error import URLError
from urllib.request import Request, urlopen

import streamlit as st
from pypdf import PdfReader


API_URL = "http://localhost:11434/api/chat"
MODELS_URL = "http://localhost:11434/api/tags"
MODEL = "qwen3.5"
CHUNK_SIZE = 1_800
CHUNK_OVERLAP = 200
MAX_CONTEXT_CHARS = 18_000


st.set_page_config(page_title="本地千问助手", page_icon="🦙", layout="wide")


def ollama_is_ready() -> bool:
    try:
        with urlopen(MODELS_URL, timeout=3) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


@st.cache_data(show_spinner=False)
def extract_pdf(file_bytes: bytes, filename: str) -> list[dict[str, str | int]]:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages: list[dict[str, str | int]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append({"file": filename, "page": page_number, "text": text})
    return pages


def make_chunks(pages: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    chunks: list[dict[str, str | int]] = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for page in pages:
        text = str(page["text"])
        for start in range(0, len(text), step):
            chunk = text[start : start + CHUNK_SIZE].strip()
            if chunk:
                chunks.append({"file": page["file"], "page": page["page"], "text": chunk})
    return chunks


def search_terms(query: str) -> set[str]:
    query = query.lower()
    terms = set(re.findall(r"[a-z0-9_]{2,}", query))
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", query))
    terms.update(chinese[index : index + 2] for index in range(max(0, len(chinese) - 1)))
    return terms


def choose_chunks(chunks: list[dict[str, str | int]], query: str) -> list[dict[str, str | int]]:
    if not chunks:
        return []

    summary_words = ("总结", "概括", "摘要", "全文", "研究目的", "研究方法", "主要结论")
    if any(word in query for word in summary_words):
        count = min(10, len(chunks))
        indexes = sorted({round(index * (len(chunks) - 1) / max(1, count - 1)) for index in range(count)})
        selected = [chunks[index] for index in indexes]
    else:
        terms = search_terms(query)

        def score(chunk: dict[str, str | int]) -> int:
            text = str(chunk["text"]).lower()
            return sum(text.count(term) for term in terms)

        ranked = sorted(enumerate(chunks), key=lambda item: (score(item[1]), -item[0]), reverse=True)
        selected = [chunk for _, chunk in ranked[:8]]

    result: list[dict[str, str | int]] = []
    used = 0
    for chunk in selected:
        length = len(str(chunk["text"]))
        if result and used + length > MAX_CONTEXT_CHARS:
            break
        result.append(chunk)
        used += length
    return result


def pdf_context(chunks: list[dict[str, str | int]], query: str) -> str:
    chosen = choose_chunks(chunks, query)
    if not chosen:
        return ""
    sections = []
    for chunk in chosen:
        sections.append(f"[来源：{chunk['file']}，第 {chunk['page']} 页]\n{chunk['text']}")
    return "\n\n".join(sections)


def stream_reply(messages: list[dict[str, str]], think: bool) -> Iterator[str]:
    payload = json.dumps(
        {
            "model": MODEL,
            "messages": messages,
            "stream": True,
            "think": think,
            "keep_alive": "10m",
        }
    ).encode("utf-8")
    request = Request(API_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=600) as response:
        for raw_line in response:
            if not raw_line.strip():
                continue
            event = json.loads(raw_line)
            content = event.get("message", {}).get("content", "")
            if content:
                yield content


if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🦙 本地千问助手")
    st.caption("Qwen3.5 · Ollama · 数据留在本机")
    if ollama_is_ready():
        st.success("Ollama 已连接")
    else:
        st.error("Ollama 未连接，请先打开 Ollama")

    think = st.toggle("深度思考", value=False, help="复杂推理时开启；普通聊天关闭会更快。")
    uploaded_files = st.file_uploader(
        "上传 PDF 论文",
        type=["pdf"],
        accept_multiple_files=True,
        help="文件只在当前 Mac 内存中读取，不会上传到 GitHub。",
    )
    if st.button("清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

all_pages: list[dict[str, str | int]] = []
for uploaded_file in uploaded_files or []:
    try:
        all_pages.extend(extract_pdf(uploaded_file.getvalue(), uploaded_file.name))
    except Exception as error:
        st.sidebar.warning(f"无法读取 {uploaded_file.name}：{error}")

chunks = make_chunks(all_pages)
if uploaded_files:
    st.sidebar.info(f"已读取 {len(uploaded_files)} 个 PDF，共 {len(all_pages)} 页可检索文字")

st.title("本地千问助手")
st.caption("可以直接聊天；上传 PDF 后，可询问研究目的、方法、结果和局限性。")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("输入问题，例如：总结这篇论文的研究方法"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    context = pdf_context(chunks, prompt)
    current_prompt = prompt
    if context:
        current_prompt = (
            "请根据下面的 PDF 摘录回答问题。优先忠于原文；如果材料不足，请明确说明。"
            "回答涉及论文内容时，请标注文件名和页码。\n\n"
            f"PDF 摘录：\n{context}\n\n用户问题：{prompt}"
        )

    recent = st.session_state.messages[-8:-1]
    api_messages = [{"role": item["role"], "content": item["content"]} for item in recent]
    api_messages.append({"role": "user", "content": current_prompt})

    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(stream_reply(api_messages, think))
        except (OSError, URLError):
            answer = "连接不到 Ollama。请先打开 Ollama 应用，然后重试。"
            st.error(answer)
        except Exception as error:
            answer = f"运行失败：{error}"
            st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": str(answer)})
