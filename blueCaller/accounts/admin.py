from django.contrib import admin
from django.contrib.auth import get_user_model

User=get_user_model()
# Register your models here.

from itertools import islice
import json
from django.contrib import admin
from django.shortcuts import get_object_or_404, render
from Transactions.models import TransactionMain
from .models import ProjectCategory, Plan, UserActivity
from django.core.files.storage import default_storage
from django.contrib.admin.actions import delete_selected 
from django.contrib.auth.hashers import make_password
from django import forms
from bolpatra.models import *
from constants import BIDDER, CSV_EXPORT_HEADERS, CSV_IMPORT_HEADERS, PAYMENT_METHOD_CHOICES
from django.contrib import messages
from django.utils.html import format_html
from datetime import date, datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from constants import NepaliDistricts
from Tender.models import Source
from itertools import islice
from django.db.models import Q
from django.contrib.admin.views.main import ChangeList
from django.core.paginator import Paginator
from django.utils.html import format_html
import csv
import logging

from urllib.parse import urlencode

logger = logging.getLogger("django")

User = get_user_model()

# Custom Filters start
class RoleFilter(admin.SimpleListFilter):
    title ='Role'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html' 

    def lookups(self, request, model_admin):
        roles = Role.objects.all()
        return [(role.id, role.name) for role in roles]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(userrole__role_id=self.value())
        return queryset

    def choices(self, changelist):
        # Remove the "All" option
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                yield choice

class OfferFilter(admin.SimpleListFilter):
    title = 'Offer'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html' 

    def lookups(self, request, model_admin):
        offer = User.offer_choices()
        del offer[0]
        return offer

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(additional_info__offer=self.value())
        
    def choices(self, changelist):
        # Remove the "All" option
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                yield choice

class RemarksFilter(admin.SimpleListFilter):
    title = 'Remarks'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html' 

    def lookups(self, request, model_admin):
        # Get all remarks choices excluding the default empty option
        remarks = User.remarks_choices()[1:]  
        return remarks

    def queryset(self, request, queryset):
        # Filter queryset based on selected remark
        if self.value():
            return queryset.filter(additional_info__remarks=self.value())
        return queryset

    def choices(self, changelist):
        # Remove the "All" option
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                yield choice


class DistrictFilter(admin.SimpleListFilter):
    title = 'District'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html'  

    def lookups(self, request, model_admin):
        return [(district[0], district[1]) for district in NepaliDistricts]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(district__iexact=self.value())
        return queryset
     
    def choices(self, changelist):
        # Remove the default "All" option
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                yield choice


class UpdatedByFilter(admin.SimpleListFilter):
    title = 'Updated'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html'

    def lookups(self, request, model_admin):
        # Fetch only admin and staff users
        users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
        return [(user.id, user.get_full_name() or user.username) for user in users]

    def queryset(self, request, queryset):
        if self.value():
            try:
                user = User.objects.get(id=self.value())
                return queryset.filter(additional_info__updated_by=user.id)
            except User.DoesNotExist:
                return queryset.none()
        return queryset


    def choices(self, changelist):
        # Override choices to remove the "All" option
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                # Directly set the user ID as the choice value without any additional query string
                choice['value'] = choice['query_string'].split('=')[-1]
                yield choice

class ProjectCategoryFilter(admin.SimpleListFilter):
    title = 'Project'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html'  

    def lookups(self, request, model_admin):
        # Fetch all ProjectCategory instances for dynamic filtering
        categories = ProjectCategory.objects.all()
        return [(category.name, category.name) for category in categories]
    
    def queryset(self, request, queryset):
        selected_categories = request.GET.getlist(self.parameter_name)
        if selected_categories:
            return queryset.filter(project_category__name__in=selected_categories)
        return queryset

    def choices(self, changelist):
        # Ensure that each choice is properly retained in the search field (keep multiple selections)
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                yield choice

class SourceFilter(admin.SimpleListFilter):
    title = 'Source'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html'

    def lookups(self, request, model_admin):
        sources = Source.objects.all()
        # Dynamically fetch all Source instances to populate the filter options
        return [(source.title, source.title) for source in sources]  
    
    def queryset(self, request, queryset):
        selected_titles = request.GET.getlist(self.parameter_name)
        if selected_titles:
             # Filter by category names if multiple are selected
            return queryset.filter(source__title__in=selected_titles)  

    def choices(self, changelist):
    # Remove the default "All" option
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                yield choice
        
class EmailStatusFilter(admin.SimpleListFilter):
    title = 'E-mail Status'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html' 

    def lookups(self, request, model_admin):
        return[
            (True, 'Verified'),
            (False, 'Un-Verified')
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(email_verification=self.value())
        
    def choices(self, changelist):
        # Remove the "All" option
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                yield choice

class PlanRemainingDaysFilter(admin.SimpleListFilter):
    title = 'Plan Remaining Days'
    parameter_name = 'plan_remaining_days'
    input_type = 'number'
    template = 'admin/input_filter.html' 

    def lookups(self, request, model_admin):
        return [('placeholder', _('Select a day'))]

    def queryset(self, request, queryset):
        try:
            remaining_days = request.GET.get(self.parameter_name)
            if remaining_days is not None:
                    today = date.today()
                    if int(remaining_days) == 0:
                        return queryset.filter(plan_end_date__lt=today)
                    else:
                        days_remaining = int(remaining_days)
                        target_date = today + timedelta(days=days_remaining)
                        return queryset.filter(plan_end_date=target_date)
            return queryset
        except ValueError:
            pass 

class PlanEndDateFilter(admin.SimpleListFilter):
    title = _('Plan End Date')
    parameter_name = 'plan_end_date'
    input_type = 'date'
    template = 'admin/input_filter.html'  

    def lookups(self, request, model_admin):
        return [('placeholder', _('Select a date'))]

    def queryset(self, request, queryset):
        if self.value() and self.value() != 'placeholder':
            try:
                filter_date = date.fromisoformat(self.value())
                return queryset.filter(plan_end_date=filter_date)
            except ValueError:
                return queryset.none()
        return queryset

    def value(self):
        return self.used_parameters.get(self.parameter_name, None)
    

class PlanFilter(admin.SimpleListFilter):
    title = 'Plan'
    parameter_name = title
    template = 'admin/custom_dropdown_filter.html' 

    def lookups(self, request, model_admin):
        return PLAN_TYPE
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user_type=self.value())
        return queryset
    
    def choices(self, changelist):
        # Remove the "All" option
        for choice in super().choices(changelist):
            if choice['display'] != 'All':
                yield choice
    
class FollowUpDateFilter(admin.SimpleListFilter):
    title = _('Follow-Up Date')
    parameter_name = 'follow-up'
    input_type = 'date'
    template = 'admin/input_filter.html'

    def lookups(self, request, modle_admin):
        return [('placeholder', _('Select a date'))]
    
    def queryset(self, request, queryset):
        if self.value() and self.value() != 'placeholder':
            try:
                filter_date = date.fromisoformat(self.value())
                return queryset.filter(additional_info__follow_up_date=str(filter_date))
            except ValueError:
                return queryset.none()
        return queryset


class UserAdminForm(forms.ModelForm):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all(), required=False)
    new_password = forms.CharField(widget=forms.PasswordInput)
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, required=False)
    amount = forms.CharField(required=False, label='Amount')
    description = forms.CharField(required=False, label='Description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password'].required = False
         # Check if 'plan' is provided in POST data
        if self.data.get('plan', '') and self.data.get('plan', '') != '':
            # Make these fields required if a plan is selected
            self.fields['payment_method'].required = True
            self.fields['amount'].required = True
            self.fields['description'].required = True
    class Meta:
        model = User
        fields = ('first_name', 'middle_name', 'last_name', 'email', 'new_password', 'contact_no', 'plan', 'payment_method', 'amount','description')

class ReverseDefaultPaginationChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_last_page_by_default = True

    def get_results(self, request):
        # Standard behavior first
        super().get_results(request)

        # Only show last page by default if 'p' is not present and 'show_all' is not set
        if (
            'p' not in request.GET
            and getattr(self, 'show_last_page_by_default', False)
            and request.GET.get("show_all") != "true"
        ):
            self.page_num = self.paginator.num_pages
            self.result_list = self.paginator.page(self.page_num).object_list
        if self.model_admin.actions:
            self.list_display = ['action_checkbox'] + list(self.model_admin.list_display)




class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm
    change_list_template = 'admin/users.html'
    ordering = ['id']
    default_to_last_page = True
    list_per_page = 100  # number of items shown per page by default
    

    # ❶ Use custom ChangeList for reverse pagination (shows last page by default)
    def get_changelist(self, request, **kwargs):
        return ReverseDefaultPaginationChangeList

    # ❷ Main view for the admin user list page
    def changelist_view(self, request, extra_context=None):
        show_all = request.GET.get("show_all") == "true"

        # a. Go to the last page by default (only when not showing all data)
        if (
            not show_all
            and "p" not in request.GET
            and getattr(self, "default_to_last_page", True)
        ):
            cl = self.get_changelist_instance(request)
            paginator = Paginator(cl.get_queryset(request), self.list_per_page)
            request.GET = request.GET.copy()  # allow changes to GET data
            request.GET["p"] = paginator.num_pages  # set to last page number

        # b. Build a clean URL (without show_all or page number) for JS
        if show_all:
            base_query = {
                k: v for k, v in request.GET.items()
                if k not in ("show_all", "p")
            }
            clean_url = f"{request.path}"
            if base_query:
                clean_url += f"?{urlencode(base_query)}"
        else:
            clean_url = None

        # c. Add clean_url and show_all flag to the context for the template
        if extra_context is None:
            extra_context = {}
        extra_context["clean_url"] = clean_url
        extra_context["show_all"] = show_all

        return super().changelist_view(request, extra_context)

    # ❸ If "show_all=true" is used, return total number of items
    def get_list_per_page(self, request):
        if request.GET.get("show_all") == "true":
            return self.get_queryset(request).count() or 1
        return super().get_list_per_page(request)

    # ❹ Create ChangeList instance and adjust per_page based on show_all flag
    def get_changelist_instance(self, request):
        mutable_get = request.GET.copy()
        show_all = mutable_get.get("show_all") == "true"

        # set per_page to total count if showing all, else use default
        per_page = (
            self.get_queryset(request).count() or 1
            if show_all else self.list_per_page
        )

        # remove show_all from request before filters are applied
        mutable_get.pop("show_all", None)
        request.GET = mutable_get

        # return the ChangeList instance with adjusted per_page
        return self.get_changelist(request)(
            request,
            self.model,
            self.list_display,
            self.list_display_links,
            self.list_filter,
            self.date_hierarchy,
            self.search_fields,
            self.list_select_related,
            per_page,
            self.list_max_show_all,
            self.list_editable,
            self,
            self.sortable_by,
        )


    def has_add_permission(self, request):
            return False
        
    def get_urls(self):
            urls = super().get_urls()
            custom_urls = [
                path('<int:pk>/detail/', self.admin_site.admin_view(self.user_detail_view), name='user_detail'),
                path('import/', self.admin_site.admin_view(self.import_csv_view), name='app_model_import'),   
            ]
            return custom_urls + urls
    
    
    def import_csv_view(self, request):
        """
        Handles the import of a CSV file to update user data.

        This view processes a POST request containing a CSV file, updates user data
        based on the contents of the file, and provides feedback on the number of
        successful and failed updates.

        Args:
            request (HttpRequest): The HTTP request object containing the CSV file.

        Returns:
            HttpResponse: Redirects back to the referring page with success or error messages.
            If the request method is not POST or no CSV file is provided, renders the import page.

        Raises:
            ValueError: If there is an issue with the CSV file content.
            Exception: For any other unexpected errors during the CSV file processing.
        """
        if request.method == 'POST' and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            try:
                updated_count, failed_count = self.handle_csv_upload(csv_file)
                messages.add_message(request, messages.SUCCESS, f'{updated_count} users updated, {failed_count} failed.')
            except ValueError as e:
                messages.add_message(request, messages.ERROR, str(e))
            except Exception as e:
                messages.add_message(request, messages.ERROR, f"An unexpected error occurred: {str(e)}")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        return render(request, 'admin/users.html')
        

    def handle_csv_upload(self, csv_file):
        """
        Handles the upload and processing of a CSV file to update user information.
        Args:
            csv_file (File): The CSV file containing user data to be processed.
        Raises:
            ValueError: If the CSV file is missing required headers.
        Returns:
            tuple: A tuple containing the count of successfully updated records and the count of failed updates.
        The CSV file should contain the following headers:
            - contact_number: The contact number of the user (required).
            - offer: The offer information to be updated (optional).
            - remarks: Remarks to be updated (optional).
            - description: Description to be updated (optional).
            - follow_up_date: Follow-up date in MM/DD/YYYY format (optional).
            - updated_by: Contact number of the staff member who updated the record (optional).
        The function performs the following steps:
            1. Reads and decodes the CSV file.
            2. Checks for missing headers and raises an error if any are missing.
            3. Iterates over the CSV data in chunks of 5000 records.
            4. For each record, retrieves the user by contact number and updates the user's additional information.
            5. Handles parsing and formatting of dates.
            6. Logs errors for users not found or other exceptions.
            7. Returns the count of successfully updated records and the count of failed updates.
        """
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        headers = reader.fieldnames
        missing_headers = [header for header in CSV_IMPORT_HEADERS if header not in headers]
        if missing_headers:
            raise ValueError(f"CSV file is missing the following headers: {', '.join(missing_headers)}")
        
        updated_count = 0
        failed_count = 0

        for chunk in islice(reader, 5000):
            # Retrieve the contact number from the CSV (convert to integer)
            contact_no = chunk.get('contact_number')
            try:
                contact_no = int(contact_no)  

                # Retrieve the user associated with this contact_no
                user = User.objects.get(contact_no=contact_no)
                additional_info = user.additional_info or {}

                # Extract and update 'offer' from the CSV
                offer = chunk.get('offer', '').strip()
                if offer:
                    additional_info['offer'] = offer

                # Extract and update 'remarks' from the CSV
                remarks = chunk.get('remarks', '').strip()
                if remarks:
                    additional_info['remarks'] = remarks

                # Extract and update 'description' from the CSV
                description = chunk.get('description', '').strip()
                if description:
                    additional_info['description'] = description
                else:
                    print(f"Description is empty for {contact_no}")

                # Parse and update 'follow_up_date' from the CSV
                follow_up_date = chunk.get('follow_up_date', '').strip()
                if follow_up_date:
                    try:
                        # Parse the date using MM/DD/YYYY format from the CSV
                        parsed_date = datetime.strptime(follow_up_date, '%m/%d/%Y')
                        # Store the date in ISO format (YYYY-MM-DD) for compatibility with input type="date"
                        additional_info['follow_up_date'] = parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        print(f"Invalid date format for {contact_no}. Skipping.")
                else:
                    print(f"Follow-up Date is empty for {contact_no}")

                # Extract and update 'updated_by' from the CSV
                updated_by = chunk.get('updated_by', '').strip()
                if updated_by:
                    updated_user = User.objects.filter(contact_no=updated_by, is_staff=True).first()
                    if updated_user:
                        additional_info['updated_by'] = updated_user.id

                # Save the updated additional_info to the user's record
                user.additional_info = additional_info
                user.save()

                updated_count += 1

            except User.DoesNotExist:
                failed_count += 1
                logger.error(f"Import CSV: User with contact {contact_no} not found.")
            except Exception as e:
                failed_count += 1
                logger.error(f"Import CSV: Error Updating {contact_no} : {str(e)}")

        return updated_count, failed_count
    
    def build_filters(self, params):
                    """
                    Build a dictionary of filters based on the provided parameters.

                    Args:
                        params (dict): A dictionary of parameters where keys are filter names and values are filter values.

                    Returns:
                        dict: A dictionary of filters to be used in querying the database.

                    The function processes the following types of fields:
                    - Additional Info Fields: Fields that are part of the 'additional_info' model.
                    - Date Fields: Fields that require date conversion from ISO format.
                    - List Fields: Fields that require splitting the value into a list.
                    - Integer Fields: Fields that require integer conversion and date calculations.
                    - Exact Fields: Fields that require exact matching.

                    The function skips any parameters with empty values and continues processing the rest.
                    """
                    filters = {}
                    additional_info_fields = {'offer', 'remarks'}
                    date_fields = {'follow-up': 'additional_info__follow_up_date', 'plan_end_date': 'plan_end_date'}
                    list_fields = {'project': 'project_category__name__in', 'source': 'source__title__in'}
                    int_fields = {'plan_remaining_days': 'plan_remaining_days'}
                    exact_fields = {'plan': 'user_type', 'role': 'userrole__role_id', 'updated': 'additional_info__updated_by', 'e-mail status': 'email_verification'}
            
                    params = params.copy()
                    params.pop("p", None)

                    for key, value in params.items():
                        if not value:
                            continue

                        key_lower = key.lower()
                        if key_lower in additional_info_fields:
                            filters[f"additional_info__{key_lower}"] = value
                        elif key_lower in date_fields:
                            try:
                                filter_date = date.fromisoformat(value)
                                filters[date_fields[key_lower]] = str(filter_date)
                            except ValueError:
                                continue
                        elif key_lower in int_fields:
                            try:
                                days_remaining = int(value)
                                today = date.today()
                                if days_remaining == 0:
                                    filters["plan_end_date__lt"] = today
                                else:
                                    target_date = today + timedelta(days=days_remaining)
                                    filters["plan_end_date"] = target_date
                            except ValueError:
                                continue
                        elif key_lower in list_fields:
                            filters[list_fields[key_lower]] = value.split(",")
                        elif key_lower in exact_fields:
                            filters[exact_fields[key_lower]] = value
                        else:
                            filters[key_lower] = value

                    return filters
                
                
    def user_detail_view(self, request, pk):
        """
        Display the detailed view of a user.

        Args:
            request (HttpRequest): The HTTP request object.
            pk (int): The primary key of the user to be displayed.

        Returns:
            HttpResponse: The rendered user detail page.

        Raises:
            Http404: If the user with the given primary key does not exist.
        """
        user = get_object_or_404(User, pk=pk)
        admin_context = self.admin_site.each_context(request)
        
        context = {
            'user': user,
            'image_host_url': settings.MEDIA_URL,
            **admin_context,
        }
        
        return render(request, 'admin/user_detail.html', context)
        
    # Override the response_add method
    def response_change(self, request, obj, post_url_continue=None):
        # If "Save and add another" is clicked, treat it as "Save"
        if "_addanother" in request.POST:
            return HttpResponseRedirect(reverse('admin:User_user_changelist'))
        return super().response_add(request, obj, post_url_continue)

    def get_queryset(self, request):
        return self.model.objects.filter(is_staff = False, is_superuser=False, is_deleted=False)
  
    @require_POST
    @method_decorator(csrf_exempt, name='dispatch')  # To bypass CSRF for AJAX requests
    def update_user_additional_info(request, pk):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                offer = data.get('offer')
                remarks = data.get('remarks')
                description = data.get('description')
                follow_up_date = data.get('follow_up_date')
                
                # Fetch and update the user object
                user = User.objects.get(pk=pk)
                additional_info = user.additional_info or {}

                additional_info['offer'] = offer
                additional_info['remarks'] = remarks
                additional_info['description'] = description
                additional_info['follow_up_date'] = follow_up_date
                if 'updated_by' not in additional_info:
                    additional_info['updated_by'] = request.user.id
                user.additional_info = additional_info
                user.save()

                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=400)

        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

    
    def save_model(self, request, obj, form, change):
        staff = request.user.id
        user_role = UserRole.user_role(obj.id)
        if user_role and user_role.role.name == BIDDER:
            if request.POST["plan"]:
                date_added, plan_type = Plan.plan_date_type(request.POST["plan"], obj.plan_end_date)
                obj.plan_end_date = date_added
                obj.user_type = plan_type
                PlanUpdate.save_data(user=obj.id, plan=request.POST["plan"], staff=staff)
                
                # insert payment detail in transaction main
                TransactionMain.objects.create(
                    description=request.POST["description"],
                    amount=request.POST["amount"],
                    user_id=obj.id,
                    transaction_idx=f'Manual-{datetime.now()}',
                    status='Completed',
                    payment_method=request.POST["payment_method"],
                    payment_type='Manual',
                    fee_for='Subscription',
                    plan_id=request.POST["plan"],
                    updated_by_id=staff
                )
                
        if request.POST["new_password"]:
            obj.password = make_password(request.POST["new_password"])
                
        obj.save()
        super().save_model(request, obj, form, change)

    
    # For update button field
    def update_button(self, obj):
        user_detail_url = reverse('admin:user_detail', args=[obj.pk])
        return format_html(
            '''
            <div style="display:flex;justify-content:center;">
                <button class="update-user-info-btn" data-user-id="{}" style="display: inline-block; background-color: white; padding: 4px 10px 10px 10px; border-radius: 5px; text-align: center;">
                    <img src="/static/admin/img/icon-changelink.svg" alt="Update User" style="height: 20px; width: 20px;">
                </button>
                <a href="{}" style="display: inline-block; background-color: white; padding: 4px 10px 10px 10px;margin-left:5px; border-radius: 5px; text-align: center;">
                    <img src="/static/admin/img/icon-viewlink.svg" alt="User Info" style="height: 20px; width: 20px;">
                </a>
            </div>
            ''',
            obj.id,
            user_detail_url
        )
    
    update_button.short_description = 'Action'
    update_button.allow_tags = True

        
    def email_verified(self, obj):
        company_name = obj.company_name if obj.company_name else 'N/A'
        if obj.email_verification:
            return format_html(
                f'<div><b>{obj.email}</b><img src="/static/admin/img/icon-yes.svg"/></div><div style="font-weight:400;color:#212529">{company_name}</div>'
            )
        else:
            return format_html(
                f'<div><b>{obj.email}</b><img src="/static/admin/img/icon-no.svg"/></div><div style="font-weight:400;color:#212529">{company_name}</div>'
            )
    email_verified.short_description = 'email'


    def verified_user_role(self, obj):
        try:
            role = '-'
            user_role = UserRole.user_role(obj.id)
            if user_role:
                role = user_role.role.name
                
            if obj.is_verified:
                return format_html(
                    f'''<div><b>{role}</b><img src="/static/admin/img/icon-yes.svg"/></div><div>{obj.user_type} Plan</div>'''
                )
            else:
                return format_html(
                    f'''<div><b>{role}</b><img src="/static/admin/img/icon-yes.svg"/></div><div>{obj.user_type} Plan</div>'''
                )
        except Exception as e:
            return 'N/A'
        
    verified_user_role.short_description = 'Role/Plan'
    
    def name_with_contact(self, obj):
        try:
            return format_html(
                f'''<div><b>{obj.full_name}</b></div><div>{obj.contact_no}</div>'''
            )
        except Exception:
            return format_html(f'{obj.full_name}')
        
    name_with_contact.short_description = 'Contact Detail'
    
    def plan_end_date_with_days(self, obj):
        if obj.plan_end_date:
            formatted_date = obj.plan_end_date.strftime('%b. %d, %Y')
            remaining_days = obj.plan_remaining_days if obj.plan_remaining_days is not None else "N/A"
            return format_html(
                f'''<div><b>{formatted_date}</b></div><div>{remaining_days} days remaining</div>'''
            )
        return None
    plan_end_date_with_days.short_description = 'Plan End Date'
    

    def editable_offer(self, obj):
        offer = obj.additional_info.get('offer', '')
        offer_dropdown = ''.join(
            [f'<option value="{choice[0]}" {"selected" if choice[0] == offer else ""}>{choice[1]}</option>'
             for choice in User.offer_choices()]
        )
        return format_html(
            f'<select class="admin-editable" data-id="{obj.id}" data-field="offer">{offer_dropdown}</select>'
        )

    def editable_remarks(self, obj):
        remarks = obj.additional_info.get('remarks', '')
        remarks_dropdown = ''.join(
            [f'<option value="{choice[0]}" {"selected" if choice[0] == remarks else ""}>{choice[1]}</option>'
             for choice in User.remarks_choices()]
        )
        return format_html(
            f'<select class="admin-editable" data-id="{obj.id}" data-field="remarks">{remarks_dropdown}</select>'
        )

    def editable_description(self, obj):
        try:
            description = obj.additional_info.get('description', '')
            return format_html(f'<input type="textarea" value="{description}" class="admin-editable form-control" style="width:auto" data-id="{obj.id}" data-field="description">')
        except: 
            return

    def editable_follow_up_date(self, obj):
        follow_up_date = obj.additional_info.get('follow_up_date', '')
        return format_html(f'<input type="date" value="{follow_up_date}" class="admin-editable" data-id="{obj.id}" data-field="follow_up_date">')

    editable_offer.short_description = 'Offer'
    editable_remarks.short_description = 'Remarks'
    editable_description.short_description = 'Description'
    editable_follow_up_date.short_description = 'Follow-up Date'

    # actions
    def updated_by(self, obj):
        user_id = obj.additional_info.get('updated_by')
        if user_id:
            user = User.objects.filter(id=user_id).first()
            return user.full_name if user else 'N/A'
        return '-'


    def verify_email(modeladmin, request, queryset):
        for obj in queryset:
            user = User.objects.get(id=obj.id)
            if user:
                user.email_verification = True
                user.save()
        messages.add_message(request, messages.SUCCESS, 'Verified user email')
        return True
    
    def verify_user(modeladmin, request, queryset):
        if not request.user.is_superuser:
            return messages.add_message(request, messages.ERROR, 'You are not authorized to perform this action')
        
        for obj in queryset:
            user = User.objects.get(id=obj.id)
            if user:
                user.is_verified = True
                user.save()
        messages.add_message(request, messages.SUCCESS, 'Verified user account')
        return True
    
    def delete_selected(modeladmin, request, queryset):
        for obj in queryset:
            if default_storage.exists(str(obj.registration_certificate_front)):
                default_storage.delete(str(obj.registration_certificate_front))
            if default_storage.exists(str(obj.registration_certificate_back)):
                default_storage.delete(str(obj.registration_certificate_back))
            if default_storage.exists(str(obj.pan_vat_certificate)):
                default_storage.delete(str(obj.pan_vat_certificate))
            if default_storage.exists(str(obj.liscense_front)):
                default_storage.delete(str(obj.liscense_front))
            if default_storage.exists(str(obj.liscense_back)):
                default_storage.delete(str(obj.liscense_back))
            # obj.delete()
            return delete_selected(modeladmin, request, queryset)

    search_fields = ("email","contact_no", "first_name", "middle_name","last_name", "company_name")
    # For new added fields
    list_display = (
        'email_verified', 'name_with_contact', 'verified_user_role', 'plan_end_date_with_days', 'editable_offer', 'editable_remarks', 'editable_description', 'editable_follow_up_date', 'updated_by', 'update_button'
    )
    actions = ['delete_selected','verify_email', 'verify_user']
    list_filter=(PlanEndDateFilter, FollowUpDateFilter, PlanRemainingDaysFilter, RemarksFilter, DistrictFilter, ProjectCategoryFilter, SourceFilter, PlanFilter, RoleFilter, OfferFilter, UpdatedByFilter, EmailStatusFilter)


class Staff(User):
    class Meta:
        proxy = True

class StaffsAdmin(UserAdmin):
    
    change_list_template = None  
    
    def has_add_permission(self, request):
        return True
    
    def get_queryset(self, request):
         
       return self.model.objects.filter(is_staff = True, is_superuser=False)
    
    
    # Override the response_add method
    def response_change(self, request, obj, post_url_continue=None):
        # If "Save and add another" is clicked, treat it as "Save"
        if "_addanother" in request.POST:
            return HttpResponseRedirect(reverse('admin:User_staff_changelist'))
        return super().response_add(request, obj, post_url_continue)
     
    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.is_active = True
        if request.POST["new_password"]:
            obj.password = make_password(request.POST["new_password"])
        super().save_model(request, obj, form, change)
    
    list_display = ("email", "contact_no")
    list_filter =('groups',)
    fields=('first_name', 'middle_name', 'last_name','email','new_password','contact_no', 'groups') 

class Activity(UserActivity):
    class Meta:
        proxy = True
        verbose_name_plural = "User Activities"

class UserActivityAdmin(admin.ModelAdmin):
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export_activity/', self.admin_site.admin_view(self.export_activity_as_csv), name='app_model_export_activity'),
        ]
        return custom_urls + urls
    
    def export_activity_as_csv(self, request):
        """Export selected users as a CSV file."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_activity.csv"'

        writer = csv.writer(response)
        writer.writerow(['Email', 'Status', 'Contact no', 'Activity type'])  

        filters = {}
        for key, value in request.GET.items():
            if value:
                if key.lower() == 'status__exact':
                    try:
                        filters [f'status__exact'] = value
                    except ValueError:
                        continue
        users = UserActivity.objects.filter(**filters)

        for user in users:

            writer.writerow([
                user.email,
                user.status,
                user.contact_no,
                user.activity_type
            ])

        return response
    
    def has_add_permission(self, request):  
        return False
    
    def has_delete_permission(self, request, obj = None):
        return False

    def complete_pending_log(self, request, queryset):
        updated_count = queryset.filter(status="Pending").update(status="Completed")
        if updated_count:
            self.message_user(request, f"{updated_count} log marked as Completed.", level=messages.SUCCESS)
        else:
            self.message_user(request, "No Pending log found to mark as Completed.", level=messages.WARNING)

    def status_display(self, obj):
        badge_class = {
            "Pending": "badge-warning",
            "Completed": "badge-success"
        }.get(obj.status, "badge-secondary")
        return format_html(
            '<span class="badge {}" style="font-weight: bold; font-size: 13px;">{}</span>',
            badge_class,
            obj.status
        )
    
    status_display.short_description = "Status"

    list_display = ("email", "status_display", "contact_no","activity_type")
    list_filter = ('activity_type', 'status') 
    fields = ("email", "activity_type", "status")
    actions = ['complete_pending_log']
    
class RecoverUser(User):
    class Meta:
        proxy = True

class RecoverUserAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return self.model.objects.filter(is_deleted=True)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def recover_user(modeladmin, request, queryset):
        for obj in queryset:
            user = User.objects.get(id=obj.id)
            if user:
                user.is_deleted = False
                user.save()
        messages.add_message(request, messages.SUCCESS, 'Recover user successfull')
        return True

    list_display = ("email", "contact_no")
    search_fields = ("contact_no", "email")
    actions = ['recover_user']

class ProjectCategoryAdmin(admin.ModelAdmin):
    pass

class PlanAdmin(admin.ModelAdmin):
    pass

admin.site.register(User, UserAdmin)
admin.site.register(Staff, StaffsAdmin)
admin.site.register(Activity, UserActivityAdmin)
admin.site.register(RecoverUser, RecoverUserAdmin)
admin.site.register(ProjectCategory, ProjectCategoryAdmin)
admin.site.register(Plan, PlanAdmin)

admin.site.site_header = "Welcome back! 👋"
