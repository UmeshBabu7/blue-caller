"""
Django management command to load sample data for BlueCaller project.
Usage: python manage.py load_sample_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from jobs.models import (
    ServiceCategory, Service, SubTask, Worker, Customer,
    WorkerService, WorkerSubTaskPricing, Appointment,
    WorkerRating, Notification
)
from phonenumber_field.phonenumber import PhoneNumber
from decimal import Decimal
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Loads 15 sample data entries for BlueCaller project'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to load sample data...'))
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        # self.stdout.write(self.style.WARNING('Clearing existing data...'))
        # Notification.objects.all().delete()
        # WorkerRating.objects.all().delete()
        # Payment.objects.all().delete()
        # Appointment.objects.all().delete()
        # WorkerSubTaskPricing.objects.all().delete()
        # WorkerService.objects.all().delete()
        # Customer.objects.all().delete()
        # Worker.objects.all().delete()
        # SubTask.objects.all().delete()
        # Service.objects.all().delete()
        # ServiceCategory.objects.all().delete()
        
        # 1. Create ServiceCategories (3 entries)
        self.stdout.write('Creating ServiceCategories...')
        categories_data = [
            {'id': 'PL', 'name': 'Plumbing', 'description': 'Professional plumbing services including repairs, installations, and maintenance', 'icon': 'fa-faucet'},
            {'id': 'EL', 'name': 'Electrical', 'description': 'Electrical services for homes and businesses including wiring, repairs, and installations', 'icon': 'fa-bolt'},
            {'id': 'CA', 'name': 'Carpentry', 'description': 'Carpentry services including furniture making, repairs, and custom woodwork', 'icon': 'fa-hammer'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = ServiceCategory.objects.get_or_create(
                id=cat_data['id'],
                defaults=cat_data
            )
            categories[cat_data['id']] = category
            self.stdout.write(f'  ✓ Created/Found: {category.name}')
        
        # 2. Create Services (3 entries)
        self.stdout.write('Creating Services...')
        services_data = [
            {'category': 'PL', 'name': 'Pipe Repair', 'description': 'Expert pipe repair services for leaks, bursts, and blockages. Available 24/7 for emergencies.', 'base_pricing_type': 'hourly', 'is_active': True},
            {'category': 'EL', 'name': 'Wiring Installation', 'description': 'Complete electrical wiring installation for new constructions and renovations. Certified electricians.', 'base_pricing_type': 'sqft', 'is_active': True},
            {'category': 'CA', 'name': 'Furniture Making', 'description': 'Custom furniture making services including beds, tables, chairs, and cabinets. Quality woodwork guaranteed.', 'base_pricing_type': 'unit', 'is_active': True},
        ]
        
        services = {}
        for svc_data in services_data:
            category = categories[svc_data.pop('category')]
            service, created = Service.objects.get_or_create(
                category=category,
                name=svc_data['name'],
                defaults=svc_data
            )
            services[svc_data['name']] = service
            self.stdout.write(f'  ✓ Created/Found: {service.name}')
        
        # 3. Create SubTasks (3 entries)
        self.stdout.write('Creating SubTasks...')
        subtasks_data = [
            {'service': 'Pipe Repair', 'name': 'Leak Repair', 'description': 'Fix leaking pipes in kitchen, bathroom, or outdoor areas. Includes material cost.', 'default_pricing_type': 'fixed', 'duration': '2-4 hours', 'materials_included': True, 'special_offer': True, 'offer_price': Decimal('2500.00'), 'original_price': Decimal('3000.00'), 'requirements': 'Access to water supply, clear work area'},
            {'service': 'Wiring Installation', 'name': 'New House Wiring', 'description': 'Complete electrical wiring for new house construction. Includes all materials and labor.', 'default_pricing_type': 'sqft', 'duration': '3-5 days', 'materials_included': False, 'special_offer': False, 'requirements': 'Building plan approval, access to construction site'},
            {'service': 'Furniture Making', 'name': 'Custom Bed Frame', 'description': 'Handcrafted wooden bed frame with storage. Available in various sizes and wood types.', 'default_pricing_type': 'unit', 'duration': '5-7 days', 'materials_included': True, 'special_offer': False, 'requirements': 'Room measurements, wood preference'},
        ]
        
        subtasks = {}
        for st_data in subtasks_data:
            service_name = st_data.pop('service')
            service = services[service_name]
            subtask, created = SubTask.objects.get_or_create(
                service=service,
                name=st_data['name'],
                defaults=st_data
            )
            subtasks[st_data['name']] = subtask
            self.stdout.write(f'  ✓ Created/Found: {subtask.name}')
        
        # 4. Create Users and Workers (3 entries)
        self.stdout.write('Creating Users and Workers...')
        workers_data = [
            {'email': 'ram.shrestha@example.com', 'name': 'Ram Shrestha', 'phone': '+9779841234567', 'tagline': 'Expert Plumber with 10+ Years Experience', 'bio': 'Professional plumber specializing in pipe repairs, installations, and maintenance. Available for both residential and commercial projects. Licensed and insured.', 'verified': True, 'appointed': True, 'rating': 4.65, 'total_ratings': 127, 'shift': 'all', 'lat': 27.7172, 'lon': 85.3240},
            {'email': 'sita.poudel@example.com', 'name': 'Sita Poudel', 'phone': '+9779852345678', 'tagline': 'Certified Electrician - Safe & Reliable', 'bio': 'Licensed electrician with expertise in wiring, repairs, and installations. Specialized in modern smart home electrical systems. Safety first approach.', 'verified': True, 'appointed': True, 'rating': 4.82, 'total_ratings': 89, 'shift': 'day', 'lat': 27.7000, 'lon': 85.3000},
            {'email': 'hari.tamang@example.com', 'name': 'Hari Tamang', 'phone': '+9779863456789', 'tagline': 'Master Carpenter - Custom Furniture Specialist', 'bio': 'Experienced carpenter creating beautiful custom furniture. Specializes in traditional Nepali woodwork and modern designs. Quality craftsmanship guaranteed.', 'verified': True, 'appointed': False, 'rating': 4.50, 'total_ratings': 45, 'shift': 'all', 'lat': 27.7100, 'lon': 85.3100},
        ]
        
        workers = {}
        for w_data in workers_data:
            user, created = User.objects.get_or_create(
                email=w_data['email'],
                defaults={
                    'username': w_data['email'],
                    'first_name': w_data['name'].split()[0],
                    'last_name': ' '.join(w_data['name'].split()[1:]) if len(w_data['name'].split()) > 1 else '',
                }
            )
            if created:
                user.set_password('password123')  # Default password
                user.save()
            
            worker, created = Worker.objects.get_or_create(
                owner=user,
                defaults={
                    'name': w_data['name'],
                    'phone_number': w_data['phone'],
                    'tagline': w_data['tagline'],
                    'bio': w_data['bio'],
                    'verified': w_data['verified'],
                    'appointed': w_data['appointed'],
                    'average_rating': Decimal(str(w_data['rating'])),
                    'total_ratings': w_data['total_ratings'],
                    'rating_count': w_data['total_ratings'],
                    'shift': w_data['shift'],
                    'latitude': w_data['lat'],
                    'longitude': w_data['lon'],
                }
            )
            workers[w_data['name']] = worker
            self.stdout.write(f'  ✓ Created/Found: {worker.name}')
        
        # 5. Create Users and Customers (2 entries)
        self.stdout.write('Creating Users and Customers...')
        customers_data = [
            {'email': 'sanjay.kumar@example.com', 'name': 'Sanjay Kumar', 'phone': '+9779874567890', 'lat': 27.7150, 'lon': 85.3200},
            {'email': 'priya.sharma@example.com', 'name': 'Priya Sharma', 'phone': '+9779885678901', 'lat': 27.7050, 'lon': 85.3150},
        ]
        
        customers = {}
        for c_data in customers_data:
            user, created = User.objects.get_or_create(
                email=c_data['email'],
                defaults={
                    'username': c_data['email'],
                    'first_name': c_data['name'].split()[0],
                    'last_name': ' '.join(c_data['name'].split()[1:]) if len(c_data['name'].split()) > 1 else '',
                }
            )
            if created:
                user.set_password('password123')  # Default password
                user.save()
            
            customer, created = Customer.objects.get_or_create(
                owner=user,
                defaults={
                    'name': c_data['name'],
                    'phone_number': c_data['phone'],
                    'latitude': c_data['lat'],
                    'longitude': c_data['lon'],
                }
            )
            customers[c_data['name']] = customer
            self.stdout.write(f'  ✓ Created/Found: {customer.name}')
        
        # 6. Create WorkerServices (3 entries)
        self.stdout.write('Creating WorkerServices...')
        worker_services_data = [
            {'worker': 'Ram Shrestha', 'service': 'Pipe Repair'},
            {'worker': 'Sita Poudel', 'service': 'Wiring Installation'},
            {'worker': 'Hari Tamang', 'service': 'Furniture Making'},
        ]
        
        worker_services = {}
        for ws_data in worker_services_data:
            worker = workers[ws_data['worker']]
            service = services[ws_data['service']]
            ws, created = WorkerService.objects.get_or_create(
                worker=worker,
                service=service,
                defaults={'is_available': True}
            )
            worker_services[f"{ws_data['worker']}_{ws_data['service']}"] = ws
            self.stdout.write(f'  ✓ Created/Found: {worker.name} - {service.name}')
        
        # 7. Create WorkerSubTaskPricing (3 entries)
        self.stdout.write('Creating WorkerSubTaskPricing...')
        pricing_data = [
            {'worker': 'Ram Shrestha', 'service': 'Pipe Repair', 'subtask': 'Leak Repair', 'pricing_type': 'fixed', 'price': Decimal('2500.00'), 'experience_level': 'expert', 'night_shift_extra': Decimal('500.00'), 'min_hours': 2},
            {'worker': 'Sita Poudel', 'service': 'Wiring Installation', 'subtask': 'New House Wiring', 'pricing_type': 'sqft', 'price': Decimal('450.00'), 'experience_level': 'expert', 'night_shift_extra': Decimal('0.00'), 'min_hours': 1},
            {'worker': 'Hari Tamang', 'service': 'Furniture Making', 'subtask': 'Custom Bed Frame', 'pricing_type': 'unit', 'price': Decimal('15000.00'), 'experience_level': 'intermediate', 'night_shift_extra': Decimal('0.00'), 'min_hours': 1},
        ]
        
        pricings = {}
        for p_data in pricing_data:
            ws_key = f"{p_data['worker']}_{p_data['service']}"
            worker_service = worker_services[ws_key]
            subtask = subtasks[p_data['subtask']]
            pricing, created = WorkerSubTaskPricing.objects.get_or_create(
                worker_service=worker_service,
                subtask=subtask,
                defaults={
                    'pricing_type': p_data['pricing_type'],
                    'price': p_data['price'],
                    'experience_level': p_data['experience_level'],
                    'night_shift_extra': p_data['night_shift_extra'],
                    'min_hours': p_data['min_hours'],
                }
            )
            pricings[f"{p_data['worker']}_{p_data['subtask']}"] = pricing
            self.stdout.write(f'  ✓ Created/Found: {pricing}')
        
        # 8. Create Appointments (3 entries)
        self.stdout.write('Creating Appointments...')
        appointments_data = [
            {'customer': 'Sanjay Kumar', 'worker': 'Ram Shrestha', 'subtask': 'Leak Repair', 'date': timezone.now() + timedelta(days=1), 'status': 'accepted', 'shift_type': 'day', 'location': 'Baneshwor, Kathmandu - House No. 45, Near Baneshwor Chowk', 'instructions': 'Please bring all necessary tools. Kitchen sink is leaking.', 'cust_completed': False, 'work_completed': False, 'cust_lat': 27.7150, 'cust_lon': 85.3200},
            {'customer': 'Priya Sharma', 'worker': 'Sita Poudel', 'subtask': 'New House Wiring', 'date': timezone.now() + timedelta(days=3), 'status': 'pending', 'shift_type': 'day', 'location': 'Thamel, Kathmandu - Apartment 3B, Building No. 12', 'instructions': 'Need complete wiring for 2BHK apartment. Please quote before starting.', 'cust_completed': False, 'work_completed': False, 'cust_lat': 27.7050, 'cust_lon': 85.3150},
            {'customer': 'Sanjay Kumar', 'worker': 'Hari Tamang', 'subtask': 'Custom Bed Frame', 'date': timezone.now() - timedelta(days=5), 'status': 'completed', 'shift_type': 'day', 'location': 'Lazimpat, Kathmandu - House No. 23', 'instructions': 'Need queen size bed frame with storage. Prefer teak wood.', 'cust_completed': True, 'work_completed': True, 'cust_lat': 27.7150, 'cust_lon': 85.3200},
        ]
        
        appointments = {}
        for a_data in appointments_data:
            customer = customers[a_data['customer']]
            worker = workers[a_data['worker']]
            pricing_key = f"{a_data['worker']}_{a_data['subtask']}"
            pricing = pricings[pricing_key]
            
            appointment, created = Appointment.objects.get_or_create(
                customer=customer,
                worker=worker,
                service_subtask=pricing,
                appointment_date=a_data['date'],
                defaults={
                    'status': a_data['status'],
                    'shift_type': a_data['shift_type'],
                    'location': a_data['location'],
                    'special_instructions': a_data['instructions'],
                    'customer_completed': a_data['cust_completed'],
                    'worker_completed': a_data['work_completed'],
                    'customer_latitude': a_data['cust_lat'],
                    'customer_longitude': a_data['cust_lon'],
                }
            )
            appointments[f"{a_data['customer']}_{a_data['worker']}"] = appointment
            self.stdout.write(f'  ✓ Created/Found: Appointment {appointment.id}')
        
        # 9. Create WorkerRatings (3 entries)
        self.stdout.write('Creating WorkerRatings...')
        ratings_data = [
            {'worker': 'Ram Shrestha', 'customer': 'Sanjay Kumar', 'appointment': 'Sanjay Kumar_Ram Shrestha', 'rating': 5, 'comment': 'Excellent service! Fixed the leak quickly and professionally. Highly recommended.'},
            {'worker': 'Hari Tamang', 'customer': 'Sanjay Kumar', 'appointment': 'Sanjay Kumar_Hari Tamang', 'rating': 5, 'comment': 'Beautiful bed frame! Exactly as requested. Great craftsmanship and timely delivery.'},
            {'worker': 'Sita Poudel', 'customer': 'Priya Sharma', 'appointment': None, 'rating': 4, 'comment': 'Good work, but took longer than expected. Quality is satisfactory.'},
        ]
        
        for r_data in ratings_data:
            worker = workers[r_data['worker']]
            customer = customers[r_data['customer']]
            appointment = appointments.get(r_data['appointment']) if r_data['appointment'] else None
            
            # Create rating (appointment is optional)
            rating, created = WorkerRating.objects.get_or_create(
                worker=worker,
                customer=customer,
                appointment=appointment,
                defaults={
                    'rating': r_data['rating'],
                    'comment': r_data['comment'],
                }
            )
            self.stdout.write(f'  ✓ Created/Found: Rating {rating.rating} stars')
        
        # 11. Create Notifications (3 entries)
        self.stdout.write('Creating Notifications...')
        notifications_data = [
            {'type': 'worker', 'worker': 'Ram Shrestha', 'notification_type': 'appointment_request', 'title': 'New Appointment Request', 'message': 'Sanjay Kumar has requested an appointment for Leak Repair service on December 20, 2024 at 10:00 AM.', 'appointment': 'Sanjay Kumar_Ram Shrestha', 'is_read': False},
            {'type': 'customer', 'customer': 'Sanjay Kumar', 'notification_type': 'appointment_accepted', 'title': 'Appointment Accepted', 'message': 'Ram Shrestha has accepted your appointment request for Leak Repair on December 20, 2024.', 'appointment': 'Sanjay Kumar_Ram Shrestha', 'is_read': True},
            {'type': 'worker', 'worker': 'Hari Tamang', 'notification_type': 'rating_received', 'title': 'New Rating Received', 'message': 'You received a 5-star rating from Sanjay Kumar for your Custom Bed Frame service.', 'appointment': 'Sanjay Kumar_Hari Tamang', 'is_read': False},
        ]
        
        for n_data in notifications_data:
            appointment = appointments.get(n_data['appointment'])
            worker = workers.get(n_data.get('worker')) if n_data['type'] == 'worker' else None
            customer = customers.get(n_data.get('customer')) if n_data['type'] == 'customer' else None
            
            notification, created = Notification.objects.get_or_create(
                notification_type=n_data['notification_type'],
                title=n_data['title'],
                appointment=appointment,
                defaults={
                    'worker': worker,
                    'customer': customer,
                    'message': n_data['message'],
                    'is_read': n_data['is_read'],
                }
            )
            self.stdout.write(f'  ✓ Created/Found: Notification {notification.title}')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Successfully loaded 15 sample data entries!'))
        self.stdout.write(self.style.SUCCESS('\nSummary:'))
        self.stdout.write(f'  - ServiceCategories: {ServiceCategory.objects.count()}')
        self.stdout.write(f'  - Services: {Service.objects.count()}')
        self.stdout.write(f'  - SubTasks: {SubTask.objects.count()}')
        self.stdout.write(f'  - Workers: {Worker.objects.count()}')
        self.stdout.write(f'  - Customers: {Customer.objects.count()}')
        self.stdout.write(f'  - WorkerServices: {WorkerService.objects.count()}')
        self.stdout.write(f'  - WorkerSubTaskPricing: {WorkerSubTaskPricing.objects.count()}')
        self.stdout.write(f'  - Appointments: {Appointment.objects.count()}')
        self.stdout.write(f'  - WorkerRatings: {WorkerRating.objects.count()}')
        self.stdout.write(f'  - Notifications: {Notification.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\nDefault password for all test users: password123'))

