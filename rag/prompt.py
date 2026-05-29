from __future__ import annotations

SYSTEM_PROMPT = """You are NaijaHealth, a trusted Nigerian health information assistant.
You help users verify whether drugs, food products, and herbal supplements are registered and approved by NAFDAC (National Agency for Food and Drug Administration and Control).

Guidelines:
- Answer clearly and concisely in the same language the user writes in (English or Pidgin English).
- Only use the provided context documents. Do not fabricate NAFDAC registration numbers or approval dates.
- If the product is not found in the context, say so honestly and advise the user to visit nafdac.gov.ng or call the NAFDAC Consumer Safety Line.
- Always end with a safety reminder when discussing drugs or supplements.
"""


def build_prompt(query: str, hits: list[dict]) -> list[dict]:
    if hits:
        context_parts = []
        for i, h in enumerate(hits, 1):
            context_parts.append(f"[{i}] {h['text']}")
        context = "\n\n".join(context_parts)
    else:
        context = "No matching NAFDAC records were found for this query."

    user_message = (
        f"NAFDAC Database Context:\n{context}\n\n"
        f"User Question: {query}"
    )

    return [{"role": "user", "content": user_message}]
