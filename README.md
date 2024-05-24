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

2. **Create EC2 key pair and ACM self signed certificate**

	Run the `setup-keys-and-cert.sh` script to set up your environment. This script creates a self-signed certificate and an EC2 key pair. It adds the key pair to Secrets Manager, which will be pulled on every execution of Ansible with our dynamic inventory file. The script also stores the ACM certificate ARN required by the CDK when attaching the certificate to the ALB. 

3. **Node.js**

    Install Node.js (used version 21.6, earlier versions should work).

4. **AWS CDK**

    Install AWS CDK globally:

    ```sh
    npm install -g aws-cdk
    cd ./aws_infrastructure
    npm install
    cdk bootstrap
    cdk deploy
    ```

**Note:** For possible improvements, consider relying entirely on the CDK for the creation of these resources.

5. **Authenticate SSH Key**

	Run the authenticate.sh script to fetch the SSH key from AWS Secrets Manager and add it to the SSH agent. This step is predicated on ssh-agent being installed and having the required AWS permissions.

	```sh 
	source ./authenticate.sh
	```


5. **Leverage Dynamic Inventory and Configure Machines**

	Configure the machines.

   ```sh
   ansible-playbook -i inventory/muhinventory.py site.yml
   ```


7. **Fetch ALB DNS Name and Public IP**

    Use the following AWS CLI command to fetch the DNS name and public IP of the ALB to test the new site:

    The virtual servers do not accept http/s traffic directly.

    ```sh
    aws elbv2 describe-load-balancers --query "LoadBalancers[*].[DNSName, LoadBalancerArn]" --output text
    aws elbv2 describe-load-balancers --query "LoadBalancers[*].[DNSName, Scheme, VpcId, State.Code, AvailabilityZones[*].LoadBalancerAddresses[*].IpAddress]" --output text
    ```

## To-Do: Further Hardening

1. **Install and Configure Fail2Ban**
   - Protect against brute-force attacks for SSH and Apache.

2. **Enable Host Firewall**
   - Restrict inbound and outbound traffic with `iptables` or something similar
   - Host level firewall is probably overkill considering we have a stateful firewall in form of security group 
 
3. **Implement Multi-Factor Authentication (MFA)**
   - Enable MFA for SSH access.

5. **Disable Unused Services**
   - Identify and disable unnecessary services.

6. **Further SSH Configuration**
    - Change default SSH port and use strong ciphers.
    - Disable SSH protocol 1.

7. **Implement Intrusion Detection System (IDS)**
    - Install and configure an IDS like `AIDE` or `OSSEC`.

8. **Enforce Encrypted EBS Drive**

9. **Restrict Apache Further**
    - Dissalow anything thats not a head/get request is thats all we are serving ( probably better further out along network perim ) 


