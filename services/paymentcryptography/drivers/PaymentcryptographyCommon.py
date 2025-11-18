import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class PaymentcryptographyCommon(Evaluator):
    def __init__(self, key, paymentCryptoClient):
        super().__init__()
        self.init()
        self.key = key
        self.paymentCryptoClient = paymentCryptoClient
        self._resourceName = key.get('KeyArn', 'Account').split('/')[-1] if key else 'Account'
        
    def _checkKeyRotation(self):
        if not self.key:
            return
            
        try:
            key_arn = self.key.get('KeyArn')
            response = self.paymentCryptoClient.get_key(KeyIdentifier=key_arn)
            
            key_details = response.get('Key', {})
            key_state = key_details.get('KeyState')
            
            if key_state != 'CREATE_COMPLETE':
                self.results['KeyState'] = [-1, f"Key is in {key_state} state"]
                
            # Check key usage
            usage_restrictions = key_details.get('KeyUsage')
            if not usage_restrictions:
                self.results['KeyUsage'] = [-1, "Key usage restrictions not properly defined"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['KeyRotationCheck'] = [-1, f"Unable to check key details: {str(e)}"]
    
    def _checkKeyAccess(self):
        if not self.key:
            return
            
        try:
            key_arn = self.key.get('KeyArn')
            
            # Check if key has proper access controls
            response = self.paymentCryptoClient.list_aliases()
            aliases = response.get('Aliases', [])
            
            key_aliases = [a for a in aliases if a.get('KeyArn') == key_arn]
            if not key_aliases:
                self.results['KeyAlias'] = [-1, "Key does not have an alias for easier management"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['KeyAccessCheck'] = [-1, f"Unable to check key access: {str(e)}"]
    
    def _checkServiceEnabled(self):
        if self.key:
            return  # Service is enabled if keys exist
            
        try:
            # Try to list keys to check if service is accessible
            response = self.paymentCryptoClient.list_keys(MaxResults=1)
            # If we get here without error, service is enabled but no keys exist
            
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                self.results['ServiceEnabled'] = [-1, "Payment Cryptography service is not enabled or accessible"]
            else:
                self.results['ServiceEnabledCheck'] = [-1, f"Unable to check service status: {str(e)}"]