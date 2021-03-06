#!/usr/bin/env python3
#
# This script will transform the full breaches list from HIBP to allow faster 
# lookup of breach information when enriching the results for an account search
#

import requests
import json
from pprint import pformat


OUTPUT_FILE = 'src/breaches.py'
HIBP_BREACHES_URL = 'https://haveibeenpwned.com/api/v3/breaches'

r = requests.get(HIBP_BREACHES_URL)

original_breaches = r.json()
new_breaches = {}

for breach in original_breaches:
    new_breaches[breach['Name']] = breach

OUTPUT_CONTENT = 'breaches = {}'.format(pformat(new_breaches))
fh = open(OUTPUT_FILE, 'w')
fh.write(OUTPUT_CONTENT)
fh.close()
