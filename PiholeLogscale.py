#!/usr/bin/python3

import argparse
import yaml
import requests
import sqlite3
import datetime
import socket
import requests
import json
from pathlib import Path
from colorama import init as colorama_init
from colorama import Fore, Back, Style
from urllib.parse import urlparse

def verify_url(url):
    try:
        result = urlparse(url)
        if all([result.scheme, result.netloc]):
            return True
        else:
            print(Fore.RED + f'ERROR - The logscale url "{url}" is not valid.')
            raise SystemExit(1)
    except ValueError:
        print(Fore.RED + f'ERROR - The logscale url "{url}" is not valid.')
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

def verify_pihole_db(db_path):
    if not Path(db_path).exists():
        print(Fore.RED + f'ERROR - Pihole DB file not found at specified location: "{db_path}"')
        raise SystemExit(1)

    with open(db_path, 'rb') as db:
        file_header = db.read(100)
    if not file_header[:16] == b'SQLite format 3\x00':
        print(Fore.RED + f'ERROR - File specified at "{db_path}" is not a valid SQLite DB file')
        raise SystemExit(1)

def format_messages(records):
    print("INFO - Formatting DB records to logscale message format.")
    messages = []
    for record in records:
        record = list(record)
        if record[5] == '':
            record[5] = 'None'
        messages.append(" ".join(map(str, record)))         
    return messages

def generate_logscale_post(messages):
    hostname = socket.gethostname()
    host_ip = socket.gethostbyname(hostname)
    post_list = []
    post_obj = {
        "fields": {
            "source": hostname,
            "source_ip": str(host_ip),
            "ShipperVersion": "1.0"
        },
        "messages": messages
    }
    post_list.append(post_obj)
    return json.dumps(post_list)

def ingest_messages(messages, logscale_url, ingest_token):
    post_body = generate_logscale_post(messages)
    req_url = f'{logscale_url}/api/v1/ingest/humio-unstructured'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {ingest_token}'
    }

    try:
        print("INFO - Attempting to send messages to ingest endpoint.")
        response = requests.post(req_url, headers=headers, data=post_body)
        response.raise_for_status()
        print("INFO - Messages succesfully sent to Logscale.")
    except requests.exceptions.HTTPError as errh:
        print(errh)
        raise SystemExit(1)
    except requests.exceptions.ConnectionError as errc:
        print(errc)
        raise SystemExit(1)
    except requests.exceptions.Timeout as errt:
        print(errt)
        raise SystemExit(1)
    except requests.exceptions.RequestException as err:
        print(err)
        raise SystemExit(1)

def generate_timeInterval(interval_value, interval_units):
    if interval_units == "MINUTES":
        req_time = datetime.datetime.now() - datetime.timedelta(minutes=interval_value)
    elif interval_units == "HOURS":
        req_time = datetime.datetime.now() - datetime.timedelta(hours=interval_value)
    elif interval_units == "SECONDS":
        req_time = datetime.datetime.now() - datetime.timedelta(seconds=interval_value)

    return int(req_time.timestamp())

def query_db(sqlite_path, interval_value, interval_units):
   query = f'SELECT timestamp, type, status, domain, client, name, forward, additional_info, reply_type, reply_time, dnssec FROM queries INNER JOIN client_by_id ON client_by_id.ip = queries.client WHERE timestamp >= {generate_timeInterval(interval_value, interval_units)};'
   try:
    sqlite_conn = sqlite3.connect(f'file:{sqlite_path}?mode=ro', uri=True)
    cursor = sqlite_conn.cursor()

    print(f'INFO - Connected to DB {sqlite_path} succesfully')

    cursor.execute(query) 
    records = cursor.fetchall()
    cursor.close()
    if len(records) == 0:
        sqlite_conn.close()
        print("INFO - Closed connection to sqlite DB")
        print("INFO - Exiting - No new messages found.")
        quit()
    print(f'INFO - Retrieved {len(records)} results from database.')
    return records
   except sqlite3.Error as error:
    print(Fore.RED + f'ERROR - Error executing query: {error}')
    if sqlite_conn:
        sqlite_conn.close()
        print("INFO - Closed connection to sqlite DB")
    raise SystemExit(1)
   finally:
    if sqlite_conn:
        sqlite_conn.close()
        print("INFO - Closed connection to sqlite DB")

def main():
    colorama_init()
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
            print(Fore.RED + f'ERROR - Config file not found at specified location: "{config_path}"')
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
            #verify_ingest_token(logscale_url, ingest_token)
            verify_interval_settings(interval_unit, interval_value)
            verify_pihole_db(pihole_db)

            #retrieve messages
            db_records = query_db(sqlite_path=pihole_db, interval_units=interval_unit, interval_value=interval_value)
            formatted_messages = format_messages(records=db_records)
            #ingest_messages(messages=formatted_messages, ingest_token=ingest_token, logscale_url=logscale_url)

    else:
        logscale_url = args.logscale_url
        ingest_token = args.ingest_token
        interval_unit = args.interval_unit
        interval_value = args.interval_value
        pihole_db = args.database

        should_exit = False
        
        if not logscale_url:
            print(Fore.RED + f'ERROR - Missing required parameter "--logscale_url"')
            should_exit = True
        if not ingest_token:
            print(Fore.RED + f'ERROR - Missing required parameter "--ingest_token"')
            should_exit = True
        if not interval_unit:
            print(Fore.RED + f'ERROR - Missing required parameter "--interval_unit"')
            should_exit = True
        if not interval_value:
            print(Fore.RED + f'ERROR - Missing required parameter "--interval_value"')
            should_exit = True     
        if not pihole_db:
            print(Fore.RED + f'ERROR - Missing required parameter "--pihole_db"')
            should_exit = True 
        
        if should_exit:
            raise SystemExit(1)

        # Verify config options
        verify_url(logscale_url)
        verify_ingest_token(logscale_url, ingest_token)
        verify_interval_settings(interval_unit, interval_value)
        verify_pihole_db(pihole_db)

        #retrieve messages
        db_records = query_db(sqlite_path=pihole_db, interval_units=interval_unit, interval_value=interval_value)
        formatted_messages = format_messages(records=db_records)
        #ingest_messages(messages=formatted_messages, ingest_token=ingest_token, logscale_url=logscale_url)

if __name__ == "__main__":
    main()