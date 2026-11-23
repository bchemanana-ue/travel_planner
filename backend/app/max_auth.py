from pathlib import Path
from dotenv import load_dotenv

import os
import json
import hmac
import hashlib

from urllib.parse import parse_qsl
from datetime import datetime, timezone


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def validate_max_init_data(init_data: str):
    bot_token = os.getenv("MAX_BOT_TOKEN")

    if not bot_token or bot_token == "ВСТАВИМ_НАСТОЯЩИЙ_ТОКЕН_ПОЗЖЕ":
        raise ValueError("Не настроен токен MAX-бота")

    if not init_data:
        raise ValueError("Данные авторизации отсутствуют")

    try:
        params_list = parse_qsl(
            init_data,
            keep_blank_values=True,
            strict_parsing=True
        )
    except ValueError:
        raise ValueError("Некорректный формат данных MAX")

    params = {}

    for key, value in params_list:
        if key in params:
            raise ValueError("Обнаружен повторяющийся параметр")

        params[key] = value

    original_hash = params.pop("hash", None)

    if (
        not original_hash
        or len(original_hash) != 64
        or any(char not in "0123456789abcdefABCDEF" for char in original_hash)
    ):
        raise ValueError("Некорректная подпись MAX")

    launch_params = "\n".join(
        f"{key}={value}"
        for key, value in sorted(params.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=launch_params.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, original_hash):
        raise ValueError("Подпись MAX недействительна")

    try:
        auth_date = int(params["auth_date"])
    except (KeyError, ValueError):
        raise ValueError("Некорректная дата авторизации")

    current_timestamp = int(
        datetime.now(timezone.utc).timestamp()
    )

    if current_timestamp - auth_date > 3600:
        raise ValueError("Данные авторизации устарели")

    if auth_date > current_timestamp + 60:
        raise ValueError("Некорректная дата авторизации")

    try:
        user = json.loads(params["user"])
    except (KeyError, json.JSONDecodeError):
        raise ValueError("Данные пользователя отсутствуют")

    if not isinstance(user, dict):
        raise ValueError("Некорректные данные пользователя")

    user_id = user.get("id")

    if (
        isinstance(user_id, bool)
        or not isinstance(user_id, int)
        or user_id <= 0
    ):
        raise ValueError("Некорректный ID пользователя")

    return user