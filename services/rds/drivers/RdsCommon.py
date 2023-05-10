import boto3

import time
import datetime

from utils.Config import Config
from utils.Tools import _pr
from utils.Tools import aws_parseInstanceFamily
from utils.Tools import _warn
from services.Evaluator import Evaluator

class RdsCommon(Evaluator):
    def __init__(self, db, rdsClient):
        self.dbParams = {}
        self.results = {}
        self.db = db
        self.rdsClient = rdsClient
        self.__configPrefix = 'rds::' + db['Engine'] + '::' + db['EngineVersion'] + '::'
        self.init()
        self.loadParameterInfo()
        
    def showInfo(self):
        print("Identifier: " + self.db['DBInstanceIdentifier'] + "\n")
        _pr(self.results)
        
    def loadParameterInfo(self):
        arr = {}
        paramGroupName = self.db['DBParameterGroups'][0]['DBParameterGroupName']
        results = self.rdsClient.describe_db_parameters(
            DBParameterGroupName = paramGroupName
        )

        for param in results.get('Parameters'):
            
            if param['IsModifiable'] == 1 and 'ParameterValue' in param:
                arr[param['ParameterName']] = param['ParameterValue']
        
        while results.get('Marker') is not None:
            results = self.rdsClient.describe_db_parameters(
                DBParameterGroupName = paramGroupName,
                Marker = results.get('Marker')
            )

            for param in results.get('Parameters'):
                #__pr(param['ParameterName'] + ' = ' + param['ParameterValue'] + ' || ' + param['IsModifiable'])
                if param['IsModifiable'] == 1 and 'ParameterValue' in param:
                    arr[param['ParameterName']] = param['ParameterValue']
        
        self.dbParams = arr
        del arr

    ##Common Logic Belows
    ##All checks start from __check;
    
    def _checkHasMultiAZ(self):
        multiAZ = -1 if self.db['MultiAZ'] == False else 1
        self.results['MultiAZ'] = [multiAZ, 'Off' if multiAZ == -1 else 'On']
    
    def _checkAutoMinorVersionUpgrade(self):
        flag = -1 if self.db['AutoMinorVersionUpgrade'] == False else 1
        self.results['AutoMinorVersionUpgrade'] = [flag, 'Off' if flag == -1 else 'On']
    
    def _checkHasStorageEncrypted(self):
        flag = -1 if self.db['StorageEncrypted'] == False else 1
        self.results['StorageEncrypted'] = [flag, 'Off' if flag == -1 else 'On']
    
    def _checkHasPerformanceInsightsEnabled(self):
        flag = -1 if self.db['PerformanceInsightsEnabled'] == False else 1
        self.results['PerformanceInsightsEnabled'] = [flag, 'Off' if flag == -1 else 'On']
        
    def _checkHasBackup(self):
        backupDay = self.db['BackupRetentionPeriod']
        if backupDay == 0:
            self.results['Backup'] = -1
        elif backupDay < 7:
            self.results['BackupTooLow'] = -1
            
        if backupDay < 7:
            self.results['Backup'] = [-1, backupDay]

    def _checkIsUsingDefaultParameterGroups(self):
        params = self.db['DBParameterGroups']
        for param in params:
            if 'default.' in param['DBParameterGroupName']:
                self.results['DefaultParams'] = [-1, param['DBParameterGroupName']]

    def _checkHasEnhancedMonitoring(self):
        flag = 1 if 'EnhancedMonitoringResourceArn' in self.db else -1
        self.results['EnhancedMonitor'] = [flag, 'On' if flag == -1 else 'Off']

    def _checkDeleteProtection(self):
        flag = -1 if self.db['DeletionProtection'] == False else 1
        self.results['DeleteProtection'] = [flag, 'Off' if flag == -1 else 'On']

    def _checkIsPublicAccessible(self):
        flag = -1 if self.db['PubliclyAccessible'] == True else 1
        self.results['PubliclyAccessible'] = [flag, 'Off' if flag == -1 else 'On']

    def _checkSubnet3Az(self):
        subnets = self.db['DBSubnetGroup']['Subnets']
        
        subnetName = []
        for subnet in subnets:
            subnetName.append(subnet['SubnetAvailabilityZone']['Name'])
        
        flag = 1
        if len(subnets) < 3:
            flag = -1
            
        self.results['Subnets3Az'] = [flag, ', '.join(subnetName)]
        
    def _checkIsInstanceLatestGeneration(self):
        key = self.__configPrefix + 'orderableInstanceType'
        instTypes = Config.get(key, [])
        
        if not instTypes:
            try:
                results = self.rdsClient.describe_orderable_db_instance_options(
                    # DBInstanceClass = self.db['DBInstanceClass'],
                    Engine = self.db['Engine'],
                    EngineVersion = self.db['EngineVersion'],
                    MaxRecords = 20
                )
                
                arr = []
                for instClass in results.get('OrderableDBInstanceOptions'):
                    arr.append(instClass['DBInstanceClass'])
                
                while results.get('Marker') is not None:
                    results = self.rdsClient.describe_orderable_db_instance_options(
                        Engine = self.db['Engine'],
                        EngineVersion = self.db['EngineVersion'],
                        Marker = results.get('Marker')
                    )
                    
                    for instClass in results.get('OrderableDBInstanceOptions'):
                        arr.append(instClass['DBInstanceClass'])
                
                instTypes = list(set(arr))
                Config.set(key, instTypes)
                
                compressedLists = {}
                for instType in instTypes:
                    temp = instType.split('.')
                    compressedLists[temp[1][0]] = temp[1][1]
                
                Config.set(key + '::zip', compressedLists)
            except self.rdsClient.exceptions as e:
                _warn("Unable to identify potential latest engine version")
                if e.getAwsErrorCode() == 'InvalidParameterCombination':
                    self.results['LatestInstanceGeneration'] = [-1, '**DEPRECIATED**' + self.db['DBInstanceClass']]
                self.results['LatestInstanceGeneration'] = [-1, '_ERROR_']
                return
        else:
            compressedLists = Config.get(key + '::zip')
            
        dbInstClass = self.db['DBInstanceClass'].split('.')
        instInfo = aws_parseInstanceFamily(self.db['DBInstanceClass'])
        dbInstFamily = instInfo['prefixDetail']['family']
        dbInstGeneration = instInfo['prefixDetail']['version']
        
        if dbInstFamily == 't':
            self.results['BurstableInstance'] = [-1, self.db['DBInstanceClass']]   
        
        if compressedLists[dbInstFamily] > dbInstGeneration:
            self.results['LatestInstanceGeneration'] = [-1, self.db['DBInstanceClass']]
    
    
    def _checkHasPatches(self):
        engine = self.db['Engine']
        engineVersion = self.db['EngineVersion']
        
        key = self.__configPrefix + 'engineVersions'
        version = Config.get(key, [])
        details = {}
        
        if not details:
            versions = self.rdsClient.describe_db_engine_versions(
                Engine=engine,
                EngineVersion=engineVersion
            )
            version = versions.get('DBEngineVersions')
            if not version:
                self.results['EngineVersionMinor'] = [-1, "**DEPRECIATED**"]
                self.results['EngineVersionMajor'] = [-1, "**DEPRECIATED**"]
                return
            details = version[0]
            Config.set(key, details)
        
        upgrades = details['ValidUpgradeTarget']
        if not upgrades:
            self.results['EngineVersion'] = [1, engineVersion]
            return
        
        if upgrades[0]['IsMajorVersionUpgrade'] == False:
            self.results['EngineVersionMinor'] = [-1, engineVersion]
        
        lastInfo = upgrades[-1]
        if lastInfo['IsMajorVersionUpgrade'] == True:
            self.results['EngineVersionMajor'] = [-1, engineVersion]
       
def _checkClusterSize(self):
    cluster = self.db.get('DBClusterIdentifier', None)
    if not cluster:
        return
    
    resp = self.rdsClient.describe_db_clusters(
        DBClusterIdentifier=cluster
    )
    
    clusters = resp.get('DBClusters')
    if len(clusters) < 2 or len(clusters) > 7:
        self.results['Aurora__ClusterSize'] = [-1, len(clusters)]
        
def _checkOldSnapshots(self):
    if self.db.get('DBClusterIdentifier'):
        identifier = self.db['DBClusterIdentifier']
        result = self.rdsClient.describe_db_cluster_snapshots(
            DBClusterIdentifier=identifier,
            SnapshotType='manual'
        )
        
        snapshots = result.get('DBClusterSnapshots')
        while result.get('Marker') is not None:
            result = self.rdsClient.describe_db_cluster_snapshots(
                DBClusterIdentifier=identifier,
                SnapshotType='manual',
                Marker=result.get('Marker')
            )
            
            snapshots = snapshots + result.get('DBSnapshots')
    else:
        identifier = self.db['DBInstanceIdentifier']
        result = self.rdsClient.describe_db_snapshots(
            DBInstanceIdentifier=identifier,
            SnapshotType='manual'
        )
        
        snapshots = result.get('DBSnapshots')
        while result.get('Marker') is not None:
            result = self.rdsClient.describe_db_snapshots(
                DBInstanceIdentifier=identifier,
                SnapshotType='manual',
                Marker=result.get('Marker')
            )
            
            snapshots = snapshots + result.get('DBSnapshots')
    
        if not snapshots:
            return
            
        oldest_copy = snapshots[-1]
        
        oldest_copy_date = oldest_copy['SnapshotCreateTime']
        
        now = datetime.datetime.now().date()
        
        diff = now - oldest_copy_date
        days = diff.days
        
        if len(snapshots) > 5:
            self.results['SnapshotTooMany'] = [-1, len(snapshots)]
    
    if days > 180:
        self.results['SnapshotTooOld'] = [-1, days]
        

def check_free_storage(self):
    cw_client = boto3.client('cloudwatch')

    if not self.db['DBClusterIdentifier']:
        # Aurora Volume auto increase until 128TB as of 23/Sep/2021
        return
    else:
        metric = 'FreeStorageSpace'
        dimensions = [
            {
                'Name': 'DBInstanceIdentifier',
                'Value': self.db['DBInstanceIdentifier']
            }
        ]

    results = cw_client.get_metric_statistics(
        Dimensions=dimensions,
        Namespace='AWS/RDS',
        MetricName=metric,
        StartTime=int(time.time()) - 300,
        EndTime=int(time.time()),
        Period=300,
        Statistics=['Average']
    )

    GBYTES = 1024 * 1024 * 1024
    dp = results['Datapoints']
    freesize = round(dp[0]['Average'] / GBYTES, 4)

    ratio = freesize / self.db['AllocatedStorage']
    if ratio < 0.2:
        self.results['FreeStorage20pct'] = [-1, str(ratio * 100) + ' / ' + str(freesize) + '(GB)']