import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class SesCommon(Evaluator):
    def __init__(self, identity, sesClient):
        super().__init__()
        self.init()
        self.identity = identity
        self.sesClient = sesClient
        self._resourceName = identity.get('IdentityName', 'Account') if identity else 'Account'
        
    def _checkDKIMAuthentication(self):
        if not self.identity:
            return
            
        try:
            identity_name = self.identity.get('IdentityName')
            response = self.sesClient.get_email_identity(EmailIdentity=identity_name)
            
            dkim_attributes = response.get('DkimAttributes', {})
            if not dkim_attributes.get('SigningEnabled'):
                self.results['DKIMSigning'] = [-1, "DKIM signing is not enabled for this identity"]
                
            if dkim_attributes.get('Status') != 'SUCCESS':
                self.results['DKIMStatus'] = [-1, f"DKIM status is {dkim_attributes.get('Status')}"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['DKIMCheck'] = [-1, f"Unable to check DKIM: {str(e)}"]
    
    def _checkSPFRecord(self):
        if not self.identity:
            return
            
        try:
            identity_name = self.identity.get('IdentityName')
            
            # Check if it's a domain identity
            if '@' not in identity_name and '.' in identity_name:
                # This is likely a domain, check for SPF
                response = self.sesClient.get_email_identity(EmailIdentity=identity_name)
                
                # Note: SESv2 doesn't directly provide SPF record validation
                # This is a placeholder for SPF record checking logic
                mail_from_attributes = response.get('MailFromAttributes', {})
                if not mail_from_attributes.get('MailFromDomain'):
                    self.results['MailFromDomain'] = [-1, "Custom MAIL FROM domain is not configured"]
                    
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['SPFCheck'] = [-1, f"Unable to check SPF configuration: {str(e)}"]
    
    def _checkReputationTracking(self):
        try:
            response = self.sesClient.get_account_sending_enabled()
            if not response.get('Enabled'):
                self.results['SendingEnabled'] = [-1, "Account sending is disabled"]
                
            # Check reputation tracking
            response = self.sesClient.get_delivery_options()
            if not response.get('DeliveryOptions', {}).get('TlsPolicy') == 'Require':
                self.results['TLSPolicy'] = [-1, "TLS is not required for email delivery"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['ReputationCheck'] = [-1, f"Unable to check reputation settings: {str(e)}"]
    
    def _checkSandboxMode(self):
        try:
            response = self.sesClient.get_sending_quota()
            max_send_rate = response.get('MaxSendRate', 0)
            
            # If max send rate is very low (like 1), likely in sandbox
            if max_send_rate <= 1:
                self.results['SandboxMode'] = [-1, "SES account appears to be in sandbox mode with limited sending"]
                
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['SandboxCheck'] = [-1, f"Unable to check sandbox status: {str(e)}"]