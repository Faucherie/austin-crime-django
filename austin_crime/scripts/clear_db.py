import os
import sys
import django

# -- Initialization --

sys.path.append('/home/scott-swanson/University_of_London/CM3035_advanced_web_development/Midterm/PROJECT/austin_crime')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'austin_crime.settings')
django.setup()

from incidents.models import (
    IncidentCrimeLink, Clearance, Incident, UCRCrime, UCRCategory,
    District, Sector, CouncilDistrict, LocationType, CensusBlockGroup
)

def clear_incident_data():
    """Clear all incident-related data while preserving admin user and other data."""
    print("Clearing incident data...")

    # Delete in correct order to respect FK constraints
    IncidentCrimeLink.objects.all().delete()
    print("  Deleted IncidentCrimeLink records")

    Clearance.objects.all().delete()
    print("  Deleted Clearance records")

    Incident.objects.all().delete()
    print("  Deleted Incident records")

    UCRCrime.objects.all().delete()
    print("  Deleted UCRCrime records")

    UCRCategory.objects.all().delete()
    print("  Deleted UCRCategory records")

    District.objects.all().delete()
    print("  Deleted District records")

    Sector.objects.all().delete()
    print("  Deleted Sector records")

    CouncilDistrict.objects.all().delete()
    print("  Deleted CouncilDistrict records")

    LocationType.objects.all().delete()
    print("  Deleted LocationType records")

    CensusBlockGroup.objects.all().delete()
    print("  Deleted CensusBlockGroup records")

    print("\n Incident data cleared - admin user preserved!")

if __name__ == '__main__':
    clear_incident_data()
