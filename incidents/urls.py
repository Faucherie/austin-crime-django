from django.urls import path
from . import views
from . import api

urlpatterns = [
    # - Index -
    path('', views.IndexView.as_view(), name='index'),
    
    # - List Incidents -
    path('list/', views.AllIncidentsListView.as_view(), name='list'),
    path('list/location_type/<int:location_type_id>/', views.LocationTypeIncidentListView.as_view(), name='list_by_location_type'),
    path('list/district/<int:district_id>/', views.DistrictIncidentListView.as_view(), name='list_by_district'),
    path('list/sector/<int:sector_id>/', views.SectorIncidentListView.as_view(), name='list_by_sector'),
    path('list/no_clearance/', views.NoClearanceIncidentListView.as_view(), name='no_clearance'),
    path('list/family_violence_assault/', views.FamilyViolenceAssaultIncidentListView.as_view(), name='family_violence_assault'),
    path('list/ucr_category/<int:ucr_category_id>/', views.UCRCategoryIncidentListView.as_view(), name='list_by_ucr_category'),
    path('list/ucr_crime/<int:ucr_crime_id>/', views.UCRCrimeIncidentListView.as_view(), name='list_by_ucr_crime'),
    
    # - Incident -
    path('create_incident/', views.CreateIncident.as_view(), name='create_incident'),
    path('incident/<int:pk>/', views.IncidentDetail.as_view(), name='incident_detail'),
    path('incident/<int:pk>/update/', views.UpdateIncident.as_view(), name='update_incident'),
    path('delete/<int:pk>/', views.DeleteIncident.as_view(), name='delete_incident'),

    # - Location Type -
    path('create_location_type/', views.CreateLocationType.as_view(), name='create_location_type'),
    path('location_type/<int:pk>/', views.DetailLocationType.as_view(), name='location_type_detail'),
    path('update_location_type/<int:pk>/', views.UpdateLocationType.as_view(), name='update_location_type'),
    path('delete_location_type/<int:pk>/', views.DeleteLocationType.as_view(), name='delete_location_type'),
    
    # - Clearance -
    path('clearance_detail/', views.ClearanceDetailView.as_view(), name='clearance_detail'),
    path('update_clearance/', views.UpdateClearance.as_view(), name='update_clearance'),
    
    # - Sector -
    path('detail_sector/', views.SectorDetailView.as_view(), name='detail_sector'),
    
    # - District -
    path('detail_district/', views.DistrictDetailView.as_view(), name='detail_district'),
    
    # - UCR Categories -
    path('detail_ucr_category/', views.UCRCategoryDetailView.as_view(), name='detail_ucr_category'),
    
    # - UCR Crimes -
    path('detail_ucr_crime/', views.UCRCrimeDetailView.as_view(), name='detail_ucr_crime'),
    
    # - API -
    path('api/incident/<int:pk>/', api.IncidentDetail.as_view(), name='api_incident_detail'),
    path('api/incidents', api.IncidentList.as_view(), name='api_incidents_list'),
    path('api/incidents/family_violence_assault/', api.IncidentFamilyViolenceAssaultList.as_view(), name='api_incidents_family_violence_assault'),
    path('api/incidents/no_clearance/', api.IncidentNoClearanceList.as_view(), name='api_incidents_no_clearance'),
    path('api/incidents/location_type/<int:location_type_id>/', api.IncidentByLocationTypeList.as_view(), name='api_incidents_by_location_type'),
    path('api/incidents/ucr_category/<int:ucr_category_id>/', api.IncidentByUCRCategoryList.as_view(), name='api_incidents_by_ucr_category'),
]