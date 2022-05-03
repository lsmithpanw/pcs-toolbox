""" Export a specific Compliance Standard trend by a given time tange """

# pylint: disable=import-error
from prismacloud.api import pc_api, pc_utility
import json
import csv
import datetime

# --Configuration-- #

DEFAULT_COMPLIANCE_EXPORT_FILE_VERSION = 3

parser = pc_utility.get_arg_parser()
parser.add_argument(
    '--concurrency',
    type=int,
    default=0,
    help='(Optional) - Number of concurrent API calls. (1-16)')
parser.add_argument(
    'compliance_standard_name',
    type=str,
    help='Name of the Compliance Standard to export.')
args = parser.parse_args()

# --Initialize-- #

settings = pc_utility.get_settings(args)
pc_api.configure(settings)

# --Main-- #

# Avoid API rate limits.
if args.concurrency > 0 and args.concurrency <= 16:
    pc_api.max_workers = args.concurrency
print('Limiting concurrent API calls to: (%s)' % pc_api.max_workers)
print()

print('API - Getting compliance data')
"""
POST https://api.prismacloud.io/compliance/posture/trend/54dbfe71-4236-4aff-9eaa-1fc5ff3bf2f1

{
    "filters": [
        {
            "operator": "=",
            "name": "cloud.type",
            "value": "aws"
        },
        {
            "operator": "=",
            "name": "policy.complianceStandard",
            "value": "NIST CSF"
        },
        {
            "operator": "=",
            "name": "complianceId",
            "value": "54dbfe71-4236-4aff-9eaa-1fc5ff3bf2f1"
        }
    ],
    "timeRange": {
        "type": "to_now",
        "value": "epoch"
    }
}

jq -r 'map({timestamp,failedResources,failedResources,totalResources,highSeverityFailedResources,mediumSeverityFailedResources,lowSeverityFailedResources}) | (first | keys_unsorted) as $keys | map([to_entries[] | .value]) as $rows | $keys,$rows[] | @csv' trend.json

"""
get_query_params = {
    "timeType": "relative",
    "timeAmount": "12",
    "timeUnit": "month",
    "policy.complianceStandard": args.compliance_standard_name
}
post_body_params = {
    "filters": [
        {
            "operator": "=",
            "name": "cloud.type",
            "value": "aws"
        },
        {
            "operator": "=",
            "name": "policy.complianceStandard",
            "value": args.compliance_standard_name
        }
    ],
    "timeRange": {
        "type": "relative",
        "value": {
           "amount": 3,
           "unit": "day" 
        }
    }
}
compliance_trend = pc_api.compliance_posture_get(query_params=get_query_params)
#compliance_trend = pc_api.compliance_posture_trend_get(query_params=get_query_params)
#compliance_trend = pc_api.compliance_posture_trend_post(body_params=post_body_params)
with open('trend.json', 'w') as outfile:
    json.dump(compliance_trend, outfile)
headers = ['timestamp', 'failedResources', 'passedResources', 'totalResources', 'highSeverityFailedResources', 'mediumSeverityFailedResources', 'lowSeverityFailedResources']
with open('trend.csv', 'w') as csv_outfile:
    writer = csv.DictWriter(csv_outfile, fieldnames=headers)
    writer.writeheader()
#    writer.writerows(compliance_trend)

#ts = compliance_trend[0]['timestamp']/1000
#dt = datetime.datetime.fromtimestamp(ts)
#print('num data points: %d, first time stamp: %d - %s' % (len(compliance_trend), ts, dt))
#print(dt)

"""
csv_outfile = open('trend.csv', 'w')
csv_writer = csv.writer(compliance_trend)
count = 0
for datapoint in compliance_trend:
    if count == 0:
        header = compliance_trend.keys()
        csv_writer.writerow(header)
        count += 1
    csv_writer.writerow(emp.values())
csv_outfile.close()
"""