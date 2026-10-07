from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import *
from .forms import *

# - Helper functions -
def get_crimes_by_category():
    """
    Groups UCRCrime objects by their ucr_category.

    Returns:
        dict: A dictionary where keys are UCRCategory objects (or the string
        'Uncategorized' for crimes without a category) and values are lists of
        UCRCrime objects.
        Example:
            {
                <UCRCategory: 01A:Murder>: [UCRCrime1, UCRCrime2],
                'Uncategorized': [UCRCrime3],
                ...
            }
    """
    crimes_by_category = {}
    # get all crimes in database, ordered by ucr_category
    for crime in UCRCrime.objects.all().order_by('ucr_category'):
        # if crime has a ucr_category, use the object as the key, otherwise use 'Uncategorized'
        category_key = crime.ucr_category if crime.ucr_category else 'Uncategorized'

        # add crime to the appropriate category list
        if category_key not in crimes_by_category:
            crimes_by_category[category_key] = []
        crimes_by_category[category_key].append(crime)
    return crimes_by_category

def get_districts_by_sectors():
    """
    Groups District objects by their sector.
    
    Returns:
        dict: A dictionary where keys are sector strings and values are lists of District objects.
        Example:
            {
                'Sector 1': [District1, District2],
                'Sector 2': [District3],
                ...
            }
    """
    districts_by_sector = {}
    # get all districts in database, ordered by sector
    for district in District.objects.all().order_by('sector'):
        # if district has a sector, use it as the key, otherwise use 'Uncategorized'
        if district.sector:
            sector_key = district.sector
        else:
            sector_key = 'Uncategorized'
        # add district to the appropriate sector list
        if sector_key not in districts_by_sector:
            districts_by_sector[sector_key] = []
        districts_by_sector[sector_key].append(district)
    return districts_by_sector

# - Views -

# -- Index View--

class IndexView(TemplateView):
    template_name = 'incidents/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        context['location_types'] = LocationType.objects.all()
        context['crimes_by_category'] = get_crimes_by_category()
        context['districts_by_sector'] = get_districts_by_sectors()
        return context


# -- List Incidents Views--

class BaseIncidentListView(ListView):
    model = Incident
    template_name = 'incidents/list.html'
    context_object_name = 'incidents'
    paginate_by = 25

    def get_ordering(self):
        return ['-occ_date', '-occ_time', 'pk']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        context['filtered_incidents_count'] = self.get_queryset().count()
        return context


class AllIncidentsListView(BaseIncidentListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'All'
        return context

class NoClearanceIncidentListView(BaseIncidentListView):
    def get_queryset(self):
        return Incident.objects.filter(clearance__clearance_date__isnull=True).order_by('-occ_date', '-occ_time', 'pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'No Clearance'
        return context


class FamilyViolenceAssaultIncidentListView(BaseIncidentListView):
    def get_queryset(self):
        return Incident.objects.filter(family_violence=True).filter(crimes__ucr_category__ucr_category='13A').order_by('-occ_date', '-occ_time', 'pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = 'Family Violence Aggravated Assault'
        return context

# lists accessed via detail pages

class LocationTypeIncidentListView(BaseIncidentListView):
    def get_queryset(self):
        self.location_type = get_object_or_404(LocationType, pk=self.kwargs['location_type_id'])
        return Incident.objects.filter(location_type=self.location_type).order_by('-occ_date', '-occ_time', 'pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = f'Location Type: {self.location_type}'
        context['location_type'] = self.location_type
        return context


class DistrictIncidentListView(BaseIncidentListView):
    def get_queryset(self):
        self.district = get_object_or_404(District, pk=self.kwargs['district_id'])
        return Incident.objects.filter(district=self.district).order_by('-occ_date', '-occ_time', 'pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = f'District: {self.district}'
        context['district'] = self.district
        return context


class SectorIncidentListView(BaseIncidentListView):
    def get_queryset(self):
        self.sector = get_object_or_404(Sector, pk=self.kwargs['sector_id'])
        return Incident.objects.filter(district__sector=self.sector).order_by('-occ_date', '-occ_time', 'pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = f'Sector: {self.sector}'
        context['sector'] = self.sector
        return context

class UCRCategoryIncidentListView(BaseIncidentListView):
    def get_queryset(self):
        self.ucr_category = get_object_or_404(UCRCategory, pk=self.kwargs['ucr_category_id'])
        return Incident.objects.filter(crimes__ucr_category=self.ucr_category).distinct().order_by('-occ_date', '-occ_time', 'pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = f'UCR Category: {self.ucr_category}'
        context['ucr_category'] = self.ucr_category
        return context

# -- Incident Veiws --
class IncidentDetail(DetailView):
    model = Incident
    template_name = 'incidents/content/incident/detail_incident.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sidebar
        # - Master Incidents for link to list/all_incidents and total count
        # - Top 25 incidents for sidebar
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        context['incident_location_type'] = {
            'pk': self.object.location_type.pk if self.object.location_type else None,
            'description': self.object.get_location_type_description(),
        }
        context['incident_district'] = {
            'pk': self.object.district.pk if self.object.district else None,
            'name': self.object.district,
        }
        return context

class CreateIncident(CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incidents/content/incident/create_incident.html'

    def get_initial(self):
        """
        Set default values for the form 
        date and time fields to the current date and time.
        """
        initial = super().get_initial()
        now = timezone.now()
        initial['occ_date'] = now.date()
        initial['occ_time'] = now.time()
        initial['rep_date'] = now.date()
        initial['rep_time'] = now.time()
        return initial

    def form_invalid(self, form):
        clearance_form = ClearanceForm(self.request.POST)
        return self.render_to_response(self.get_context_data(
            form=form,
            clearance_form=clearance_form,
        ))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sidebar
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()

        # Next incident number for display
        last_incident = Incident.objects.order_by('-incident_number').first()
        context['last_incident_number'] = last_incident.incident_number if last_incident else 0
        context['next_incident_number'] = context['last_incident_number'] + 1

        # Current date/time for display
        now = timezone.now()
        context['current_date'] = now.date()
        context['current_time'] = now.time()

        # Clearance form (pre-populate with NOT_CLEARED and today's date)
        if 'clearance_form' not in context:
            context['clearance_form'] = ClearanceForm(initial={
                'clearance_status': Clearance.Status.NOT_CLEARED,
            })

        # Crimes grouped by category for checkbox rendering
        context['crimes_by_category'] = get_crimes_by_category()

        return context

    def form_valid(self, form):
        clearance_form = ClearanceForm(self.request.POST)
        if not clearance_form.is_valid():
            return self.form_invalid(form)

        last_incident = Incident.objects.order_by('-incident_number').first()
        next_incident_number = (last_incident.incident_number + 1) if last_incident else 1

        incident = form.save(commit=False)
        incident.incident_number = next_incident_number
        incident.save()

        # Create Clearance record using submitted form values
        clearance = clearance_form.save(commit=False)
        clearance.incident = incident
        clearance.last_updated = timezone.now()
        clearance.save()

        # Create crime links for many-to-many relationship
        for crime in form.cleaned_data['crimes']:
            IncidentCrimeLink.objects.create(incident=incident, crime=crime)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return "/"

class UpdateIncident(UpdateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incidents/content/incident/update_incident.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Sidebar
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()

        # Crimes grouped by category for checkbox rendering
        context['crimes_by_category'] = get_crimes_by_category()

        # IDs of currently linked crimes to mark checkboxes as selected
        context['selected_crime_ids'] = set(
            self.object.crimes.values_list('pk', flat=True)
        )

        return context

    def form_valid(self, form):
        incident = form.save()

        # Rebuild crime links for many-to-many relationship
        IncidentCrimeLink.objects.filter(incident=incident).delete()
        for crime in form.cleaned_data['crimes']:
            IncidentCrimeLink.objects.create(incident=incident, crime=crime)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return f"/incident/{self.object.pk}/"

class DeleteIncident(DeleteView):
    model = Incident
    template_name = 'incidents/confirm_object_delete.html'
    success_url = "/"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Delete related records manually because IncidentCrimeLink uses DO_NOTHING
        IncidentCrimeLink.objects.filter(incident=self.object).delete()
        Clearance.objects.filter(incident=self.object).delete()
        return super().delete(request, *args, **kwargs)

    # After successful deletion, redirect to home page
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        context['cancel_url'] = f"/incident/{self.object.pk}/"
        return context

# -- Location Type --
class CreateLocationType(CreateView):
    model = LocationType
    form_class = LocationTypeForm
    template_name = 'incidents/content/location_type/create_location_type.html'
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        last_location_type = LocationType.objects.order_by('-pk').first()
        context['next_location_type'] = (last_location_type.pk + 1) if last_location_type else 1
        return context

class DetailLocationType(DetailView):
    model = LocationType
    template_name = 'incidents/content/location_type/detail_location_type.html'
    context_object_name = 'location_type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        context['count'] = Incident.objects.filter(location_type=self.object).count()
        return context

class UpdateLocationType(UpdateView):
    model = LocationType
    form_class = LocationTypeForm
    template_name = 'incidents/content/location_type/update_location_type.html'
    context_object_name = 'location_type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        return context

    def get_success_url(self):
        return f"/location_type/{self.object.pk}/"


class DeleteLocationType(DeleteView):
    model = LocationType
    template_name = 'incidents/confirm_object_delete.html'
    success_url = '/'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Delete all incidents that reference this location type
        incidents_to_delete = Incident.objects.filter(location_type=self.object)
        for incident in incidents_to_delete:
            IncidentCrimeLink.objects.filter(incident=incident).delete()
            Clearance.objects.filter(incident=incident).delete()
            incident.delete()
        self.object.delete()
        return HttpResponseRedirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        context['cancel_url'] = f"/location_type/{self.object.pk}/"
        return context

# -- Clearance --

class ClearanceDetailView(DetailView):
    model = Clearance
    template_name = 'incidents/content/clearance/detail_clearance.html'
    context_object_name = 'clearance'

    def get_object(self, queryset=None):
        return get_object_or_404(Clearance, pk=self.request.GET.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clearance = self.object
        incident = clearance.incident
        context['incident'] = incident
        context['incident_location_type'] = {
            'pk': incident.location_type.pk if incident.location_type else None,
            'description': incident.get_location_type_description(),
        }
        context['incident_district'] = {
            'pk': incident.district.pk if incident.district else None,
            'name': incident.district,
        }
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        return context


class UpdateClearance(UpdateView):
    model = Clearance
    form_class = ClearanceForm
    template_name = 'incidents/content/clearance/update_clearance.html'
    context_object_name = 'clearance'

    def get_object(self, queryset=None):
        return get_object_or_404(Clearance, pk=self.request.GET.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incident'] = self.object.incident
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        return context

    def form_valid(self, form):
        clearance = form.save(commit=False)
        clearance.last_updated = timezone.now()
        clearance.save()
        return HttpResponseRedirect(f'/clearance_detail/?pk={clearance.pk}')


# -- Sectors --

class SectorDetailView(DetailView):
    model = Sector
    template_name = 'incidents/content/sectors/detail_sector.html'
    context_object_name = 'sector'

    def get_object(self, queryset=None):
        return get_object_or_404(Sector, pk=self.request.GET.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector = self.object
        context['districts'] = sector.districts.all()
        context['count'] = Incident.objects.filter(district__sector=sector).count()
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        return context


class DistrictDetailView(DetailView):
    model = District
    template_name = 'incidents/content/district/detail_district.html'
    context_object_name = 'district'

    def get_object(self, queryset=None):
        return get_object_or_404(District, pk=self.request.GET.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        district = self.object
        context['count'] = Incident.objects.filter(district=district).count()
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        return context


# -- UCR Categories --

class UCRCategoryDetailView(DetailView):
    model = UCRCategory
    template_name = 'incidents/content/ucr/detail_ucr_category.html'
    context_object_name = 'ucr_category'

    def get_object(self, queryset=None):
        return get_object_or_404(UCRCategory, pk=self.request.GET.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ucr_category = self.object
        context['count'] = Incident.objects.filter(crimes__ucr_category=ucr_category).distinct().count()
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        return context

class UCRCrimeDetailView(DetailView):
    model = UCRCrime
    template_name = 'incidents/content/ucr/detail_ucr_crime.html'
    context_object_name = 'ucr_crime'

    def get_object(self, queryset=None):
        return get_object_or_404(UCRCrime, pk=self.request.GET.get('pk'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ucr_crime = self.object
        context['count'] = Incident.objects.filter(crimes=ucr_crime).distinct().count()
        context['sidebar_incidents'] = Incident.objects.order_by('-occ_date', '-occ_time', 'pk')[:25]
        context['incidents_count'] = Incident.objects.count()
        return context


class UCRCrimeIncidentListView(BaseIncidentListView):
    def get_queryset(self):
        self.ucr_crime = get_object_or_404(UCRCrime, pk=self.kwargs['ucr_crime_id'])
        return Incident.objects.filter(crimes=self.ucr_crime).distinct().order_by('-occ_date', '-occ_time', 'pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type'] = f'UCR Crime: {self.ucr_crime}'
        context['ucr_crime'] = self.ucr_crime
        return context
