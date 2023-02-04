# Pihole-LogscaleShipper

Python utility that can grab DNS query requests from the PiHole SQLite3 DB at set intervals and send them to Falcon Logscale. 


# Instruction

### pihole_siem.py
The main python application, you will need to replace the location of the SQLite DB if you have moved it from the default pihole location. You can find this in the call to the 'query_db' function.
You will also need to replace add your falcon logscale ingest token and ensure that parser file is imported and assigned to this token in the console. The token needs to be added in the 'post_messages' function.

### pihole-sqlite3.yml
This is the parser that will break out the incoming messages into fields within logscale.
You will need to create a new parser in the logscale console and choose the 'From Template' option and import this file.
Finally, create your ingest token and assign the newly created parser to it. 