from scraper.spiders.base import clean_str


def parse_herbal_record(raw: dict) -> dict:
    """Extract the value dict from a Ninja Tables AJAX row and normalize keys."""
    val = raw.get("value", raw)

    return {
        "sn": clean_str(val.get("sn")),
        "product_name": clean_str(val.get("productname")),
        "nafdac_number": clean_str(val.get("nafdacnumber")),
        "other_name": clean_str(val.get("othername")),
        "pack_size": clean_str(val.get("packsize")),
        "presentation": clean_str(val.get("presentation")),
        "dosage_form": clean_str(val.get("dosageform")),
        "applicant_name": clean_str(val.get("applicantname")),
        "address": clean_str(val.get("address")),
        "manufacturer_name": clean_str(val.get("manufacturername")),
        "contact_address": clean_str(val.get("contactaddress")),
        "state": clean_str(val.get("state")),
        "certificate_issued_date": clean_str(val.get("certificateissueddate")),
        "expiry_date": clean_str(val.get("expirydate")),
    }
