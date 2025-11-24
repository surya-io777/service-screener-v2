import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class Route53HostedZone(Evaluator):
    def __init__(self, hosted_zone, route53Client):
        super().__init__()
        self.init()
        self.hosted_zone = hosted_zone
        self.route53Client = route53Client
        self._resourceName = hosted_zone.get('Name', 'Unknown').rstrip('.')
        
    def _checkQueryLogging(self):
        try:
            zone_id = self.hosted_zone['Id'].split('/')[-1]
            response = self.route53Client.list_query_logging_configs(
                HostedZoneId=zone_id
            )
            
            configs = response.get('QueryLoggingConfigs', [])
            if not configs:
                self.results['QueryLogging'] = [-1, "Query logging is not enabled for this hosted zone"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDenied']:
                self.results['QueryLogging'] = [-1, f"Unable to check query logging: {str(e)}"]
    
    def _checkDNSSEC(self):
        try:
            zone_id = self.hosted_zone['Id'].split('/')[-1]
            response = self.route53Client.get_dnssec(HostedZoneId=zone_id)
            
            status = response.get('Status', {})
            if status.get('StatusMessage') != 'Signing DNSSEC with KSK':
                self.results['DNSSEC'] = [-1, "DNSSEC is not enabled for this hosted zone"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'DNSSECNotFound':
                self.results['DNSSEC'] = [-1, "DNSSEC is not enabled for this hosted zone"]
            elif e.response['Error']['Code'] not in ['AccessDenied']:
                self.results['DNSSEC'] = [-1, f"Unable to check DNSSEC: {str(e)}"]
    
    def _checkHealthChecks(self):
        try:
            zone_id = self.hosted_zone['Id'].split('/')[-1]
            
            # Get all records for the hosted zone
            response = self.route53Client.list_resource_record_sets(
                HostedZoneId=zone_id
            )
            
            record_sets = response.get('ResourceRecordSets', [])
            health_check_records = [r for r in record_sets if r.get('HealthCheckId')]
            
            if not health_check_records:
                # Check if there are any A or AAAA records that could benefit from health checks
                a_records = [r for r in record_sets if r.get('Type') in ['A', 'AAAA'] and r.get('Name') != self.hosted_zone['Name']]
                if a_records:
                    self.results['HealthChecks'] = [-1, "No health checks configured for DNS records"]
                    
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDenied']:
                self.results['HealthChecks'] = [-1, f"Unable to check health checks: {str(e)}"]
    
    def _checkPrivateZoneVPCs(self):
        if not self.hosted_zone.get('Config', {}).get('PrivateZone'):
            return  # Skip for public zones
            
        try:
            zone_id = self.hosted_zone['Id'].split('/')[-1]
            response = self.route53Client.get_hosted_zone(Id=zone_id)
            
            vpcs = response.get('VPCs', [])
            if len(vpcs) < 2:
                self.results['PrivateZoneVPCs'] = [-1, "Private hosted zone is associated with only one VPC"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDenied']:
                self.results['PrivateZoneVPCs'] = [-1, f"Unable to check VPC associations: {str(e)}"]