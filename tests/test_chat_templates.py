from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.chat_templates import format_chat_prompt


class FakeTokenizer:
    def __init__(self, has_template: bool = True):
        if has_template:
            self.chat_template = "{% for msg in messages %}{{ msg.role }}: {{ msg.content }}\n{% endfor %}{% if add_generation_prompt %}Assistant:\n{% endif %}"

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        if hasattr(self, "chat_template") and self.chat_template:
            result = ""
            for msg in messages:
                result += f"{msg['role']}: {msg['content']}\n"
            if add_generation_prompt:
                result += "Assistant:\n"
            return result
        raise ValueError("No template")


def test_native_template_used():
    tok = FakeTokenizer(has_template=True)
    messages = [{"role": "user", "content": "Hello"}]
    result = format_chat_prompt(tok, messages, add_generation_prompt=True)
    assert "user: Hello" in result
    assert "Assistant:" in result


def test_fallback_format():
    tok = FakeTokenizer(has_template=False)
    messages = [{"role": "user", "content": "Hello"}]
    result = format_chat_prompt(tok, messages, add_generation_prompt=True)
    assert "User: Hello" in result
    assert "Assistant:" in result


def test_fallback_multiple_messages():
    tok = FakeTokenizer(has_template=False)
    messages = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "How are you?"},
    ]
    result = format_chat_prompt(tok, messages, add_generation_prompt=True)
    assert "User: Hi" in result
    assert "Assistant: Hello!" in result
    assert "User: How are you?" in result
    assert result.strip().endswith("Assistant:")


def test_fallback_no_generation_prompt():
    tok = FakeTokenizer(has_template=False)
    messages = [{"role": "user", "content": "Hello"}]
    result = format_chat_prompt(tok, messages, add_generation_prompt=False)
    assert "Assistant:" not in result


def test_fallback_system_message():
    tok = FakeTokenizer(has_template=False)
    messages = [
        {"role": "system", "content": "You are a bot."},
        {"role": "user", "content": "Hello"},
    ]
    result = format_chat_prompt(tok, messages, add_generation_prompt=True)
    assert "System: You are a bot." in result
    assert "User: Hello" in result
