#!/usr/bin/env python3

import boto3
import json
from datetime import datetime
import subprocess

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Type {type(obj)} not serializable')

def get_instances_by_tag(tag_key, tag_values):
    ec2 = boto3.client('ec2', region_name='ap-southeast-2')
    filters = [{'Name': f'tag:{tag_key}', 'Values': tag_values}]
    response = ec2.describe_instances(Filters=filters)
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] == 'running':
                instances.append(instance)
    return instances


def main():
    tag_key = 'Name'
    tag_values = ['ansible_vm1', 'ansible_vm2']
    secret_name = 'AnsChallengeEC2KeyPairSecret'

    all_instances = get_instances_by_tag(tag_key, tag_values)

    # Filter instances that have a public IP address
    public_ips = [instance['PublicIpAddress'] for instance in all_instances if 'PublicIpAddress' in instance]

    inventory = {
        'all': {
            'hosts': public_ips,
            'vars': {
                'ansible_user': 'ec2-user',
            }
        }
    }

    print(json.dumps(inventory, indent=2))

if __name__ == '__main__':
    main()
