""" Get statistics from cloud discovery """

# TODO
# - Lambda
# - EC2
# - AKS
# - Everything else

# pylint: disable=import-error
import pprint

from prismacloud.api import pc_api, pc_utility

# --Configuration-- #

parser = pc_utility.get_arg_parser()
parser.add_argument(
    '--detailed',
    action="store_true",
    help="(Optional) - Detailed results"
)
parser.add_argument(
    '--output_to_csv',
    action="store_true",
    help="(Optional) - Write results to host_inventory.csv"
)
args = parser.parse_args()

csvoutfile = ''

# --Helpers-- #

def output(*a):
    print(*a)
    if args.output_to_csv:
        print(*a, file=csvoutfile)

# --Initialize-- #

settings = pc_utility.get_settings(args)
pc_api.configure(settings)

# --Main-- #

discovery = pc_api.cloud_discovery_read()

if args.output_to_csv:
    csvoutfile = open("workload_defense_inventory.csv", "w")

aws_ec2 = 0
aws_ec2_defended = 0
aws_lambda = 0
aws_lambda_defended = 0
aws_ecs = 0
aws_ecs_defended = 0
aws_eks = 0
aws_eks_defended = 0
aws_eks_clusters = []
aws_ecs_ec2_clusters = []
aws_fargate_tasks = []
aws_ecr = 0
aws_ecr_defended = 0

print('Account, Region, Service, Defended Count, Total Count')
services = {'aws-ec2', 'aws-lambda', 'aws-ecs', 'aws-eks', 'aws-ecr'}
for item in discovery:
    if 'err' in item:
        continue
    service = item['serviceType']
    if item['provider'] == 'aws':
        service = item['serviceType']
        if service not in services:
            continue
        if service == 'aws-ec2':
            print('%s, %s, %s, %s, %s' % (item['accountID'], item['region'], service, item['defended'], item['total']))
            aws_ec2 += item['total']
            aws_ec2_defended += item['defended']
        elif service == 'aws-lambda':
            print('%s, %s, %s, %s, %s' % (item['accountID'], item['region'], service, item['defended'], item['total']))
            aws_lambda += item['total']
            aws_lambda_defended += item['defended']
        elif service == 'aws-ecs':
# Prisma Compute ECS with EC2 deployment coverage
# Prisma Compute ECS with Fargate deployment coverage
#            pprint.pprint(item)
            for entity in item['entities']:
#                pprint.pprint(entity)
                # nodesCount > 0 implies ECS on EC2
                if entity['nodesCount'] > 0:
                    print('%s, %s, %s, %s, %s' % (item['accountID'], item['region'], service, entity['defended'], entity['runningTasksCount']))
                    cluster = {'accountID': item['accountID'], 'region': item['region'], 'defended': entity['defended'], 'name': entity['name'], 'arn': entity['arn']}
                    aws_ecs_ec2_clusters.append(cluster)
                    aws_ecs += 1
                    if entity['defended']:
                        aws_ecs_defended += 1                 
                else:
                    # Should be Fargate
#                    print('fargate item')
#                    pprint.pprint(entity)
                    continue
        elif service == 'aws-eks':
#            pprint.pprint(item)
            if args.detailed:
                item.pop('collections')
            aws_eks_clusters.append(item)
            print('%s, %s, %s, %s, %s' % (item['accountID'], item['region'], service, item['defended'], item['total']))
            aws_eks += item['total']
            aws_eks_defended += item['defended']
        elif service == 'aws-ecr':
            print('%s, %s, %s, %s, %s' % (item['accountID'], item['region'], service, item['defended'], item['total']))
            aws_ecr += item['total']
            aws_ecr_defended += item['defended']
        else:
            print('Unknown AWS service: %s' % service)
    elif item['provider'] == 'azure':
#        pprint.pprint(item)
        continue
    else:
        continue

# Special handling for Fargate that is only compatible with SaaS

undefended_fargate_rql = 'config from cloud.resource where api.name = \'aws-ecs-describe-task-definition\' AND json.rule = containerDefinitions[*].name does not equal "TwistlockDefender" and status equals "ACTIVE"'
all_fargate_rql = 'config from cloud.resource where api.name = \'aws-ecs-describe-task-definition\' AND json.rule = status equals "ACTIVE"'

search_params = {'query': undefended_fargate_rql}
undefended_fargate = pc_api.search_config_read(search_params)
search_params = {'query': all_fargate_rql}
all_fargate = pc_api.search_config_read(search_params)
#pprint.pprint(undefended_fargate)

# Print totals

print('Summary Totals by Account')
print('EC2: %d/%d' % (aws_ec2_defended, aws_ec2))
print('EKS: %d/%d' % (aws_eks_defended, aws_eks))
print('Lambda: %d/%d' % (aws_lambda_defended, aws_lambda))
print('ECS on EC2: %d/%d' % (aws_ecs_defended, aws_ecs))
print('ECR: %d/%d' % (aws_ecr_defended, aws_ecr))
print('Fargate: %d/%d' % (len(undefended_fargate), len(all_fargate)))

if args.detailed:
    print('Detailed List of Undefended Workloads')
    output('Service, Account, Region, Cluster, Defended, ARN')
    for item in aws_eks_clusters:
        for entity in item['entities']:
            output('aws-eks, %s, %s, %s, %s, %s' % (item['accountID'], item['region'], entity['name'], entity['defended'], entity['arn']))

    for item in aws_ecs_ec2_clusters:
        output('aws-ecs, %s, %s, %s, %s, %s' % (item['accountID'], item['region'], item['name'], item['defended'], item['arn']))

    for task in undefended_fargate:
        accountID = task['accountId']
        region = task['regionId']
        cluster = 'N/A'
        defended = False
        arn = task['data']['taskDefinitionArn']
        output('aws-fargate, %s, %s, %s, %s, %s' % (accountID, region, cluster, defended, arn))
