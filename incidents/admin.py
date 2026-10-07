from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register([
    CensusBlockGroup, 
    CouncilDistrict, 
    District, 
    LocationType, 
    Sector,
    UCRCategory, 
    UCRCrime, 
    Incident, 
    Clearance,
    IncidentCrimeLink

])
