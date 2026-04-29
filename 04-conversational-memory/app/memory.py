from collections import defaultdict
from copy import deepcopy
from typing import DefaultDict


ConversationTurn = dict[str, str]


_sessions: DefaultDict[str, list[ConversationTurn]] = defaultdict(list)


def get_history(session_id: str) -> list[ConversationTurn]:
    return deepcopy(_sessions[session_id])


def add_turn(session_id: str, role: str, content: str) -> None:
    _sessions[session_id].append({"role": role, "content": content})


def replace_history(session_id: str, history: list[ConversationTurn]) -> None:
    _sessions[session_id] = deepcopy(history)


def clear_session(session_id: str) -> None:
    _sessions[session_id] = []


def session_exists(session_id: str) -> bool:
    return session_id in _sessions and bool(_sessions[session_id])
