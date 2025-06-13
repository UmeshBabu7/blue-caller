from django.contrib import admin
from django.http import HttpRequest
from .models import Worker, Customer,Appointment,WorkerRating,Contact

def verify_workers(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset):
    queryset.update(verified=True)

admin.site.register(Worker)
admin.site.register(Customer)
admin.site.register(Appointment)
admin.site.register(WorkerRating)
admin.site.register(Contact)
admin.site.add_action(verify_workers)

