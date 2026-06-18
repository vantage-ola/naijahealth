from __future__ import annotations

_MAX_TG_CHARS = 4096


def format_answer(answer: str, sources: list[dict]) -> str:
    body = answer.strip()

    if sources:
        source_lines = []
        seen: set[str] = set()
        for s in sources:
            name = s.get("product_name", "")
            nafdac = s.get("nafdac_number") or ""
            key = f"{name}|{nafdac}"
            if key in seen:
                continue
            seen.add(key)
            label = f"• {name}"
            if nafdac:
                label += f" (NAFDAC: {nafdac})"
            source_lines.append(label)

        if source_lines:
            sources_block = "\n\nSources checked:\n" + "\n".join(source_lines)
            body = body + sources_block

    if len(body) > _MAX_TG_CHARS:
        body = body[: _MAX_TG_CHARS - 3] + "..."

    return body
