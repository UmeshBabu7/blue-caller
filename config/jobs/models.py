from django.db import models
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField

User=get_user_model()

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()

class Worker(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workers')  # Changed to ForeignKey
    name = models.CharField(max_length=50)
    phone_number = PhoneNumberField(region="NP", unique=True)
    tagline = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to="profiles/", blank=True)
    verified = models.BooleanField(default=False)
    citizenship_image = models.ImageField(upload_to='citizenship/', blank=True, null=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    latitude = models.CharField(max_length=20, null=True, blank=True)
    longitude = models.CharField(max_length=20, null=True, blank=True)
    appointed = models.BooleanField(default=False)
    appointment_date = models.DateTimeField(null=True, blank=True)

    def average_rating(self):
        from django.db.models import Avg
        average = WorkerRating.objects.filter(appointment__worker=self).aggregate(Avg('rating'))['rating__avg']
        return round(average, 1) if average else 0

    def __str__(self):
        return f"{self.id} | {self.name}"

class Customer(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers')  # Changed to ForeignKey
    name = models.CharField(max_length=50)
    phone_number = PhoneNumberField(region="NP", unique=True)
    profile_pic = models.ImageField(upload_to="profiles/", blank=True)
    latitude = models.CharField(max_length=20, null=True, blank=True)
    longitude = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.id} | {self.name}"


    

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_appointments')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='worker_appointments')
    appointment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Appointment with {self.worker} on {self.appointment_date}"
    
class WorkerRating(models.Model):
    worker = models.ForeignKey(Worker,on_delete=models.CASCADE)
    appointment = models.ManyToManyField(Appointment, related_name='ratings')
    rating = models.PositiveSmallIntegerField()  # Rating between 1 and 5
    created_at = models.DateTimeField(auto_now_add=True)
    average_rating = models.FloatField(default=0.0)

#This is a check for merge 