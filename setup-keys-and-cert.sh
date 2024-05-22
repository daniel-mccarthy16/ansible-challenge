#!/bin/bash -x

# Set variables
REGION="ap-southeast-2"
KEY_NAME="ansible-challenge-keypair"
CERT_FILE="self-signed-cert.pem"
KEY_FILE="self-signed-key.pem"
EC2_SECRET_NAME="AnsChallengeEC2KeyPairSecret"
ACM_SECRET_NAME="AnsChallengeACMCertificateArn"

# Check if key pair exists
aws ec2 describe-key-pairs --region $REGION --key-names $KEY_NAME > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Creating key pair: $KEY_NAME"
  aws ec2 create-key-pair --region $REGION --key-name $KEY_NAME --query 'KeyMaterial' --output text > ${KEY_NAME}.pem
  chmod 400 ${KEY_NAME}.pem

  # Store key pair in Secrets Manager
  aws secretsmanager create-secret --region $REGION --name $EC2_SECRET_NAME --secret-string file://${KEY_NAME}.pem
  echo "Key pair $KEY_NAME created and stored in Secrets Manager"

  # Clean up the key file
  rm -f ${KEY_NAME}.pem
else
  echo "Key pair $KEY_NAME already exists."
fi

# Generate a self-signed certificate and import into ACM if the ACM secret does not exist
aws secretsmanager describe-secret --region $REGION --secret-id $ACM_SECRET_NAME > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Creating self-signed certificate"
  openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Department/CN=daniel.ansible.test.com" \
    -keyout $KEY_FILE -out $CERT_FILE

  # Ensure the certificate and private key are valid and correctly formatted
  openssl x509 -in $CERT_FILE -text -noout
  openssl rsa -in $KEY_FILE -check

  # Import the certificate into ACM using fileb:// to ensure correct reading of binary data
  ACM_ARN=$(aws acm import-certificate --region $REGION --certificate fileb://$CERT_FILE --private-key fileb://$KEY_FILE --output text --query 'CertificateArn')

  # Check if ACM_ARN is not empty
  if [ -n "$ACM_ARN" ]; then
    # Store ACM ARN in Secrets Manager
    aws secretsmanager create-secret --region $REGION --name $ACM_SECRET_NAME --secret-string "$ACM_ARN"
    echo "ACM certificate imported and ARN stored in Secrets Manager"
  else
    echo "Failed to import ACM certificate."
  fi

  # Clean up certificate files
  rm -f $CERT_FILE $KEY_FILE
else
  echo "Certificate ARN secret $ACM_SECRET_NAME already exists."
fi
