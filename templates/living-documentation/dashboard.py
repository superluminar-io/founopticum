import boto3
import json
import os
from datetime import datetime

cw = boto3.client("cloudwatch")
ssm = boto3.client("ssm")

def handler(event, context):

    superwerker_config = {}
    for ssm_parameter in ssm.get_parameters(
            Names=[
                '/superwerker/domain_name_servers'
            ]
    )['Parameters']:
        superwerker_config[ssm_parameter['Name']] = ssm_parameter['Value']


    rootmail_ready_alarm_state = cw.describe_alarms(
        AlarmNames=[
            'superwerker-RootMailReady',
        ]
    )['MetricAlarms'][0]['StateValue']

    if rootmail_ready_alarm_state == 'OK':
        dns_delegation_text = """
        #### 🏠 {domain}
        #### ✅ DNS configuration is set up correctly. 
        """.format(
            domain=os.environ['SUPERWERKER_DOMAIN'],
        )
    else:
        if '/superwerker/domain_name_servers' in superwerker_config:
            dns_delegation_text = """
        #### 🏠 {domain}
        #### ❌ DNS configuration needed. 

        &nbsp;

        ### Next Steps 

        Please create the following NS records for your domain:

        ```
        {ns[0]}
        {ns[1]}
        {ns[2]}
        {ns[3]}
        ```
        """.format(
                domain=os.environ['SUPERWERKER_DOMAIN'],
                ns=superwerker_config['/superwerker/domain_name_servers'].split(','),
            )
        else:
            dns_delegation_text = '### DNS Setup pending'

    markdown = """
        # [superwerker](https://github.com/superwerker/superwerker)
        &nbsp;

        {dns_delegation}

        &nbsp;

        ```
        Updated at {current_time} (use browser reload to refresh)
        ```
          """.format(
        dns_delegation=dns_delegation_text,
        current_time=datetime.now(),
    )

    body = {
        "widgets": [
            {
                "type": "text",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 20,
                "properties": {
                    "markdown": markdown,
                }
            }
        ]
    }

    cw.put_dashboard(
        DashboardName='superwerker',
        DashboardBody=json.dumps(body),
    )

def log(msg):
    print(json.dumps(msg), flush=True)