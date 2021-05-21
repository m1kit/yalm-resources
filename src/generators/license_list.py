import requests
from os.path import join as pjoin
import json

_filepath = 'licenses.json'

def generate(dest):
  res = requests.get('https://spdx.org/licenses/licenses.json')
  assert res.status_code == 200
  data = res.json()
  with open('static/bigquery-license-count.json') as f:
    stats = {e['license']: e['count'] for e in json.load(f)}
  licenses = []
  for license in data['licenses']:
    count = stats.get(license['licenseId'].lower(), 0)
    # the more smaller key is, the more frequently used
    key = (
      -count,
      not license['isOsiApproved'],
      not license['isDeprecatedLicenseId'],
      license['licenseId'],
    )
    licenses.append({
      'id': license['licenseId'],
      'name': license['name'],
      'priority': key,
    })
  licenses.sort(key=lambda l: l['priority'])
  for i, license in enumerate(licenses):
    license['priority'] = i
  with open(pjoin(dest, _filepath), "w+") as f:
    json.dump(licenses, f)
  return {
      'licenses-file': _filepath,
      'licenses-version': data['licenseListVersion'],
  }
