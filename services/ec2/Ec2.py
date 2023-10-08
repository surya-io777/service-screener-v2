# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_instances.html

import boto3
import botocore

import json
import time

from utils.Config import Config
from services.Service import Service
from services.ec2.drivers.Ec2Instance import Ec2Instance
from services.ec2.drivers.Ec2CompOpt import Ec2CompOpt
from services.ec2.drivers.Ec2EbsVolume import Ec2EbsVolume
from services.ec2.drivers.Ec2SecGroup import Ec2SecGroup
from services.ec2.drivers.Ec2CostExplorerRecs import Ec2CostExplorerRecs
from services.ec2.drivers.Ec2EIP import Ec2EIP
from services.ec2.drivers.Ec2ElbCommon import Ec2ElbCommon
from services.ec2.drivers.Ec2ElbClassic import Ec2ElbClassic
from services.ec2.drivers.Ec2AutoScaling import Ec2AutoScaling

class Ec2(Service):
    def __init__(self, region):
        super().__init__(region)
        self.ec2Client = boto3.client('ec2', config=self.bConfig)
        self.ssmClient = boto3.client('ssm', config=self.bConfig)
        self.compOptClient = boto3.client('compute-optimizer', config=self.bConfig)
        self.ceClient = boto3.client('ce', config=self.bConfig)
        self.elbClient = boto3.client('elbv2', config=self.bConfig)
        self.elbClassicClient = boto3.client('elb', config=self.bConfig)
        self.asgClient = boto3.client('autoscaling', config=self.bConfig)
        self.wafv2Client = boto3.client('wafv2', config=self.bConfig)
    
    # get EC2 Instance resources
    def getResources(self):
        filters = []
        if self.tags:
            filters = self.tags
                
        results = self.ec2Client.describe_instances(
            Filters = filters
        )
        
            
        arr = results.get('Reservations')
        while results.get('NextToken') is not None:
            results = self.ec2Client.describe_instances(
                Filters = filters,
                NextToken = results.get('NextToken')
            )    
            arr = arr + results.get('Reservations')

        return arr
    
    def getEC2SecurityGroups(self,instance):
        if 'SecurityGroups' not in instance:
            print(f"Security Group not found in {instance['InstanceId']}")
            return {}
        
        arr = []    
        filters = []
        groupIds = []
        if self.tags:
            filters = self.tags
        
        for group in instance['SecurityGroups']:
            groupIds.append(group['GroupId'])
        
        results = self.ec2Client.describe_security_groups(
            GroupIds=groupIds,
            Filters=filters
        )
        arr = results.get('SecurityGroups')
        
        while results.get('NextToken') is not None:
            results = self.ec2Client.describe_security_groups(
                GroupIds = groupIds,
                Filters=filters,
                NextToken = results.get('NextToken')
                )
            arr = arr + results.get('SecurityGroups')
        
        return arr
    
    def getEBSResources(self):
        filters = []
        
        if self.tags:
            filters = self.tags
        
        results = self.ec2Client.describe_volumes(
            Filters = filters
        )
        
        arr = results.get('Volumes')
        while results.get('NextToken') is not None:
            results = self.ec2Client.describe_volumes(
                Filters = filters,
                NextToken = results.get('NextToken')
            )    
            arr = arr + results.get('Reservations')

        return arr
        
    def getELB(self):
        results = self.elbClient.describe_load_balancers()
        
        arr = results.get('LoadBalancers')
        while results.get('NextMarker') is not None:
            results = self.elbClient.describe_load_balancers(
                Marker = results.get('NextMarker')
            )
            arr = arr + results.get('LoadBalancers')
            
        ## TO DO: support tagging later
        
        # if self.tags is None:
        #     return arr
        
        # filteredResults = []
        # for lb in arr:
        #     tagResults = self.elbClient.describe_tags(
        #         ResourceArns = [lb['LoadBalancerArn']]
        #     )
        #     tagDesc = tagResults.get('TagDescriptions')
        #     if len(tagDesc) > 0:
        #         for desc in tagDesc:
        #             if self.resourceHasTags(desc['Tags']):
        #                 filteredResults.append(lb)
        #                 break
                    
        # return filteredResults
        
        return arr
        
    def getELBClassic(self):
        results = self.elbClassicClient.describe_load_balancers()
        
        arr = results.get('LoadBalancerDescriptions')
        while results.get('NextMarker') is not None:
            results = self.elbClient.describe_load_balancers(
                Marker = results.get('NextMarker')
            )
            
            arr = arr + results.get('LoadBalancerDescriptions')
            
        return arr
        
    def getELBSecurityGroup(self, elb):
        if 'SecurityGroups' not in elb:
            return []
        
        securityGroups = elb['SecurityGroups']
        groupIds = []
        arr = []
        for groupId in securityGroups:
            groupIds.append(groupId)
            
        if len(groupIds) == 0:
            return arr
        
        filters = []  
        if self.tags is not None:
            filters = self.tags
            
        results = self.ec2Client.describe_security_groups(
            GroupIds = groupIds,
            Filters = filters
        )
        
        arr = results.get('SecurityGroups')
        while results.get('NextToken') is not None:
            results = self.ec2Client.describe_security_groups(
                GroupIds = groupIds,
                Filters = filters,
                NextToken = results.get('NextToken')
            )
            arr = arr + results.get('SecurityGroups')
            
        return arr
        
    def getASGResources(self):
        filters = []
        if self.tags:
            filters = self.tags
        
        results = self.asgClient.describe_auto_scaling_groups(
            Filters = filters
        )
        arr = results.get('AutoScalingGroups')
        while results.get('NextToken') is not None:
            results = self.asgClient.describe_auto_scaling_groups(
                Filters = filters,
                NextToken = results.get('NextToken')
            )
            
            arr = arr + results.get('AutoScalingGroups')
        
        return arr
        
    def getEIPResources(self):
        filters = []
        if self.tags:
            filters = self.tags
            
        result = self.ec2Client.describe_addresses(
            Filters = filters    
        )
        arr = result.get('Addresses')
        
        return arr
        
    def getDefaultSG(self):
        defaultSGs = {}
        result = self.ec2Client.describe_security_groups()
        for group in result.get('SecurityGroups'):
            if group.get('GroupName') == 'default':
                defaultSGs[group.get('GroupId')] = group
                
        while result.get('NextToken') is not None:
            result = self.ec2Client.describe_security_groups(
                NextToken = result.get('NextToken')
            )
            for group in result.get('SecurityGroups'):
                if group.get('GroupName') == 'default':
                    defaultSGs[group.get('GroupId')] = group
        
        return defaultSGs
    
    def advise(self):
        objs = {}
        secGroups = {}
        
        # compute optimizer checks
        hasRunComputeOpt = Config.get('EC2_HasRunComputeOpt', False)
        if hasRunComputeOpt == False:
            try:
                compOptPath = "/aws/service/global-infrastructure/regions/" + self.region + "/services/compute-optimizer";
                compOptCheck = self.ssmClient.get_parameters_by_path(
                    Path = compOptPath    
                )
                
                if 'Parameters' in compOptCheck and len(compOptCheck['Parameters']) > 0:
                    print('... (Compute Optimizer Recommendations) inspecting')
                    obj = Ec2CompOpt(self.compOptClient)
                    obj.run()
                    objs['ComputeOptimizer'] = obj.getInfo()
                    Config.set('EC2_HasRunComputeOpt', True)
                    
            except botocore.exceptions.ClientError as e:
                ecode = e.response['Error']['Code']
                emsg = e.response['Error']['Message']
                print(ecode, emsg)     
            except Exception as e:
                print(e)
                print("!!! Skipping compute optimizer check for <" + self.region + ">")
            
        
        #EC2 Cost Explorer checks
        hasRunRISP = Config.get('EC2_HasRunRISP', False)
        if hasRunRISP == False:
            print('... (Cost Explorer Recommendations) inspecting')
            obj = Ec2CostExplorerRecs(self.ceClient)
            obj.run()
    
            objs['CostExplorer'] = obj.getInfo()
            Config.set('EC2_HasRunRISP', True)
        
        
        # EC2 instance checks
        instances = self.getResources()
        for instance in instances:
            instanceData = instance['Instances'][0]
            print('... (EC2) inspecting ' + instanceData['InstanceId'])
            obj = Ec2Instance(instanceData,self.ec2Client)
            obj.run()
            
            objs[f"EC2::{instanceData['InstanceId']}"] = obj.getInfo()
            
            ## Gather SecGroups in dict first to prevent check same sec groups multiple time
            instanceSG = self.getEC2SecurityGroups(instanceData)
            for group in instanceSG:
                secGroups[group['GroupId']] = group
            
        
        #EBS checks
        volumes = self.getEBSResources()
        for volume in volumes:
            print('... (EBS) inspecting ' + volume['VolumeId'])
            obj = Ec2EbsVolume(volume,self.ec2Client)
            obj.run()
            objs[f"EBS::{volume['VolumeId']}"] = obj.getInfo()
            
        # ELB checks
        loadBalancers = self.getELB()
        for lb in loadBalancers:
            print(f"... (ELB::Load Balancer) inspecting {lb['LoadBalancerName']}")
            obj = Ec2ElbCommon(lb, self.elbClient, self.wafv2Client)
            obj.run()
            objs[f"ELB::{lb['LoadBalancerName']}"] = obj.getInfo()
            
            
            elbSGList = self.getELBSecurityGroup(lb)
            for group in elbSGList:
                secGroups[group['GroupId']] = group
        
        # ELB classic checks
        lbClassic = self.getELBClassic()
        for lb in lbClassic:
            print(f"... (ELB::Load Balancer Classic) inspecting {lb['LoadBalancerName']}")
            obj = Ec2ElbClassic(lb, self.elbClassicClient)
            obj.run()
            objs[f"ELB Classic::{lb['LoadBalancerName']}"] = obj.getInfo()
            
            elbSGList = self.getELBSecurityGroup(lb)
            for group in elbSGList:
                secGroups[group['GroupId']] = group
        
        # ASG checks
        autoScalingGroups = self.getASGResources()
        for group in autoScalingGroups:
            print(f"... (ASG::Auto Scaling Group) inspecting {group['AutoScalingGroupName']}");
            obj = Ec2AutoScaling(group, self.asgClient, self.elbClient, self.elbClassicClient, self.ec2Client)
            obj.run()
            objs[f"ASG::{group['AutoScalingGroupName']}"] = obj.getInfo()
        
        defaultSGs = self.getDefaultSG()
        for groupId in defaultSGs.keys():
            if groupId not in secGroups:
                secGroups[groupId] = defaultSGs[groupId]
                secGroups[groupId]['inUsed'] = 'False'
            
        # SG checks
        for group in secGroups.values():
            print(f"... (EC2::Security Group) inspecting {group['GroupId']}")
            obj = Ec2SecGroup(group, self.ec2Client)
            obj.run()
            
            objs[f"SG::{group['GroupId']}"] = obj.getInfo()
        
        # EIP checks    
        print('... (Elastic IP Recommendations) inspecting')
        eips = self.getEIPResources()
        for eip in eips:
            obj = Ec2EIP(eip)
            obj.run()
            objs[f"ElasticIP::{eip['AllocationId']}"] = obj.getInfo()
        
        
        return objs