from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    pass

    def get_worker(self):
        if(hasattr(self,'worker')):
            return self.worker 
        return None
    
    def get_customer(self):
        if(hasattr(self,'customer')):
            return self.customer 
        return None