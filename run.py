#!bin/python
from app import app
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--prod", help="increase output verbosity", action="store_true")
args = parser.parse_args()

ip = '127.0.0.1'
if args.prod:
    ip = '0.0.0.0'

app.run(debug=False, host=ip)
