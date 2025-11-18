import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.route53.drivers.Route53HostedZone import Route53HostedZone

class Route53(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.route53Client = ssBoto.client('route53', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.route53Client.list_hosted_zones()
            arr = results.get('HostedZones', [])
            
            # Handle pagination
            while results.get('IsTruncated'):
                results = self.route53Client.list_hosted_zones(
                    Marker=results.get('NextMarker')
                )
                arr.extend(results.get('HostedZones', []))
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDenied', 'Throttling']:
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        hosted_zones = self.getResources()
        for zone in hosted_zones:
            zone_name = zone.get('Name', 'Unknown').rstrip('.')
            print('... (Route53) inspecting ' + zone_name)
            obj = Route53HostedZone(zone, self.route53Client)
            obj.run(self.__class__)
            objs[f"Route53::{zone_name}"] = obj.getInfo()
            del obj
        
        return objs