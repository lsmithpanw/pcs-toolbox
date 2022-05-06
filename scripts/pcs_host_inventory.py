""" Get host inventory """

import json

# pylint: disable=import-error
from prismacloud.api import pc_api, pc_utility

# --Configuration-- #

parser = pc_utility.get_arg_parser()
parser.add_argument(
    '--hostname',
    type=str,
    help='(Optional) - target hostname')
parser.add_argument(
    '--output_to_csv',
    action="store_true",
    help="(Optional) - Write results to host_inventory.csv"
)
parser.add_argument(
    '--quiet',
    action="store_true",
    help="(Optional) - Less console output"
)

args = parser.parse_args()
csvoutfile = ""

# --Helpers-- #

def output(*a):
    if not args.quiet:
        print(*a)
    if args.output_to_csv:
        print(*a, file=csvoutfile)

# --Initialize-- #

settings = pc_utility.get_settings(args)
pc_api.configure(settings)
pc_api.validate_api_compute()

# --Main-- #

print('Testing Compute API Access ...', end='')
intelligence = pc_api.statuses_intelligence()
print(' done.')

hosts = pc_api.execute_compute('GET', 'api/v1/hosts')

with open("host_inventory.json", "w") as outfile:
    json.dump(hosts, outfile, indent=3)

if args.output_to_csv:
    csvoutfile = open("host_inventory.csv", "w")

output("host, package, version, source, cloudProvider, cloudaccount, resourceid, platformname, platformversion, platformrelease, platformdistro")
for host in hosts:
    if args.hostname and host['hostname'] != args.hostname:
        continue

    cloudProvider = ""
    cloudaccount = ""
    resourceid = ""
    platformname = ""
    platformversion = ""
    platformrelease = ""
    platformdistro = ""

    if 'cloudMetadata' in host and 'provider' in host['cloudMetadata']:
        cloudProvider = host["cloudMetadata"]["provider"]

    if 'cloudMetadata' in host and 'accountID' in host['cloudMetadata']:
        cloudaccount = host["cloudMetadata"]["accountID"]

    if 'cloudMetadata' in host and 'resourceID' in host['cloudMetadata']:
        resourceid = host["cloudMetadata"]["resourceID"]

    if 'osDistro' in host:
        platformname = host["osDistro"]

    if 'osDistro' in host:
        platformversion = host["osDistroVersion"]

    if 'osDistro' in host:
        platformrelease = host["osDistroRelease"]

    if 'osDistro' in host:
        platformdistro = host["distro"]

    if 'applications' in host:
        for app in host['applications']:
            output("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" % (host['hostname'], app['name'], app['version'], "applications", cloudProvider, cloudaccount, resourceid, platformname, platformversion, platformrelease, platformdistro))

    if 'binaries' in host:
        for binary in host['binaries']:
            output("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" % (host['hostname'], binary['name'], "", "binaries", cloudProvider, cloudaccount, resourceid, platformname, platformversion, platformrelease, platformdistro))

    if 'packages' in host:
        for package in host['packages']:
            if 'pkgs' in package:
                for pkg in package['pkgs']:
                    output("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" % (host['hostname'], pkg['name'], pkg['version'], "packages", cloudProvider, cloudaccount, resourceid, platformname, platformversion, platformrelease, platformdistro))

"""
    del host["complianceIssues"]
    del host["applications"]
    del host["binaries"]
    del host["packages"]
    del host["vulnerabilities"]
    with open("host.json", "w") as outfile:
        json.dump(host, outfile, indent=3)
"""
if args.output_to_csv:
    csvoutfile.close()
