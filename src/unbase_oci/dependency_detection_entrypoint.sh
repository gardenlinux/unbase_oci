#!/usr/bin/env sh

pip install --break-system-packages unbase_oci
python3 -m unbase_oci scan --unbase-inplace-file ./unbase_inplace.json --python-env-self-dependencies true --requirements-schemes-file ./unbase_schemes.json
