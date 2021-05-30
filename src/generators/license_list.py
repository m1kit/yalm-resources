import requests
import os
from os.path import join as pjoin
import json
import progressbar
import xml.dom.minidom as xml
from spdx_xml import nodes

_filepath = 'licenses.json'

_dir_template = 'template'
_dir_regex = 'regex'
_dir_words = 'words'
_dirs = [
    _dir_template,
    _dir_regex,
    _dir_words,
]


def generate(dest):
  print(f"Generating '{_filepath}'...")
  res = requests.get('https://spdx.org/licenses/licenses.json')
  assert res.status_code == 200
  data = res.json()

  with open('static/bigquery-license-count.json') as f:
    stats = {e['license']: e['count'] for e in json.load(f)}

  # make output directories
  for d in _dirs:
    os.makedirs(pjoin(dest, d), exist_ok=True)

  licenses = []
  for license in progressbar.progressbar(data['licenses']):
    license_id = license['licenseId']
    count = stats.get(license_id.lower(), 0)
    # the more smaller key is, the more frequently used
    key = (
        -count,
        not license['isOsiApproved'],
        not license['isDeprecatedLicenseId'],
        license_id,
    )
    templates = _generate_template(dest, license_id)
    licenses.append({'id': license_id, 'name': license['name'], 'priority': key, **templates})

  licenses.sort(key=lambda l: l['priority'])
  for i, license in enumerate(licenses):
    license['priority'] = i
  with open(pjoin(dest, _filepath), 'w+') as f:
    json.dump(licenses, f)

  return {
      'licenses-file': _filepath,
      'licenses-version': data['licenseListVersion'],
  }


def _generate_template(dest, license_id):
  res = requests.get(f'https://raw.githubusercontent.com/spdx/license-list-XML/master/src/{license_id}.xml')
  assert res.status_code == 200
  doc = xml.parseString(res.text)

  text = doc.getElementsByTagName('text')[0]
  template = nodes.parse(text)

  path_template = pjoin(_dir_template, f"{license_id}.json")
  with open(pjoin(dest, path_template), 'w+') as f:
    json.dump(nodes.to_dict(template), f)

  return {
      'template': path_template,
  }
