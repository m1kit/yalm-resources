import requests
import os
from os.path import join as pjoin
import json
import progressbar

_filepath = 'licenses.json'


def generate(dest, meta):
  print(f"Generating '{_filepath}'...")
  res = requests.get('https://spdx.org/licenses/licenses.json')
  assert res.status_code == 200
  data = res.json()

  with open('static/bigquery-license-count.json') as f:
    stats = {e['license']: e['count'] for e in json.load(f)}

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
    licenses.append({'id': license_id, 'name': license['name'], 'priority': key})

  licenses.sort(key=lambda l: l['priority'])
  for i, license in enumerate(licenses):
    license['priority'] = i
  with open(pjoin(dest, _filepath), 'w+') as f:
    json.dump(licenses, f)

  meta['licenses-file'] = _filepath
  meta['licenses-version'] = data['licenseListVersion']
