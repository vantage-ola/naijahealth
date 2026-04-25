from scraper.spiders.base import clean_str


def parse_greenbook_record(raw: dict) -> dict:
    """Flatten a nested greenbook API record into a flat dict for validation."""
    ingredient = raw.get("ingredient") or {}
    applicant = raw.get("applicant") or {}
    form = raw.get("form") or {}
    route = raw.get("route") or {}
    category = raw.get("product_category") or {}

    return {
        "product_id": raw.get("product_id"),
        "product_name": clean_str(raw.get("product_name")),
        "nafdac_reg_no": clean_str(raw.get("NAFDAC")),
        "ingredient_name": clean_str(ingredient.get("ingredient_name")),
        "ingredient_synonym": clean_str(ingredient.get("synonym")),
        "product_category": clean_str(category.get("name")),
        "form": clean_str(form.get("name")),
        "route": clean_str(route.get("name")),
        "strength": clean_str(raw.get("strength")),
        "applicant_name": clean_str(applicant.get("name")),
        "approval_date": raw.get("approval_date"),
        "expiry_date": raw.get("expiry_date"),
        "status": clean_str(raw.get("status")),
        "pack_size": clean_str(raw.get("pack_size")),
        "composition": clean_str(raw.get("composition")),
        "product_description": clean_str(raw.get("product_description")),
    }
