# ANSIBLE CHALLENGE

## Prerequisites

1. **Python Virtual Environment and Packages**

    Create a Python virtual environment and install the necessary packages.

    ```sh
    python3 -m venv pythonenv
    source pythonenv/bin/activate
    pip install ansible boto3
    ```
    **Note:** Ensure your shell has the necessary AWS permissions (It probably needs alot as the cdk will leverage them in creating all of its resources).

2. **Node.js**

    Install Node.js (used version 21.6, earlier versions should work).

3. **AWS CDK**

    Install AWS CDK globally:

    ```sh
    npm install -g aws-cdk
    cd /home/daniel/repos/ansible-challenge/aws_infrastructure
    npm install
    cdk bootstrap
    ```

4. **Create EC2 key pair and ACM self signed certificate**

Run the `setup-keys-and-cert.sh` script to set up your environment. This script creates a self-signed certificate and an EC2 key pair. It adds the key pair to Secrets Manager, which will be pulled on every execution of Ansible with our dynamic inventory file. The script also stores the ACM certificate ARN required by the CDK when attaching the certificate to the ALB. 

**Note:** For possible improvements, consider relying entirely on the CDK for the creation of these resources.


5. 
