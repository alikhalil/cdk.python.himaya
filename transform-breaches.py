#!/usr/bin/env python3
#
# This script will transform the full breaches list from HIBP to allow faster 
# lookup of breach information when enriching the results for an account search
#

import requests
import json

OUTPUT_FILE = 'src/breaches.json'
HIBP_BREACHES_URL = 'https://haveibeenpwned.com/api/v3/breaches'

r = requests.get(HIBP_BREACHES_URL)

original_breaches = r.json()
new_breaches = {}

for breach in original_breaches:
    new_breaches[breach['Name']] = breach

fh = open(OUTPUT_FILE, 'w')
fh.write(
    json.dumps(
        new_breaches,
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
        )
    )
fh.close()
