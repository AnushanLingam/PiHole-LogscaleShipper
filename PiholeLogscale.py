#!/usr/bin/python3

import argparse
import yaml
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
            return False
    except ValueError:
        return False






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
        print(Fore.RED + "ERROR - Config file not found at specified location.")
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
        
        # Verify config options
        if not verify_url(options["logscale_url"]):
            print(Fore.RED + "ERROR - The value for 'logscale_url' is not a valid URL.")
            raise SystemExit(1)

#print(args)