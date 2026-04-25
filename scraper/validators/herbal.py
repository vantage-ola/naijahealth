from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

DATE_FORMATS = ["%d %b %Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]


def _parse_date(v: str | None) -> date | None:
    if not v or not isinstance(v, str):
        return None
    v = v.strip()
    for fmt in DATE_FORMATS:
        try:
            return date.fromisoformat(v) if fmt == "%Y-%m-%d" else date(
                *__import__("time").strptime(v, fmt)[:3]
            )
        except (ValueError, OverflowError):
            continue
    return None


class HerbalProduct(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sn: str | None = None
    product_name: str
    nafdac_number: str
    other_name: str | None = None
    pack_size: str | None = None
    presentation: str | None = None
    dosage_form: str | None = None
    applicant_name: str | None = None
    address: str | None = None
    manufacturer_name: str | None = None
    contact_address: str | None = None
    state: str | None = None
    certificate_issued_date: date | None = None
    expiry_date: date | None = None

    @field_validator("certificate_issued_date", "expiry_date", mode="before")
    @classmethod
    def parse_date(cls, v: str | None) -> date | None:
        return _parse_date(v)
