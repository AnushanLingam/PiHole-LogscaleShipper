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

def verify_interval_settings(interval_unit, interval_value):
    if not ((interval_unit == "MINUTES") or (interval_unit == "SECONDS") or (interval_unit == "HOURS")):
        print(Fore.RED + f'ERROR - Unexpected value "{interval_unit}" specified for message retrieval interval units. Allowed values are "MINUTES" or "SECONDS" or "HOURS.')
        raise SystemExit(1)
    
    try:
        int(interval_value)
    except:
        print(Fore.RED + f'ERROR - Failed to parse value "{interval_value}" into a valid integer.')
        raise SystemExit(1)


init()
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", action="store", help="Specify path to config.yml. If this is used, any other switches are ignored.")
parser.add_argument("-u", "--logscale_url", action="store", help="FQDN:PORT of your logscale instance. e.g. https://cloud.community.humio.com")
parser.add_argument("-i", "--ingest_token", action="store", help="Ingest token from the Falcon Logscale portal. Ensure the Pihole-sqlite3 parser is assigned to this token.")
parser.add_argument("-iu", "--interval_unit", action="store", choices=["MINUTES","SECONDS", "HOURS"], default="MINUTES", help="The units for the time you want to fetch messages from. e.g MINUTES and 5 = retrieve last 5 minutes of queries. Default Value: MINUTES")
parser.add_argument("-iv", "--interval_value", action="store", default=5, help="How far back in time you want to retrieve messages. Default Value: 5")
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
        interval_unit = options["message_retrieval"]["units"]
        interval_value = options["message_retrieval"]["interval"]
        pihole_db = options["pihole_db"]

        # Verify config options
        verify_url(logscale_url)
        verify_ingest_token(logscale_url, ingest_token)
        verify_interval_settings(interval_unit, interval_value)




#print(args)