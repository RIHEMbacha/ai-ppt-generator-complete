"""Robust JSON extraction from LLM responses."""

import json
import logging
import re

logger = logging.getLogger("llm")


def extract_json(raw: str) -> dict:
    """Extract the first valid JSON object/array from a raw LLM response.

    Strategy:
    - Strip ```json blocks if present.
    - Look for the first { or [ and then scan forward with a simple lexer
      that respects string quoting and escaping to find the matching closing
      bracket/brace. This avoids failing on extra trailing commentary.
    - Fall back to previous heuristics if needed.
    """
    raw = (raw or "").strip()

    if "```" in raw:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw, re.I)
        if m:
            raw = m.group(1).strip()
        else:
            raw = raw.replace("```json", "").replace("```", "").strip()

    # Find first JSON opening char
    idx = None
    for i, ch in enumerate(raw):
        if ch in "[{":
            idx = i
            break
    if idx is None:
        raise ValueError("No JSON object found in LLM response")

    opener = raw[idx]
    closer = '}' if opener == '{' else ']'

    # Scan forward to find the matching closer while respecting strings and escapes
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
            # If direct loads failed, try JSONDecoder.raw_decode on the remainder
            try:
                decoder = json.JSONDecoder()
                obj, end = decoder.raw_decode(raw[idx:])
                return obj
            except Exception:
                # fall through to heuristics below
                pass

    # Additional robust attempt: use JSONDecoder to parse the first value and ignore trailing data
    try:
        decoder = json.JSONDecoder()
        obj, end = decoder.raw_decode(raw[idx:])
        return obj
    except Exception:
        pass

    # Heuristic fallbacks (best-effort attempts similar to previous logic)
    start = raw.find('{')
    if start != -1:
        end = raw.rfind('}')
        if end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass

    # Try to balance quotes/brackets/braces minimally and parse
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
