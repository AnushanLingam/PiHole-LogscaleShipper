#!/usr/bin/python3

import argparse
import yaml
import requests
from pathlib import Path
from colorama import init
from colorama import Fore, Back, Style
from urllib.parse import urlparse

def verify_url(url):
    try:
        result = urlparse(url)
        if all([result.scheme, result.netloc]):
            return True
        else:
            print(Fore.RED + f'ERROR - The logscale url "{logscale_url}" is not valid.')
            raise SystemExit(1)
    except ValueError:
        print(Fore.RED + f'ERROR - The logscale url "{logscale_url}" is not valid.')
        raise SystemExit(1)


def verify_ingest_token(logscale_url, ingest_token):

    req_url = f'{logscale_url}/api/v1/ingest/humio-unstructured'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {ingest_token}'
    }

    response = requests.post(req_url, headers=headers)
    if response.status_code == 401:
        print(Fore.RED + f'ERROR - The ingest token "{ingest_token}" is not valid.')
        raise SystemExit(1)
    elif (not response.status_code == 401) and (not response.status_code == 400):
        print(Fore.RED + f'ERROR - Failed to validate ingest token "{ingest_token}". HTTP Response; {response.status_code} {response.reason}')
        raise SystemExit(1)



init()
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", action="store", help="Specify path to config.yml. If this is used, any other switches are ignored.")
parser.add_argument("-u", "--logscale_url", action="store", help="FQDN:PORT of your logscale instance. e.g. https://cloud.community.humio.com")
parser.add_argument("-i", "--ingest_token", action="store", help="Ingest token from the Falcon Logscale portal. Ensure the Pihole-sqlite3 parser is assigned to this token.")
parser.add_argument("-iu", "--interval_unit", action="store", choices=["MINUTES","SECONDS"], default="MINUTES", help="Specify path to config.yml. If this is used, any other switches are ignored. Default Value: MINUTES")
parser.add_argument("-iv", "--interval_value", action="store", default=5, help="Specify path to config.yml. If this is used, any other switches are ignored. \n Default Value: 5")
parser.add_argument("-d", "--database", action="store", default="/etc/pihole/pihole-FTL.db", help="Specify path to pihole-ftl.db. Default value: /etc/pihole/pihole-FTL.db")

args = parser.parse_args()

if args.config:
    config_path = Path(args.config)
    if not config_path.exists():
        print(Fore.RED + "ERROR - Config file not found at specified location: '{config_path}'")
        raise SystemExit(1)
    else:
        # Load YAML Config file
        with open(config_path, "r") as stream:
            try:
                options = yaml.safe_load(stream)
            except yaml.YAMLError as err:
                print(Fore.RED + "ERROR - Failed to parse YAML file. See stacktrace below")
                print(err)
                raise SystemExit(1)
        
        # Set variables
        logscale_url = options["logscale_url"]
        ingest_token = options["ingest_token"]
        retrieval_units = options["message_retrieval"]["units"]
        retrieval_interval = options["message_retrieval"]["interval"]

        # Verify config options
        verify_url(logscale_url)
        verify_ingest_token(logscale_url, ingest_token)





#print(args)