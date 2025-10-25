# payment_utils.py - eSewa Payment Gateway Integration
import hashlib
import uuid
import requests
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class EsewaPayment:
    """
    eSewa Payment Gateway Integration
    """
    
    def __init__(self):
        # eSewa configuration - these should be in settings.py
        self.merchant_id = getattr(settings, 'ESEWA_MERCHANT_ID', 'EPAYTEST')
        self.secret_key = getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')
        self.success_url = getattr(settings, 'ESEWA_SUCCESS_URL', '')
        self.failure_url = getattr(settings, 'ESEWA_FAILURE_URL', '')
        self.base_url = getattr(settings, 'ESEWA_BASE_URL', 'https://uat.esewa.com.np')
        
    def generate_payment_request(self, amount, product_name, payment_request_id):
        """
        Generate payment request for eSewa
        """
        try:
            # Convert amount to string with 2 decimal places
            amount_str = f"{Decimal(str(amount)):.2f}"
            
            # Generate unique transaction ID
            transaction_id = str(uuid.uuid4())
            
            # Create the payment data
            payment_data = {
                'amt': amount_str,
                'pdc': 0,  # Product delivery charge
                'psc': 0,  # Product service charge
                'txAmt': 0,  # Tax amount
                'tAmt': amount_str,  # Total amount
                'pid': payment_request_id,  # Product ID (our payment request ID)
                'scd': self.merchant_id,  # Service code (merchant ID)
                'su': self.success_url,  # Success URL
                'fu': self.failure_url,  # Failure URL
            }
            
            # Generate signature
            signature_string = f"total_amount={amount_str},transaction_uuid={transaction_id},product_code={payment_request_id}"
            signature = hashlib.sha256(signature_string.encode()).hexdigest()
            
            return {
                'payment_data': payment_data,
                'transaction_id': transaction_id,
                'signature': signature,
                'payment_url': f"{self.base_url}/epay/main"
            }
            
        except Exception as e:
            logger.error(f"Error generating payment request: {e}")
            return None
    
    def verify_payment(self, payment_request_id, transaction_id, amount):
        """
        Verify payment with eSewa
        """
        try:
            # Create verification data
            verification_data = {
                'amt': str(amount),
                'rid': transaction_id,
                'pid': payment_request_id,
                'scd': self.merchant_id
            }
            
            # Make verification request to eSewa
            response = requests.post(
                f"{self.base_url}/epay/transrec",
                data=verification_data,
                timeout=30
            )
            
            if response.status_code == 200:
                # Parse response (eSewa returns XML)
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                # Check if payment is successful
                if root.find('response_code').text == 'Success':
                    return True, "Payment verified successfully"
                else:
                    return False, f"Payment verification failed: {root.find('response_message').text}"
            else:
                return False, f"Verification request failed with status {response.status_code}"
                
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False, f"Payment verification error: {str(e)}"

def calculate_payment_amounts(total_amount, initial_percentage=20):
    """
    Calculate initial and final payment amounts
    """
    initial_amount = (total_amount * Decimal(initial_percentage)) / 100
    final_amount = total_amount - initial_amount
    
    return {
        'initial_amount': initial_amount,
        'final_amount': final_amount,
        'total_amount': total_amount
    }

def create_payment_request_id():
    """
    Generate unique payment request ID
    """
    return f"PAY_{uuid.uuid4().hex[:12].upper()}"
