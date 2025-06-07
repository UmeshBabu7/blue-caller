from django.urls import path
from .views import index , WorkerListView, WorkerDetailView, WorkerCreateView, CustomerCreateView, handle_login
from django.views.generic import TemplateView
from . import views


urlpatterns=[
    path('', TemplateView.as_view(template_name="landing/index.html"), name='landing-page'),
    path('get-started/', WorkerListView.as_view(), name='worker-list'),
    path('account-setup/', handle_login, name='handle-login'),
    path('worker/<int:pk>/',WorkerDetailView.as_view(), name='worker-detail'),
    path('worker/create/',WorkerCreateView.as_view(), name='worker-create'),
    path('customer/create/',CustomerCreateView.as_view(), name='customer-create'),
    path('worker/appoint/<int:worker_id>',views.appoint_worker, name='appoint-worker'),
    path('customer/appointments/', views.customer_appointments, name='customer_appointments'),
    path('worker/appointments/', views.worker_appointments, name='worker_appointments'),
    path('appointment/<int:appointment_id>/accept/', views.accept_appointment, name='accept_appointment'),
    path('appointment/<int:appointment_id>/reject/', views.reject_appointment, name='reject_appointment'),
    path('appointment/delete/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    path('complete-appointment/<int:appointment_id>/', views.complete_appointment, name='complete_appointment'),
    path('rate-worker/<int:appointment_id>/', views.rate_worker, name='rate_worker'),
]