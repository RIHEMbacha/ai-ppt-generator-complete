"""Robust JSON extraction from LLM responses."""

import json
import logging
import re

logger = logging.getLogger("llm")


def extract_json(raw: str) -> dict:
    raw = (raw or "").strip()

    if "```" in raw:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.I)
        if m:
            raw = m.group(1).strip()
        else:
            raw = raw.replace("```json", "").replace("```", "").strip()

    idx = None
    for i, ch in enumerate(raw):
        if ch in "[{":
            idx = i
            break
    if idx is None:
        raise ValueError("No JSON object found in LLM response")

    opener = raw[idx]
    closer = '}' if opener == '{' else ']'

    depth = 0
    in_string = False
    escape = False
    end_idx = None
    for i in range(idx, len(raw)):
        ch = raw[i]
        if in_string:
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"':
                in_string = False
                continue
            continue
        else:
            if ch == '"':
                in_string = True
                continue
            if ch == opener:
                depth += 1
                continue
            if ch == closer:
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break
    if end_idx is not None:
        candidate = raw[idx : end_idx + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            try:
                decoder = json.JSONDecoder()
                obj, end = decoder.raw_decode(raw[idx:])
                return obj
            except Exception:
                pass

    try:
        decoder = json.JSONDecoder()
        obj, end = decoder.raw_decode(raw[idx:])
        return obj
    except Exception:
        pass

    start = raw.find('{')
    if start != -1:
        end = raw.rfind('}')
        if end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass

    start = raw.find('{')
    if start == -1:
        raise ValueError("No JSON object found in LLM response")
    candidate = raw[start:]
    if candidate.count('"') % 2 == 1:
        candidate += '"'
    open_braces = candidate.count("{") - candidate.count("}")
    open_brackets = candidate.count("[") - candidate.count("]")
    candidate += "]" * max(0, open_brackets) + "}" * max(0, open_braces)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        preview = raw[start : start + 1000]
        logger.error("JSON parse failed. Preview:\n%s", preview)
        raise ValueError(f"Invalid JSON from LLM: {e}") from e
