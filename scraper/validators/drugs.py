from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator


class GreenBookProduct(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    product_id: int
    product_name: str
    nafdac_reg_no: str
    ingredient_name: str | None = None
    ingredient_synonym: str | None = None
    product_category: str | None = None
    form: str | None = None
    route: str | None = None
    strength: str | None = None
    applicant_name: str | None = None
    approval_date: date | None = None
    expiry_date: date | None = None
    status: str | None = None
    pack_size: str | None = None
    composition: str | None = None
    product_description: str | None = None

    @field_validator("product_name", "nafdac_reg_no", mode="before")
    @classmethod
    def strip_special(cls, v: str) -> str:
        if isinstance(v, str):
            return v.replace("#", "").replace("*", "").strip()
        return v

    @field_validator("approval_date", "expiry_date", mode="before")
    @classmethod
    def parse_date(cls, v: str | None) -> date | None:
        if not v or not isinstance(v, str):
            return None
        try:
            return date.fromisoformat(v[:10])
        except ValueError:
            return None
