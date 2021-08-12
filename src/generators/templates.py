import requests
import os
from os.path import join as pjoin
import json
import progressbar
import xml.dom.minidom as xml
from yalm.template import parser
from util import escape_license_id

_dir = 'template'


def generate(dest, meta):
  print(f"Generating templates...")
  with open(pjoin(dest, meta['licenses-file'])) as f:
    licenses = json.load(f)

  os.makedirs(pjoin(dest, _dir), exist_ok=True)

  for license in progressbar.progressbar(licenses):
    license_id = license['id']
    license_path = escape_license_id(license_id)
    template_path = pjoin(dest, _dir, f"{license_path}.json")
    _generate_template(template_path, license_id)

  meta['templates-dir'] = _dir


def _generate_template(dest, license_id):
  res = requests.get(f'https://raw.githubusercontent.com/spdx/license-list-XML/master/src/{license_id}.xml')
  assert res.status_code == 200
  doc = xml.parseString(res.text)

  text = doc.getElementsByTagName('text')[0]
  template = parser.parse_xml(text)

  with open(dest, 'w+') as f:
    json.dump(template.to_dict(), f)
