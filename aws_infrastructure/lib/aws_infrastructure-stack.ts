import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { InstanceTarget } from 'aws-cdk-lib/aws-elasticloadbalancingv2-targets';
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

export class AwsInfrastructureStack extends cdk.Stack {

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const keyPairName = 'ansible-challenge-keypair';
    const acmSecretName = 'AnsChallengeACMCertificateArn';

    // Create a VPC
    const vpc = new ec2.Vpc(this, 'MyVPC', {
      maxAzs: 2,
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'),
      subnetConfiguration: [
        {
          name: 'public',
          subnetType: ec2.SubnetType.PUBLIC,
        },
        {
          name: 'private',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
        }
      ]
    });

    const albSecurityGroup = new ec2.SecurityGroup(this, 'ALBSecurityGroup', {
      vpc,
      description: 'Allow HTTPS traffic from world',
      allowAllOutbound: true,
    });
    albSecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(443), 'allow HTTPS traffic');

    const ec2SecurityGroup = new ec2.SecurityGroup(this, 'EC2SecurityGroup', {
      vpc,
      description: 'Allow HTTP traffic from ALB and SSH from anywhere',
      allowAllOutbound: true,
    });
    ec2SecurityGroup.addIngressRule(albSecurityGroup, ec2.Port.tcp(80), 'allow HTTP traffic from ALB');
    ec2SecurityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'allow SSH access');

    const instanceType = ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO);
    const machineImage = ec2.MachineImage.latestAmazonLinux2();

    const ec2Instance1 = new ec2.Instance(this, 'Instance1', {
      instanceType,
      machineImage,
      vpc,
      securityGroup: ec2SecurityGroup,
      keyName: keyPairName,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
    });
    cdk.Tags.of(ec2Instance1).add('Name', 'ansible_vm1');

    const eip1 = new ec2.CfnEIP(this, 'EIP1', {
      instanceId: ec2Instance1.instanceId,
    });

    const ec2Instance2 = new ec2.Instance(this, 'Instance2', {
      instanceType,
      machineImage,
      vpc,
      securityGroup: ec2SecurityGroup,
      keyName: keyPairName,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
    });
    cdk.Tags.of(ec2Instance2).add('Name', 'ansible_vm2');

    const eip2 = new ec2.CfnEIP(this, 'EIP2', {
      instanceId: ec2Instance2.instanceId,
    });

    const secretsManagerClient = new SecretsManagerClient({ region: 'ap-southeast-2' });
    const getSecretValueCommand = new GetSecretValueCommand({ SecretId: acmSecretName });
    secretsManagerClient.send(getSecretValueCommand).then(data => {
      const certificateArn = data.SecretString;
      if (!certificateArn) {
        throw new Error('Certificate ARN is not defined in Secrets Manager');
      }

      const alb = new elbv2.ApplicationLoadBalancer(this, 'ALB', {
        vpc,
        internetFacing: true,
        securityGroup: albSecurityGroup,
      });

      const listener = alb.addListener('Listener', {
        port: 443,
        open: true,
        certificates: [{ certificateArn }],
      });

      const targetGroup = new elbv2.ApplicationTargetGroup(this, 'TargetGroup', {
        vpc,
        port: 80,
        targets: [
          new InstanceTarget(ec2Instance1),
          new InstanceTarget(ec2Instance2),
        ],
        healthCheck: {
          path: '/',
          interval: cdk.Duration.seconds(60),
        },
      });

      listener.addTargetGroups('TargetGroupAttachment', {
        targetGroups: [targetGroup],
      });

      new cdk.CfnOutput(this, 'ALBDNSName', {
        value: alb.loadBalancerDnsName,
        description: 'The DNS name of the ALB',
      });

    }).catch(err => {
      console.error('Error retrieving ACM ARN from Secrets Manager:', err);
      throw new Error('Error retrieving ACM ARN from Secrets Manager');
    });
  }
}
