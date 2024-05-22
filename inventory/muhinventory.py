import boto3
import json
from datetime import datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Type {type(obj)} not serializable')

def get_instances_by_tag(tag_key, tag_values):
    ec2 = boto3.client('ec2', region_name='ap-southeast-2')
    filters = [{'Name': f'tag:{tag_key}', 'Values': tag_values}]
    response = ec2.describe_instances(Filters=filters)
    # Print the raw response with datetime objects converted to strings
    print(json.dumps(response, indent=2, default=json_serial))
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] == 'running':
                instances.append(instance)
    return instances

def fetch_ssh_key(secret_name):
    secrets_manager = boto3.client('secretsmanager', region_name='ap-southeast-2')
    response = secrets_manager.get_secret_value(SecretId=secret_name)
    return response['SecretString']

def main():
    tag_key = 'Name'
    tag_values = ['ansible_vm1', 'ansible_vm2']
    secret_name = 'AnsChallengeEC2KeyPairSecret'

    all_instances = get_instances_by_tag(tag_key, tag_values)

    # Debug step: Print out instance details
    for instance in all_instances:
        print(json.dumps(instance, indent=2, default=json_serial))

    ssh_key = fetch_ssh_key(secret_name)

    # Filter instances that have a public IP addresg
    public_ips = [instance['PublicIpAddress'] for instance in all_instances if 'PublicIpAddress' in instance]

    inventory = {
        'all': {
            'hosts': public_ips,
            'vars': {
                'ansible_user': 'ec2-user',
                'ansible_ssh_private_key_content': ssh_key
            }
        }
    }

    print(json.dumps(inventory, indent=2))

if __name__ == '__main__':
    main()
