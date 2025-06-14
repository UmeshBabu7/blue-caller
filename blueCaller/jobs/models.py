from django.db import models
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone

from django.db.models import Count, Sum, Q
User=get_user_model()

# Create your models here.
class Worker(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
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
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_ratings = models.PositiveIntegerField(default=0)
    rating_count = models.PositiveIntegerField(default=0)

    def bayesian_average_rating(self):
        """Calculate Bayesian average rating for backward compatibility"""
        C = 3  # prior mean (e.g., assume average rating is 3 out of 5)
        m = 5  # minimum votes required to be considered credible

        ratings = self.ratings.all()
        n = ratings.count()

        if n == 0:
            return 0

        total_rating = sum(r.rating for r in ratings)
        R = total_rating / n

        # Bayesian average formula
        bayesian_avg = (m * C + n * R) / (m + n)
        return round(bayesian_avg, 1)

    def update_average_rating(self):
        """Update the worker's average rating using a weighted algorithm"""
        ratings = self.ratings.all()
        if not ratings.exists():
            self.average_rating = 0
            self.total_ratings = 0
            self.rating_count = 0
            self.save()
            return

        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        for rating in ratings:
            # Weight decreases with time (ratings older than 30 days have less weight)
            days_old = (timezone.now() - rating.created_at).days
            weight = max(0.5, 1 - (days_old / 30))  # Minimum weight of 0.5
            
            weighted_sum += rating.rating * weight
            total_weight += weight

        self.average_rating = round(weighted_sum / total_weight, 2)
        self.total_ratings = weighted_sum
        self.rating_count = ratings.count()
        self.save()

    def get_rating_breakdown(self):
        """Get the breakdown of ratings (how many 1-star, 2-star, etc.)"""
        ratings = self.ratings.all()
        breakdown = {
            5: 0,  # 5 stars
            4: 0,  # 4 stars
            3: 0,  # 3 stars
            2: 0,  # 2 stars
            1: 0   # 1 star
        }
        
        for rating in ratings:
            breakdown[rating.rating] += 1
            
        return breakdown

    def get_rating_percentage(self, star_count):
        """Get the percentage of a specific star rating"""
        breakdown = self.get_rating_breakdown()
        total = sum(breakdown.values())
        if total == 0:
            return 0
        # Convert star_count to integer if it's a string
        star_count = int(star_count) if isinstance(star_count, str) else star_count
        return (breakdown[star_count] / total) * 100

    def __str__(self):
        return f"{self.id} | {self.name}"

class Customer(models.Model):
    owner=models.OneToOneField(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=50)
    phone_number=PhoneNumberField(region="NP", unique=True)
    profile_pic=models.ImageField(upload_to="profiles/", blank=True)
    latitude = models.CharField(max_length=20,null=True,blank=True)
    longitude = models.CharField(max_length=20,null=True,blank=True)

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
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='ratings')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='given_ratings', null=True, blank=True)
    rating = models.PositiveSmallIntegerField()  # Rating between 1 and 5
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('worker', 'appointment', 'customer')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update worker's average rating when a new rating is added
        self.worker.update_average_rating()

    def __str__(self):
        return f"Rating {self.rating} by {self.customer.name if self.customer else 'Unknown'} for {self.worker.name}"

from django.contrib.auth.models import User

SERVICE_CATEGORIES = [
    ('PL', 'Plumber'),
    ('EL', 'Electrician'),
    ('CA', 'Carpenter'),
    ('CL', 'Cleaner'),
    ('ME', 'Mechanic'),
    ('PA', 'Painter'),
    ('AC', 'AC Repair'),
    ('IT', 'IT Support'),
    ('D','Driver'),

]

class Service(models.Model):
    title = models.CharField(max_length=100)
    category = models.CharField(choices=SERVICE_CATEGORIES, max_length=2)
    description = models.TextField()
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, help_text="Cost per hour in INR")
    estimated_time_hours = models.DecimalField(max_digits=4, decimal_places=2, help_text="Approximate time required in hours")
    image = models.ImageField(upload_to='service_images/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} - {self.get_category_display()}"

    @property
    def total_estimated_cost(self):
        return round(self.hourly_rate * self.estimated_time_hours, 2)