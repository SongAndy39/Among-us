"""JSON line protocol helpers and payload validation."""

import json
from typing import Any, Dict, Iterable, Optional


SYNC_MESSAGE_FIELDS = {
    "position_update": ("player_name", "location"),
    "sabotage": ("system",),
    "repair_sabotage": ("system",),
    "place_bomb": ("location",),
    "defuse_bomb": (),
    "complete_task": ("player_name", "completed_tasks"),
    "game_over": ("winner",),
}


def encode_line(message: Dict[str, Any]) -> bytes:
    return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")


def decode_line(line: str) -> Optional[Dict[str, Any]]:
    try:
        message = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return None
    return message if isinstance(message, dict) else None


def validate_sync_message(message: Dict[str, Any]) -> bool:
    msg_type = message.get("type")
    if msg_type not in SYNC_MESSAGE_FIELDS:
        return False

    for field in SYNC_MESSAGE_FIELDS[msg_type]:
        if field not in message:
            return False
    return True


def safe_send(sock, message: Dict[str, Any]) -> bool:
    try:
        sock.sendall(encode_line(message))
        return True
    except (BrokenPipeError, ConnectionResetError, OSError):
        return False
