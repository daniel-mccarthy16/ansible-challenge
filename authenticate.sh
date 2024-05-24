#!/bin/bash

# Fetch the SSH key from AWS Secrets Manager
SECRET_NAME="AnsChallengeEC2KeyPairSecret"
SSH_KEY=$(aws secretsmanager get-secret-value --region 'ap-southeast-2' --secret-id $SECRET_NAME --query SecretString --output text)

# Start the SSH agent and add the key
eval "$(ssh-agent -s > /dev/null)"
echo "$SSH_KEY" | ssh-add - > /dev/null 2>&1

# Verify the key was added
if ssh-add -L > /dev/null; then
  echo "SSH key added to agent."
else
  echo "Failed to add SSH key to agent."
  exit 1
fi

# Export the SSH_AUTH_SOCK and SSH_AGENT_PID for use in subsequent commands
export SSH_AUTH_SOCK
export SSH_AGENT_PID
