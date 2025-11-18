import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.paymentcryptography.drivers.PaymentcryptographyCommon import PaymentcryptographyCommon

class Paymentcryptography(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.paymentCryptoClient = ssBoto.client('payment-cryptography', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.paymentCryptoClient.list_keys()
            arr = results.get('Keys', [])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException', 'UnauthorizedOperation']:
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        keys = self.getResources()
        if not keys:
            # Create a placeholder for account-level checks
            obj = PaymentcryptographyCommon({}, self.paymentCryptoClient)
            obj.run(self.__class__)
            objs['PaymentCrypto::Account'] = obj.getInfo()
            del obj
        else:
            for key in keys:
                key_id = key.get('KeyArn', 'Unknown').split('/')[-1]
                print('... (PaymentCryptography) inspecting ' + key_id)
                obj = PaymentcryptographyCommon(key, self.paymentCryptoClient)
                obj.run(self.__class__)
                objs[f"PaymentCrypto::{key_id}"] = obj.getInfo()
                del obj
        
        return objs