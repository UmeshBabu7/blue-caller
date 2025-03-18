from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from jobs.models import Worker, Customer, Appointment, WorkerRating
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.utils.timezone import make_aware, now
from django.core.mail import send_mail
from django.db.models import Avg, QuerySet
from jobs.templatetags.distance import calculate_distance
from django.db.models import F, ExpressionWrapper, FloatField
from datetime import datetime
from phonenumber_field.formfields import PhoneNumberField

def index(request):
    return HttpResponse("<h1>BlueCaller</h1>")

#class based view - reduces the code and simplifies
class WorkerListView(ListView):
    model = Worker
    template_name = 'worker_list.html'

    def get_queryset(self):
        query = self.request.GET.get('q')  # Search query
        filter_param = self.request.GET.get('filter')  # Filter parameter

        queryset = Worker.objects.all()

        # Apply search functionality (by tagline) first
        if query:
            queryset = queryset.filter(tagline__icontains=query)

        # Filter by Rating
        if filter_param == 'rating':
            # Filter workers by rating (only those already searched)
            queryset = queryset.annotate(avg_rating=Avg('workerrating__rating')).order_by('-avg_rating')


        # Filter by Distance
        elif filter_param == 'distance':
            customer = getattr(self.request.user, 'customer', None)
            if customer and customer.latitude and customer.longitude:
                customer_lat = float(customer.latitude)
                customer_lon = float(customer.longitude)

                # Annotate workers with calculated distance
                queryset = queryset.annotate(
                    distance=ExpressionWrapper(
                        # Distance formula using latitudes and longitudes (Haversine formula)
                        (F('latitude') - customer_lat) ** 2 + (F('longitude') - customer_lon) ** 2,
                        output_field=FloatField()
                    )
                ).order_by('distance')  # Order by the calculated distance

        return queryset


        
    def get_context_data(self, **kwargs):
        # Get the context data from the parent class
        context = super().get_context_data(**kwargs)
        
        # Get the query from the URL (use 'q' here instead of 'query')
        query = self.request.GET.get('q')
        
        # Add 'q' to the context so it can be used in the template
        context['q'] = query
        # Add worker appointments if the user is a worker
        if hasattr(self.request.user, 'worker'):
            appointments = Appointment.objects.filter(worker=self.request.user.worker).select_related('customer')
            context['appointments'] = appointments

        # Add average rating for each worker
        workers = context.get('worker_list', self.get_queryset())  # Use get_queryset as fallback
        for worker in workers:
            # Calculate the worker's average rating
            average_rating = WorkerRating.objects.filter(appointment__worker=worker).aggregate(Avg('average_rating'))['average_rating__avg']
            worker.average_rating = round(average_rating, 1) if average_rating else 0  # Default to 0 if no ratings exist

            # Get the total number of ratings
            total_ratings = WorkerRating.objects.filter(appointment__worker=worker).count()
            worker.total_ratings = total_ratings  # Pass the total number of ratings to the template

            # Calculate the number of stars
            full_stars = int(worker.average_rating)
            half_star = 1 if worker.average_rating % 1 >= 0.5 else 0
            empty_stars = 5 - (full_stars + half_star)
            
            worker.full_stars = [1] * full_stars  # List of full stars
            worker.half_star = [1] * half_star  # List for half star (1 or 0)
            worker.empty_stars = [1] * empty_stars  # List of empty stars
        
        context['worker_list'] = workers  # Ensure worker_list is added explicitly
        return context

class WorkerDetailView(LoginRequiredMixin, DetailView):
    model = Worker
    template_name = 'jobs/worker_detail.html'  # Specify your template file

    def get_queryset(self):
        # Return all workers initially
        return Worker.objects.all()

    def get_object(self, queryset=None):
        # Get the worker object based on the provided ID
        worker = super().get_object(queryset)
        
        # Ensure that the user is either the owner of the worker or a customer
        if self.request.user != worker.owner and not hasattr(self.request.user, 'customer'):
            # Raise 403 if the user is not authorized to view the worker's detail
            raise PermissionDenied("You do not have permission to view this worker's details.")
        return worker

    def get_context_data(self, **kwargs):
        # Add additional context data to the template
        context = super().get_context_data(**kwargs)
        worker = self.get_object()
        
        # Calculate the worker's average rating

        average_rating = WorkerRating.objects.filter(appointment__worker=worker).aggregate(Avg('average_rating'))['average_rating__avg']
        context['average_rating'] = round(average_rating, 1) if average_rating else 0  # Default to 0 if no ratings exist

        total_ratings = WorkerRating.objects.filter(appointment__worker=worker).count()
        context['total_ratings'] = total_ratings
        full_stars = int(context['average_rating'])
        half_star = 1 if context['average_rating'] % 1 >= 0.5 else 0
        empty_stars = 5 - (full_stars + half_star)
        
        context['full_stars'] = [1] * full_stars  # List of full stars
        context['half_star'] = [1] * half_star  # List for half star (1 or 0)
        context['empty_stars'] = [1] * empty_stars  # List of empty stars
        return context

class WorkerCreateView(LoginRequiredMixin, CreateView):
    model = Worker
    fields=['name','profile_pic','tagline','phone_number','bio','citizenship_image', 'certificate_file']
    success_url=reverse_lazy('worker-list')

    def form_valid(self, form):
        form.instance.owner=self.request.user
        form.instance.latitude = self.request.POST.get('latitude')
        form.instance.longitude = self.request.POST.get('longitude')
        return super(WorkerCreateView, self).form_valid(form)
    
    def add_worker(request):
        if request.method == 'POST':
            form = WorkerCreateView(request.POST, request.FILES)  # Include request.FILES to handle file uploads
            if form.is_valid():
                form.save()  # Save the worker instance
                return redirect('success')  # Redirect after a successful submission
        else:
            form = WorkerCreateView()

        return render(request, 'add_worker.html', {'form': form})

# naming convention of the templates for these classes ..CreateView expect is model_form.html

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    fields=['name','profile_pic','phone_number']
    success_url=reverse_lazy('worker-list')

    def form_valid(self, form):    
        form.instance.latitude = self.request.POST.get('latitude')
        form.instance.longitude = self.request.POST.get('longitude')
        form.instance.owner=self.request.user
        return super(CustomerCreateView, self).form_valid(form)    

@login_required
def handle_login(request):
    # check if user has a worker/customer account -> take them home
    # if they don't , render some template where they can select one or the other

    if request.user.get_worker() or request.user.get_customer():
        return redirect(reverse_lazy('worker-list'))
    
    
    return render(request,'jobs/choose_account.html',{})

def appoint_worker(request, worker_id):
    worker = get_object_or_404(Worker, id=worker_id)

    # Check if the worker already has a pending appointment
    appointment_count = Appointment.objects.filter(status="pending", worker=worker).count()
    if appointment_count < 1:
        if request.method == "POST":
            customer = get_object_or_404(Customer, owner=request.user)
            appointment_date_str = request.POST.get("appointment_date")

            try:
                # Parse the date string into a timezone-aware datetime object
                appointment_date = make_aware(datetime.strptime(appointment_date_str, "%Y-%m-%d"))
                
                # Check if the selected date is in the future
                if appointment_date <= now():
                    messages.error(request, "You can only book appointments for future dates.")
                    return redirect('worker-list')

                # Create a new appointment with the selected date
                appointment = Appointment.objects.create(
                    customer=customer,
                    worker=worker,
                    appointment_date=appointment_date,
                    status="pending"
                )

                # Update the worker's appointment status
                worker.appointed = True
                worker.appointment_date = appointment.appointment_date
                worker.save()

                messages.success(request, "Worker has been appointed and notified successfully.")
            except ValueError:
                messages.error(request, "Invalid appointment date. Please try again.")
    else:
        messages.error(request, "Worker has already been appointed.")

    return redirect('worker-list')

def send_email_to_worker(worker):
    subject = "Appointment Details"
    message = f"Dear {worker.name},\n\n You have been appointed on {worker.appointment_date}.\n\nThankyou!"
    from_email = "mitas.player@gmail.com"
    recipent_list = [worker.email]
    send_mail(subject, message, from_email, recipent_list)

def customer_appointments(request):
    # Assuming the logged-in user is a customer
    customer = get_object_or_404(Customer, owner=request.user)
    appointments = Appointment.objects.filter(customer=customer)
    return render(request, 'jobs/customer_appointments.html', {'appointments': appointments})

# View for Workers to Manage Appointments
def worker_appointments(request):
    # Assuming the logged-in user is a worker
    worker = get_object_or_404(Worker, owner=request.user)
    appointments = Appointment.objects.filter(worker=worker)
    return render(request, 'jobs/worker_appointments.html', {'appointments': appointments})

def accept_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.method == 'POST':
        appointment.status = 'accepted'
        appointment.save()
    return redirect('worker_list')

def reject_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.method == 'POST':
        appointment.status = 'rejected'
        appointment.save()
    return redirect('worker-list')

def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Ensure that only the customer or worker associated with the appointment can delete it
    if request.user == appointment.customer.owner or request.user == appointment.worker.owner:
        appointment.delete()
        messages.success(request, "Appointment deleted successfully.")
        if request.user == appointment.customer.owner:
            return redirect('customer_appointments')  # Redirect to customer appointments page
        elif request.user == appointment.worker.owner:
            return redirect('worker-list')  # Redirect to worker appointments page
    else:
        messages.error(request, "You are not authorized to delete this appointment.")
    
    return redirect('worker-list')  # Redirect back to customer appointments page

def complete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Ensure only the assigned worker can mark as completed
    if appointment.worker.owner != request.user:
        return HttpResponseForbidden("You are not allowed to complete this appointment.")

    # Update the status to "Completed"
    appointment.status = 'completed'
    appointment.save()

    return redirect('worker_list')  # Redirect to the worker's dashboard or another relevant page

def rate_worker(request, appointment_id):
    # Fetch the appointment and ensure the user is the customer
    appointment = get_object_or_404(Appointment, id=appointment_id, customer=request.user.customer)

    # Ensure the appointment is completed before allowing a rating
    if appointment.status != 'completed':
        return HttpResponseForbidden("You can only rate a worker after the appointment is completed.")

    if request.method == 'POST':
        rating_value = request.POST.get('rating')

        # Validate the rating value
        if not rating_value or not rating_value.isdigit() or int(rating_value) < 1 or int(rating_value) > 5:
            return HttpResponseForbidden("Invalid rating value. It should be between 1 and 5.")

        # Check if the user has already rated this appointment
        existing_rating = WorkerRating.objects.filter(appointment=appointment, appointment__customer=request.user.customer).exists()
        if existing_rating:
            return HttpResponseForbidden("You have already rated this worker for this appointment.")

        # Create the new rating
        if WorkerRating.objects.filter(worker = appointment.worker).exists():
            past_rating = WorkerRating.objects.get(worker = appointment.worker)
            total_rating = int(rating_value) + past_rating.rating
            appointment_count = past_rating.appointment.count()  + 1
            new_average = total_rating / appointment_count
            past_rating.rating = total_rating
            past_rating.average_rating = new_average
            past_rating.appointment.add(appointment)
            past_rating.save()
        else:
            new_object = WorkerRating.objects.create(worker=appointment.worker,rating=rating_value,average_rating=float(rating_value))
            new_object.appointment.add(appointment)
                                                     
              # Link the rating to the appointment via the ManyToManyField

        return redirect('worker-list')

    # For GET requests, render a form for rating
    return render(request, 'jobs/rate_worker.html', {'appointment': appointment})