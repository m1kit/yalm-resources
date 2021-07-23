import re


def escape_license_id(license: str) -> str:
  return re.sub(r'\W', '_', license)
