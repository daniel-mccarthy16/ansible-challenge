#!/usr/bin/env python3

import boto3
import json
import subprocess
import os
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

def start_ssh_agent():
    agent_output = subprocess.run(["ssh-agent"], capture_output=True, text=True)
    if agent_output.returncode != 0:
        raise Exception(f"Error starting SSH agent: {agent_output.stderr}")

    agent_vars = agent_output.stdout
    agent_vars_dict = {}
    for line in agent_vars.split('\n'):
        if 'SSH_AUTH_SOCK' in line or 'SSH_AGENT_PID' in line:
            key, value = line.replace('export ', '').split('=')
            agent_vars_dict[key.strip()] = value.strip().split(';')[0]
    
    print(f"SSH agent started with variables: {agent_vars_dict}")
    os.environ.update(agent_vars_dict)
    return agent_vars_dict

def add_ssh_key_to_agent(ssh_key):
    print(f"Adding SSH key to agent with SSH_AUTH_SOCK={os.environ.get('SSH_AUTH_SOCK')}")
    ssh_add = subprocess.run(["ssh-add", "-"], input=ssh_key, capture_output=True, text=True, env=os.environ)
    if ssh_add.returncode != 0:
        raise Exception(f"Error adding SSH key to agent: {ssh_add.stderr}")

def main():
    tag_key = 'Name'
    tag_values = ['ansible_vm1', 'ansible_vm2']
    secret_name = 'AnsChallengeEC2KeyPairSecret'

    all_instances = get_instances_by_tag(tag_key, tag_values)
    ssh_key = fetch_ssh_key(secret_name)

    print(f"Initial SSH_AUTH_SOCK: {os.environ.get('SSH_AUTH_SOCK')}")
    print(f"Initial SSH_AGENT_PID: {os.environ.get('SSH_AGENT_PID')}")

    # Start ssh-agent and add the key
    try:
        agent_vars_dict = start_ssh_agent()
    except Exception as e:
        print(f"Failed to start SSH agent: {e}")
        return

    print(f"Updated SSH_AUTH_SOCK: {os.environ.get('SSH_AUTH_SOCK')}")
    print(f"Updated SSH_AGENT_PID: {os.environ.get('SSH_AGENT_PID')}")
    print(f"SSH agent environment: {agent_vars_dict}")

    try:
        add_ssh_key_to_agent(ssh_key)
    except Exception as e:
        print(f"Failed to add SSH key to agent: {e}")
        return

    # Filter instances that have a public IP address
    public_ips = [instance['PublicIpAddress'] for instance in all_instances if 'PublicIpAddress' in instance]

    inventory = {
        'all': {
            'hosts': public_ips,
            'vars': {
                'ansible_user': 'ec2-user',
                'ssh_agent_pid': agent_vars_dict['SSH_AGENT_PID'],
                'ssh_auth_sock': agent_vars_dict['SSH_AUTH_SOCK']
            }
        }
    }

    print(json.dumps(inventory, indent=2, default=json_serial))

if __name__ == '__main__':
    main()
