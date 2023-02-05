![enter image description here](https://i.imgur.com/6awUP3Q.png)

A collection of scripts and parsers to extract DNS query logs from the long-term query database of a Pihole instance and ingest them into the Falcon Logscale (Humio) platform.
# Usage
This will retrieve the last **x** amount of messages depending on the options you configure (e.g. last 5 minutes) and send them to your logscale instance via the ingest api. Set this script to run as a scheduled task or cron job to retrieve your DNS queries at regular intervals.
To run succesfully this tool needs a few parameters:
- **logscale_url**: This is the url of your logscale instance. If you are using the cloud hosted version of logscale this will be 'https://cloud.humio.com' or 'https://cloud.community.humio.com'
- **ingest_token**: This is the api token used to ingest data into your instance. It can be retrieved from the settings page in the Logscale console. Ensure the token you choose has the parser found in this repo assigned to it so that it can break out incoming messages into fields. Instructions below on how to set this up.
- **interval_unit**: The units for how far back in time you want to retrieve messages. Available options are "HOURS", "MINUTES", "SECONDS".
- **interval_value**: The value for how far back in time you want to retrieve messages. 
- **database**: Path the to the 'pihole-FTL.db' file containing your query data. The default value for this is '/etc/pihole/pihole-FTL.db'.

You have two options for supplying the neccesary parameters for the script to run,
### Use the Config file
You can run the script with a config file containg the required information. Review the 'sample_config.yml' file in this repo for a list of the available options
#### Example
> ./PiholeLogscale.py -c ./config.yml 
### Run as CLI Tool 
You can use the below options to provide the required info at runtime.
#### Example
> ./PiholeLogscale.py -u "https://cloud.community.humio.com" -i "<INGEST_TOKEN>" --interval_unit "HOURS" --interval_value "1"
##### CLI Options
>usage: PiholeLogscale.py [-h] [-c CONFIG] [-u LOGSCALE_URL] [-i INGEST_TOKEN] [-iu {MINUTES,SECONDS,HOURS}] [-iv INTERVAL_VALUE] [-d DATABASE]
>
>options:
>  -h, --help            show this help message and exit
>  -c CONFIG, --config CONFIG
>                        Specify path to config.yml. If this is used, any other switches are ignored.
>
>  -u LOGSCALE_URL, --logscale_url LOGSCALE_URL
>                        FQDN:PORT of your logscale instance. e.g. https://cloud.community.humio.com
>
>  -i INGEST_TOKEN, --ingest_token INGEST_TOKEN
>                        Ingest token from the Falcon Logscale portal. Ensure the Pihole-sqlite3 parser is assigned to this token.
>                        
>  -iu {MINUTES,SECONDS,HOURS}, --interval_unit {MINUTES,SECONDS,HOURS}
>                        The units for the time you want to fetch messages from. e.g MINUTES and 5 = retrieve last 5 minutes of queries.
>
>  -iv INTERVAL_VALUE, --interval_value INTERVAL_VALUE
>                        How far back in time you want to retrieve messages. Default Value: 5
>
>  -d DATABASE, --database DATABASE
>                        Specify path to pihole-ftl.db. Default value: /etc/pihole/pihole-FTL.db

# Setting up the Parser and Ingest Token
To make use of the ingested messages you need a valid parser in logscale to break up the raw message string into searchable fields.

This repo contains a parser in 'LogscaleTemplates/pihole-sqlite3.yml' To use this with your logscale instance, create a new parser from the Parsers page in your logscale repository and then select the '**From Template**' option and select the '**pihole-sqlite3.yml**' file.

Finally create a new ingest token from the settings page and when prompted to assign a parser, choose the new parser you created above.
You should now be ready to send messages into your instance and have them parsed correctly.