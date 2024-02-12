from aws_cdk import Size, Stack
from aws_cdk import CfnOutput
from aws_cdk import aws_s3 as _s3
from aws_cdk import aws_ec2 as _vpc
from aws_cdk import aws_ec2 as _ec2
from aws_cdk import RemovalPolicy
import aws_cdk as core 
from constructs import Construct

key_name="aws-cdk"
class CdkVpcEc2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Creating S3 Bucket 
        # my_bucket = _s3.Bucket(self, id="MyFirstS3Bucket", 
        #                        bucket_name="devops-aws-cdk-s3-bucket", 
        #                        encryption=_s3.BucketEncryption.S3_MANAGED, 
        #                        versioned=True, 
        #                        public_read_access=True,
        #                        removal_policy=RemovalPolicy.DESTROY)
        
        # core.CfnOutput(self, "S3-Bucket-Name", value=my_bucket.bucket_name)
        # core.CfnOutput(self, "S3-Bucket-Arn", value=my_bucket.bucket_arn)
        # core.CfnOutput(self, "S3-Bucket-url", value=my_bucket.bucket_website_url)
        
        # Creating VPC    
        my_vpc = _vpc.Vpc(self,
                       self.node.try_get_context('Network')['logical_id'],
                       enable_dns_hostnames=True,
                       enable_dns_support=True,
                       nat_gateways=0,
                       cidr=self.node.try_get_context('Network')['vpc_cidr'],
    # 'IpAddresses' configures the IP range and size of the entire VPC.
    # The IP space will be divided based on configuration for the subnets.
                        # ip_addresses=_vpc.IpAddresses.cidr(self.node.try_get_context('Network')['vpc_cidr']),

    # 'maxAzs' configures the maximum number of availability zones to use.
    # If you want to specify the exact availability zones you want the VPC
    # to use, use `availabilityZones` instead.
                        max_azs=self.node.try_get_context('Network')['max_AZs'],

    # 'subnetConfiguration' specifies the "subnet groups" to create.
    # Every subnet group will have a subnet for each AZ, so this
    # configuration will create `3 groups × 3 AZs = 9` subnets.
                        subnet_configuration=[_vpc.SubnetConfiguration(
        # 'subnetType' controls Internet access, as described above.
                            subnet_type=_vpc.SubnetType.PUBLIC,

        # 'name' is used to name this particular subnet group. You will have to
        # use the name for subnet selection if you have more than one subnet
        # group of the same type.
                            name="Web",

        # 'cidrMask' specifies the IP addresses in the range of of individual
        # subnets in the group. Each of the subnets in this group will contain
        # `2^(32 address bits - 24 subnet bits) - 2 reserved addresses = 254`
        # usable IP addresses.
        #
        # If 'cidrMask' is left out the available address space is evenly
        # divided across the remaining subnet groups.
                            cidr_mask=self.node.try_get_context('Network')['cidr_mask']), 
                        
                        _vpc.SubnetConfiguration(
                            cidr_mask=self.node.try_get_context('Network')['cidr_mask'],
                            name="Application",
                            subnet_type=_vpc.SubnetType.PRIVATE_ISOLATED), 
                        
                        _vpc.SubnetConfiguration(
                            cidr_mask=self.node.try_get_context('Network')['cidr_mask'],
                            name="Database",
                            subnet_type=_vpc.SubnetType.PRIVATE_ISOLATED)])
        
        # Amazon Linux 2
        my_instance=_ec2.Instance(self, "Instance",
                     vpc=my_vpc,
                     instance_name="AWS-CDK-Host",
                     instance_type=_ec2.InstanceType.of(_ec2.InstanceClass.T2, _ec2.InstanceSize.MEDIUM),
                     key_name=key_name,
                     machine_image=_ec2.MachineImage.latest_amazon_linux2(),
                     vpc_subnets=_ec2.SubnetSelection(subnet_type=_ec2.SubnetType.PUBLIC),
                     user_data_causes_replacement=True)
        
        volume = _ec2.Volume(self, "Volume",
                            availability_zone="us-east-2a",
                            size=Size.gibibytes(10),
                            # volume_type="gp3",
                            # delete_on_termination=False,
                            # iops=3000,
                            # throughput=125,
                            encrypted=True,
                            removal_policy=RemovalPolicy.DESTROY)
        
        _ec2.CfnVolumeAttachment(self, "MyCfnVolumeAttachment",
                                 instance_id=my_instance.instance_id,
                                 volume_id=volume.volume_id,
                                 # the properties below are optional
                                 device="/dev/xvdb")
        
        # Attaching Elastic IP with the Instance         
        _ec2.CfnEIP(self, "myEIP", instance_id=my_instance.instance_id)
        
        # Installing packages at instance launch
        _ec2.UserData.add_commands('yum update -y',
                                   'yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm',
                                   'amazon-linux-extras install nginx1',
                                   'service nginx start')
        
        core.CfnOutput(self, 'WebServerDnsName',
                  value=my_instance.instance_public_dns_name)
        
        # Allowing connections to the web server
        my_instance.connections.allow_from_any_ipv4(_ec2.Port.tcp(22), "Allow ssh from internet")
        my_instance.connections.allow_from_any_ipv4(_ec2.Port.tcp(80), "Allow http from internet")
        my_instance.connections.allow_from_any_ipv4(_ec2.Port.icmp_ping(), "Allow ping from internet")
