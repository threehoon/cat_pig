from collections.abc import Sequence

from app.modules.assistant.completion import Turn


MAX_MESSAGES = 60
MAX_CHARS = 8000


def model_history(turns: Sequence[Turn]) -> list[Turn]:
    """Keep the newest turns that fit the model budget.

    The screen still shows the whole thread. This only trims the copy sent
    to the model: 30 rounds, or about 8000 characters, whichever comes first.
    """
    if not turns:
        return []
    chosen: list[Turn] = []
    used = 0
    for turn in reversed(turns):
        if len(chosen) >= MAX_MESSAGES:
            break
        text = turn.content
        if not chosen and len(text) > MAX_CHARS:
            return [Turn(turn.role, text[:MAX_CHARS])]
        if used + len(text) > MAX_CHARS:
            break
        chosen.append(Turn(turn.role, text))
        used += len(text)
    chosen.reverse()
    return chosen
