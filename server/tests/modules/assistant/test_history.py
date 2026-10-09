from app.modules.assistant.completion import INSTRUCTIONS, Turn
from app.modules.assistant.history import MAX_CHARS, MAX_MESSAGES, model_history


def test_empty_history_stays_empty() -> None:
    assert model_history(()) == []


def test_history_keeps_the_newest_sixty_messages() -> None:
    turns = [
        Turn("user" if index % 2 == 0 else "assistant", f"m{index}")
        for index in range(MAX_MESSAGES + 2)
    ]
    chosen = model_history(turns)
    assert len(chosen) == MAX_MESSAGES
    assert chosen[0].content == "m2"
    assert chosen[-1].content == f"m{MAX_MESSAGES + 1}"


def test_history_stops_before_crossing_the_character_budget() -> None:
    chunk = "字" * 3000
    turns = [Turn("user", chunk), Turn("assistant", chunk), Turn("user", chunk)]
    chosen = model_history(turns)
    assert [turn.content for turn in chosen] == [chunk, chunk]
    assert sum(len(turn.content) for turn in chosen) == 6000


def test_newest_overlong_message_is_clipped() -> None:
    older = Turn("user", "旧的")
    newest = Turn("assistant", "新" * (MAX_CHARS + 50))
    chosen = model_history([older, newest])
    assert len(chosen) == 1
    assert chosen[0].role == "assistant"
    assert chosen[0].content == "新" * MAX_CHARS


def test_instructions_refuse_the_canned_opener() -> None:
    assert "不要用「我是小x。这是常识说明」开头" in INSTRUCTIONS
    assert "顺着接" in INSTRUCTIONS
