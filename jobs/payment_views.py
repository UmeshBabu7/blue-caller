# payment_views.py - Payment related views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
import json
import logging

from .models import Appointment, Payment
from .payment_utils import EsewaPayment, calculate_payment_amounts, create_payment_request_id

logger = logging.getLogger(__name__)

@login_required
def initiate_payment(request, appointment_id):
    """
    Initiate payment for an appointment
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user is the customer for this appointment
    if appointment.customer.owner != request.user:
        messages.error(request, "You don't have permission to access this payment.")
        return redirect('customer_appointments')
    
    # Check if appointment has a service subtask with pricing
    if not appointment.service_subtask:
        messages.error(request, "No pricing information available for this appointment.")
        return redirect('customer_appointments')
    
    # Calculate total amount
    total_amount = appointment.service_subtask.price
    
    # Calculate payment amounts
    payment_amounts = calculate_payment_amounts(
        total_amount, 
        getattr(settings, 'INITIAL_PAYMENT_PERCENTAGE', 20)
    )
    
    # Update appointment with payment amounts
    appointment.total_amount = payment_amounts['total_amount']
    appointment.initial_payment_amount = payment_amounts['initial_amount']
    appointment.final_payment_amount = payment_amounts['final_amount']
    appointment.save()
    
    # Check if initial payment already exists
    initial_payment = appointment.get_initial_payment()
    if initial_payment and initial_payment.status == 'completed':
        messages.info(request, "Initial payment already completed.")
        return redirect('customer_appointments')
    
    # Create or get initial payment
    if not initial_payment:
        payment_request_id = create_payment_request_id()
        initial_payment = Payment.objects.create(
            appointment=appointment,
            payment_type='initial',
            amount=payment_amounts['initial_amount'],
            payment_request_id=payment_request_id
        )
    
    # Initialize eSewa payment
    esewa = EsewaPayment()
    payment_request = esewa.generate_payment_request(
        amount=payment_amounts['initial_amount'],
        product_name=f"Initial Payment - {appointment.worker.name}",
        payment_request_id=initial_payment.payment_request_id
    )
    
    if not payment_request:
        messages.error(request, "Failed to initialize payment. Please try again.")
        return redirect('customer_appointments')
    
    context = {
        'appointment': appointment,
        'payment': initial_payment,
        'payment_request': payment_request,
        'amount': payment_amounts['initial_amount'],
        'total_amount': payment_amounts['total_amount'],
        'final_amount': payment_amounts['final_amount']
    }
    
    return render(request, 'jobs/payment/initiate_payment.html', context)

@login_required
def payment_success(request):
    """
    Handle successful payment callback from eSewa
    """
    try:
        # Get payment parameters from eSewa
        oid = request.GET.get('oid')  # Our payment request ID
        amt = request.GET.get('amt')  # Amount
        refId = request.GET.get('refId')  # eSewa transaction ID
        
        if not all([oid, amt, refId]):
            messages.error(request, "Invalid payment response.")
            return redirect('customer_appointments')
        
        # Find the payment
        payment = get_object_or_404(Payment, payment_request_id=oid)
        
        # Verify payment with eSewa
        esewa = EsewaPayment()
        is_verified, message = esewa.verify_payment(oid, refId, amt)
        
        if is_verified:
            # Update payment status
            payment.status = 'completed'
            payment.esewa_transaction_id = refId
            payment.esewa_status = 'success'
            payment.paid_at = timezone.now()
            payment.save()
            
            # Update appointment payment status
            appointment = payment.appointment
            if payment.payment_type == 'initial':
                appointment.payment_status = 'partial'
                # Send notification to worker about payment
                # You can add notification logic here
            elif payment.payment_type == 'final':
                appointment.payment_status = 'completed'
            
            appointment.save()
            
            messages.success(request, f"Payment of ₹{amt} completed successfully!")
            
            # Redirect based on payment type
            if payment.payment_type == 'initial':
                return redirect('customer_appointments')
            else:
                return redirect('customer_appointments')
        else:
            messages.error(request, f"Payment verification failed: {message}")
            return redirect('customer_appointments')
            
    except Exception as e:
        logger.error(f"Error in payment success callback: {e}")
        messages.error(request, "An error occurred while processing your payment.")
        return redirect('customer_appointments')

@login_required
def payment_failure(request):
    """
    Handle failed payment callback from eSewa
    """
    messages.error(request, "Payment was not completed. Please try again.")
    return redirect('customer_appointments')

@login_required
def final_payment(request, appointment_id):
    """
    Process final payment for completed appointment
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user is the customer for this appointment
    if appointment.customer.owner != request.user:
        messages.error(request, "You don't have permission to access this payment.")
        return redirect('customer_appointments')
    
    # Check if appointment is completed
    if appointment.status != 'completed':
        messages.error(request, "Appointment must be completed before final payment.")
        return redirect('customer_appointments')
    
    # Check if final payment already exists and is completed
    final_payment = appointment.get_final_payment()
    if final_payment and final_payment.status == 'completed':
        messages.info(request, "Final payment already completed.")
        return redirect('customer_appointments')
    
    # Create final payment if it doesn't exist
    if not final_payment:
        payment_request_id = create_payment_request_id()
        final_payment = Payment.objects.create(
            appointment=appointment,
            payment_type='final',
            amount=appointment.final_payment_amount,
            payment_request_id=payment_request_id
        )
    
    # Initialize eSewa payment
    esewa = EsewaPayment()
    payment_request = esewa.generate_payment_request(
        amount=appointment.final_payment_amount,
        product_name=f"Final Payment - {appointment.worker.name}",
        payment_request_id=final_payment.payment_request_id
    )
    
    if not payment_request:
        messages.error(request, "Failed to initialize payment. Please try again.")
        return redirect('customer_appointments')
    
    context = {
        'appointment': appointment,
        'payment': final_payment,
        'payment_request': payment_request,
        'amount': appointment.final_payment_amount,
        'total_amount': appointment.total_amount,
        'initial_amount': appointment.initial_payment_amount
    }
    
    return render(request, 'jobs/payment/final_payment.html', context)

@login_required
def payment_history(request):
    """
    Display payment history for the customer
    """
    customer = request.user.customer
    appointments = Appointment.objects.filter(customer=customer).order_by('-created_at')
    
    # Get all payments for these appointments
    payments = Payment.objects.filter(appointment__in=appointments).order_by('-created_at')
    
    context = {
        'payments': payments,
        'appointments': appointments
    }
    
    return render(request, 'jobs/payment/payment_history.html', context)

@login_required
def payment_details(request, payment_id):
    """
    Display details of a specific payment
    """
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Check if user has permission to view this payment
    if payment.appointment.customer.owner != request.user:
        messages.error(request, "You don't have permission to view this payment.")
        return redirect('customer_appointments')
    
    context = {
        'payment': payment,
        'appointment': payment.appointment
    }
    
    return render(request, 'jobs/payment/payment_details.html', context)
