import boto3
import botocore

from utils.Config import Config
from utils.Tools import _pr
from services.Service import Service
##import drivers here
from services.rds.drivers.RdsCommon import RdsCommon
from services.rds.drivers.RdsMysql import RdsMysql
from services.rds.drivers.RdsMysqlAurora import RdsMysqlAurora
from services.rds.drivers.RdsPostgres import RdsPostgres
from services.rds.drivers.RdsPostgresAurora import RdsPostgresAurora
from services.rds.drivers.RdsMssql import RdsMssql
from services.rds.drivers.SecretsManager import SecretsManager
from services.rds.drivers.SecretsVsDB import SecretsVsDB
from services.rds.drivers.RdsSecurityGroup import RdsSecurityGroup

class Rds(Service):
    def __init__(self, region):
        super().__init__(region)
        self.rdsClient = boto3.client('rds', config=self.bConfig)
        self.ec2Client = boto3.client('ec2', config=self.bConfig)
        self.ctClient = boto3.client('cloudtrail', config=self.bConfig)
        self.smClient = boto3.client('secretsmanager', config=self.bConfig)
        self.cwClient = boto3.client('cloudwatch', config=self.bConfig)
        
        self.secrets = []

    engineDriver = {
        'mysql': 'Mysql',
        'aurora-mysql': 'MysqlAurora',
        'postgres': 'Postgres',
        'aurora-postgresql': 'PostgresAurora',
        'sqlserver': 'Mssql'
    }
    
    def getResources(self):
        results = self.rdsClient.describe_db_instances()
        
        arr = results.get('DBInstances')
        while results.get('Maker') is not None:
            results = self.rdsClient.describe_db_instances(
                Maker = results.get('Maker')
            )
            arr = arr + results.get('DBInstances')
        
        if not self.tags:
            return arr
        
        finalArr = []
        for i, detail in enumerate(arr):
            if self.resourceHasTags(detail['TagList']):
                finalArr.append(arr[i])
        
        return finalArr    
    
    def getSecrets(self):
        results = self.smClient.list_secrets(IncludePlannedDeletion=False, MaxResults=10)
        self.registerSecrets(results)
        NextToken = results.get('NextToken')
        while NextToken != None:
            results = self.smClient.list_secrets(IncludePlannedDeletion=False, MaxResults=10, NextToken=NextToken)
            NextToken = results.get('NextToken')
            
            self.registerSecrets(results)
            
    def registerSecrets(self, results):
        for secret in results.get('SecretList'):
            resp = self.smClient.describe_secret(SecretId=secret['ARN'])
            self.secrets.append(resp)
        
    def advise(self):
        objs = {}
        instances = self.getResources()
        securityGroupArr = {}
        
        for instance in instances:
            print('... (RDS) inspecting ' + instance['DBInstanceIdentifier'])
            
            if 'VpcSecurityGroups' in instance:
                for sg in instance['VpcSecurityGroups']:
                    if 'Status' in sg and (sg['Status'] == 'active' or sg['Status'] == 'adding'):
                        if sg['VpcSecurityGroupId'] in securityGroupArr:
                            securityGroupArr[sg['VpcSecurityGroupId']].append(instance['DBInstanceIdentifier'])
                        else:
                            securityGroupArr[sg['VpcSecurityGroupId']] = [instance['DBInstanceIdentifier']]
                
            engine = instance['Engine']
            
            # grouping mssql versions together
            if engine.find('sqlserver') != -1:
                engine = 'sqlserver'
                
            if engine not in self.engineDriver:
                continue
            
            driver_ = self.engineDriver[engine]
            driver = 'Rds' + driver_
            if driver in globals():
                obj = globals()[driver](instance, self.rdsClient, self.ctClient, self.cwClient)
                obj.setEngine(engine)
                obj.run(self.__class__)
                
                objs[instance['Engine'] + '::' + instance['DBInstanceIdentifier']] = obj.getInfo()
                del obj
        
        for sg, rdsList in securityGroupArr.items():
            print('... (RDS-SG) inspecting ' + sg)
            obj = RdsSecurityGroup(sg, self.ec2Client, rdsList)
            obj.run(self.__class__)
            objs['RDS_SG::' + sg] = obj.getInfo()
            del obj

        self.getSecrets()
        for secret in self.secrets:
            print('... (SecretsManager) inspecting ' + secret['Name'])
            obj = SecretsManager(secret, self.smClient, self.ctClient)
            obj.run(self.__class__)
            
            objs['SecretsManager::'+ secret['Name']] = obj.getInfo()
            del obj
        
        obj = SecretsVsDB(len(self.secrets), len(instances))
        obj.run(self.__class__)
        objs['SecretsRDS::General'] = obj.getInfo()
        del obj
        
        return objs
    
if __name__ == "__main__":
    Config.init()
    o = Rds('ap-southeast-1')
    out = o.advise()