import sqlite3
import datetime
import socket
import requests
import json

def query_db(sqlite_path, query):
   try:
    sqlite_conn = sqlite3.connect(sqlite_path)
    cursor = sqlite_conn.cursor()

    print(f'Connected to DB {sqlite_path} succesfully')

    cursor.execute(query) 
    records = cursor.fetchall()
    cursor.close()
    if len(records) == 0:
        sqlite_conn.close()
        print("Closed connection to sqlite DB")
        print("Exiting - No new messages found.")
        quit()
    print(f'Retrieved {len(records)} results from query {query}')
    return records
   except sqlite3.Error as error:
    print(f'Error executing query: {error}')
   finally:
    if sqlite_conn:
        sqlite_conn.close()
        print("Closed connection to sqlite DB")

def generate_timeInterval(interval):
    req_time = datetime.datetime.now() - datetime.timedelta(minutes=interval)
    return int(req_time.timestamp())

def format_messages(records):
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
            "source_ip": str(host_ip)
        },
        "messages": messages
    }
    post_list.append(post_obj)
    return json.dumps(post_list)

def post_messages(post_body):
    req_url = "https://cloud.community.humio.com/api/v1/ingest/humio-unstructured"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer <ADD_INGEST_TOKEN_HERE>"
    }

    try:
        response = requests.post(req_url, headers=headers, data=post_body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print(errh)
    except requests.exceptions.ConnectionError as errc:
        print(errc)
    except requests.exceptions.Timeout as errt:
        print(errt)
    except requests.exceptions.RequestException as err:
        print(err)

results = query_db("/etc/pihole/pihole-FTL.db", f'SELECT timestamp, type, status, domain, client, name, forward, additional_info, reply_type, reply_time, dnssec FROM queries INNER JOIN client_by_id ON client_by_id.ip = queries.client WHERE timestamp >= {generate_timeInterval(1)};')

messages = format_messages(results)

post_body = generate_logscale_post(messages)

post_messages(post_body)

