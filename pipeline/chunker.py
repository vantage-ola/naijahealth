from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Chunk:
    product_id: str
    source: str
    text: str
    nafdac_number: str | None
    product_name: str
    payload: dict[str, Any]
    content_hash: str


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _line(label: str, value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in {"n/a", "na", "nil", "none"}:
        return None
    return f"{label}: {s}"


def _join(*lines: str | None) -> str:
    return "\n".join(line for line in lines if line)


def chunk_greenbook(record: dict) -> Chunk:
    nafdac = record.get("nafdac_reg_no")
    name = record["product_name"]
    pid = f"greenbook:{record['product_id']}"
    text = _join(
        _line("Source", "NAFDAC Greenbook (drug)"),
        _line("Product", name),
        _line("NAFDAC Reg No", nafdac),
        _line("Category", record.get("product_category")),
        _line("Form", record.get("form")),
        _line("Route", record.get("route")),
        _line("Strength", record.get("strength")),
        _line("Active Ingredient", record.get("ingredient_name")),
        _line("Synonym", record.get("ingredient_synonym")),
        _line("Composition", record.get("composition")),
        _line("Pack Size", record.get("pack_size")),
        _line("Applicant", record.get("applicant_name")),
        _line("Approval Date", record.get("approval_date")),
        _line("Expiry Date", record.get("expiry_date")),
        _line("Status", record.get("status")),
        _line("Description", record.get("product_description")),
    )
    return Chunk(
        product_id=pid,
        source="greenbook",
        text=text,
        nafdac_number=nafdac,
        product_name=name,
        payload=record,
        content_hash=_hash(text),
    )


def chunk_food(record: dict) -> Chunk:
    nafdac = record["nafdac_number"]
    name = record["product_name"]
    pid = f"food:{nafdac}"
    text = _join(
        _line("Source", "NAFDAC Food Products Database"),
        _line("Product", name),
        _line("NAFDAC Number", nafdac),
        _line("Category", record.get("category")),
        _line("Subcategory", record.get("subcategory")),
        _line("Pack Size", record.get("pack_size")),
        _line("Presentation", record.get("presentation")),
        _line("Applicant", record.get("applicant_name")),
        _line("Applicant Address", record.get("address")),
        _line("Country", record.get("country")),
        _line("Manufacturer", record.get("manufacturer")),
        _line("Manufacturer Address", record.get("manufacturer_address")),
        _line("Issue Date", record.get("issue_date")),
        _line("Expiry Date", record.get("expiry_date")),
        _line("Year", record.get("year")),
    )
    return Chunk(
        product_id=pid,
        source="food",
        text=text,
        nafdac_number=nafdac,
        product_name=name,
        payload=record,
        content_hash=_hash(text),
    )


def chunk_herbal(record: dict) -> Chunk:
    nafdac = record["nafdac_number"]
    name = record["product_name"]
    pid = f"herbal:{nafdac}"
    text = _join(
        _line("Source", "NAFDAC Herbal Products Database"),
        _line("Product", name),
        _line("NAFDAC Number", nafdac),
        _line("Other Name", record.get("other_name")),
        _line("Dosage Form", record.get("dosage_form")),
        _line("Pack Size", record.get("pack_size")),
        _line("Presentation", record.get("presentation")),
        _line("Applicant", record.get("applicant_name")),
        _line("Applicant Address", record.get("address")),
        _line("Manufacturer", record.get("manufacturer_name")),
        _line("Manufacturer Address", record.get("contact_address")),
        _line("State", record.get("state")),
        _line("Certificate Issued", record.get("certificate_issued_date")),
        _line("Expiry Date", record.get("expiry_date")),
    )
    return Chunk(
        product_id=pid,
        source="herbal",
        text=text,
        nafdac_number=nafdac,
        product_name=name,
        payload=record,
        content_hash=_hash(text),
    )


CHUNKERS = {
    "greenbook": chunk_greenbook,
    "food": chunk_food,
    "herbal": chunk_herbal,
}


def chunk_record(source: str, record: dict) -> Chunk:
    return CHUNKERS[source](record)
