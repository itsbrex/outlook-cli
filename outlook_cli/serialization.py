from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone, timedelta

from .models import Attachment, Contact, Email, Event, Folder

SCHEMA_VERSION = "1"


# Get local timezone
def _get_local_timezone():
    """Get system local timezone."""
    import datetime as dt
    return dt.datetime.now(dt.timezone.utc).astimezone().tzinfo


class _Encoder(json.JSONEncoder):
    def __init__(self, *, local_tz=None, **kwargs):
        super().__init__(**kwargs)
        self._local_tz = local_tz

    def default(self, o):
        if isinstance(o, datetime):
            if self._local_tz and o.tzinfo:
                # Convert to local timezone
                local_dt = o.astimezone(self._local_tz)
                return {
                    "utc": o.isoformat(),
                    "local": local_dt.strftime("%Y-%m-%d %H:%M"),
                    "local_iso": local_dt.isoformat(),
                }
            return o.isoformat()
        return super().default(o)


def _normalize(items):
    """Convert dataclasses / mixed lists to plain dicts."""
    if isinstance(items, list):
        return [asdict(i) if hasattr(i, "__dataclass_fields__") else i for i in items]
    if hasattr(items, "__dataclass_fields__"):
        return asdict(items)
    return items


def to_json(items: list | dict, pretty: bool = True) -> str:
    """Raw JSON — used by save_json for file export."""
    return json.dumps(_normalize(items), cls=_Encoder, indent=2 if pretty else None, ensure_ascii=False)


def to_json_envelope(items: list | dict, pretty: bool = True, local: bool = False) -> str:
    """Wrap data in {ok, schema_version, data} envelope for stdout.

    Args:
        items: Data to serialize
        pretty: Pretty-print JSON (default True)
        local: Convert datetimes to local timezone (default False)
    """
    if local:
        local_tz = _get_local_timezone()

        class _LocalEncoder(_Encoder):
            def __init__(self, **kwargs):
                super().__init__(local_tz=local_tz, **kwargs)

        encoder_cls = _LocalEncoder
    else:
        encoder_cls = _Encoder

    envelope = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "data": _normalize(items),
    }
    return json.dumps(envelope, cls=encoder_cls, indent=2 if pretty else None, ensure_ascii=False)


def error_json(code: str, message: str) -> str:
    """Structured error envelope for --json mode."""
    envelope = {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "error": {"code": code, "message": message},
    }
    return json.dumps(envelope, indent=2, ensure_ascii=False)


def save_json(items: list | dict, path: str, local: bool = False) -> None:
    """Save raw JSON to file (no envelope — file export is raw data).

    Args:
        items: Data to serialize
        path: File path to write to
        local: Convert datetimes to local timezone (default False)
    """
    if local:
        local_tz = _get_local_timezone()

        class _LocalEncoder(_Encoder):
            def __init__(self, **kwargs):
                super().__init__(local_tz=local_tz, **kwargs)

        encoder_cls = _LocalEncoder
    else:
        encoder_cls = _Encoder

    with open(path, "w") as f:
        f.write(json.dumps(_normalize(items), cls=encoder_cls, indent=2, ensure_ascii=False))
