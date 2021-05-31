import requests
from os.path import join as pjoin
import json

_filepath = 'equivalentwords.json'


def generate(dest, meta):
  print(f"Generating '{_filepath}'...")
  res = requests.get('https://spdx.org/licenses/equivalentwords.txt')
  assert res.status_code == 200
  content = res.content.decode()

  pairs = []
  for line in content.strip().split('\n'):
    t, s = line.split(',')
    pairs.append({'from': s, 'to': t})

  with open(pjoin(dest, _filepath), "w+") as f:
    json.dump(pairs, f)

  meta['equivalentwords-file'] = _filepath
