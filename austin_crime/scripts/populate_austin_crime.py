import os
import sys
import django
import csv
from collections import defaultdict
from datetime import datetime, time

# -- Initialization --

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'austin_crime.settings')
django.setup()

from incidents.models import (
    LocationType, CouncilDistrict, CensusBlockGroup, Sector, District, UCRCategory,
    UCRCrime, Incident, IncidentCrimeLink, Clearance
)

# Sector code mapping
SECTOR_CODE_TO_NAME = {
    'AD': 'AD', 'AI': 'AI', 'BA': 'BA', 'CH': 'CH', 'DA': 'DA',
    'ED': 'ED', 'FR': 'FR', 'GE': 'GE', 'HE': 'HE', 'ID': 'ID',
}

# -- Helper Functions --

def parse_time(time_str):
    """Convert HHMM format to time object."""
    if not time_str or time_str.strip() == '':
        return time(0, 0)
    try:
        time_int = int(time_str)
        return time(time_int // 100, time_int % 100)
    except (ValueError, TypeError):
        return time(0, 0)

def parse_date(date_str):
    """Convert MM/DD/YYYY format to date object."""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%m/%d/%Y').date()
    except ValueError:
        return None

def parse_csv(data_file):
    """Parse CSV file and return parsed incident data and reference collections."""
    incidents = {}
    location_types = set()
    council_districts = set()
    sectors = set()
    districts = defaultdict(set)
    ucr_categories = {}
    ucr_crimes = {}
    census_block_groups = set()

    print("Parsing CSV file...")
    with open(data_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        csv_reader.__next__()  # Skip header

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Skip rows with non-numeric district values
                if row[13].strip() and not row[13].strip().isdigit():
                    continue

                # Parse basic fields
                incident_number = int(row[0])
                crime_desc = row[1].strip()
                crime_code = int(row[2])
                family_violence = row[3].strip().upper() == 'Y'
                occ_date = parse_date(row[5])
                occ_time = parse_time(row[6])
                rep_date = parse_date(row[8])
                rep_time = parse_time(row[9])
                location_type = row[10].strip()
                council_district = int(row[11]) if row[11].strip() else None
                sector_code = row[12].strip()
                district_num = int(row[13]) if row[13].strip() else None
                clearance_status = row[14].strip() if row[14].strip() else 'N'
                clearance_date_str = row[15].strip()
                ucr_category_code = row[16].strip()
                ucr_category_desc = row[17].strip()
                census_block_group = int(row[18]) if row[18].strip() else None

                # Collect reference data
                if location_type:
                    location_types.add(location_type)
                if council_district:
                    council_districts.add(council_district)
                if sector_code and sector_code in SECTOR_CODE_TO_NAME:
                    sectors.add(sector_code)
                    if district_num:
                        districts[sector_code].add(district_num)
                if census_block_group:
                    census_block_groups.add(census_block_group)
                if ucr_category_code:
                    ucr_categories[ucr_category_code] = ucr_category_desc

                # Store crime and incident data
                ucr_crimes[(crime_code, crime_desc)] = ucr_category_code
                incidents[incident_number] = {
                    'crime_code': crime_code, 'crime_desc': crime_desc,
                    'family_violence': family_violence,
                    'occ_date': occ_date, 'occ_time': occ_time,
                    'rep_date': rep_date, 'rep_time': rep_time,
                    'location_type': location_type, 'council_district': council_district,
                    'sector_code': sector_code, 'district_num': district_num,
                    'clearance_status': clearance_status,
                    'clearance_date': parse_date(clearance_date_str) if clearance_date_str else None,
                    'census_block_group': census_block_group,
                }
            except (ValueError, IndexError) as e:
                print(f"Warning: Error parsing row {row_num}: {e}")
                continue

    print(f"Parsed {len(incidents)} incidents")
    return incidents, location_types, council_districts, sectors, districts, ucr_categories, ucr_crimes, census_block_groups

def clear_database():
    """Clear all existing data from database."""
    print("Clearing existing data...")
    IncidentCrimeLink.objects.all().delete()
    Clearance.objects.all().delete()
    Incident.objects.all().delete()
    UCRCrime.objects.all().delete()
    UCRCategory.objects.all().delete()
    District.objects.all().delete()
    Sector.objects.all().delete()
    CouncilDistrict.objects.all().delete()
    LocationType.objects.all().delete()
    CensusBlockGroup.objects.all().delete()

def create_reference_data(location_types, council_districts, sectors, districts,
                         ucr_categories, ucr_crimes, census_block_groups):
    """Create all reference tables and return FK mappings."""
    print("Creating reference data...")

    # LocationTypes
    location_type_rows = {}
    for loc_type in location_types:
        row = LocationType.objects.create(location_type=loc_type)
        location_type_rows[loc_type] = row
    print(f"  Created {len(location_type_rows)} LocationTypes")

    # CouncilDistricts
    council_district_rows = {}
    for council_dist in council_districts:
        row = CouncilDistrict.objects.create(council_district=council_dist)
        council_district_rows[council_dist] = row
    print(f"  Created {len(council_district_rows)} CouncilDistricts")

    # CensusBlockGroups
    census_block_group_rows = {}
    for census_group in census_block_groups:
        row = CensusBlockGroup.objects.create(census_block_group=census_group)
        census_block_group_rows[census_group] = row
    print(f"  Created {len(census_block_group_rows)} CensusBlockGroups")

    # Sectors and Districts
    sector_rows = {}
    district_rows = {}
    for sector_code in sectors:
        if sector_code in SECTOR_CODE_TO_NAME:
            try:
                row = Sector.objects.create(name=SECTOR_CODE_TO_NAME[sector_code])
                sector_rows[sector_code] = row
                for district_num in districts[sector_code]:
                    dist_row = District.objects.create(sector=row, number=district_num)
                    district_rows[(sector_code, district_num)] = dist_row
            except Exception as e:
                print(f"  Warning: Could not create sector {sector_code}: {e}")
    print(f"  Created {len(sector_rows)} Sectors and {len(district_rows)} Districts")

    # UCRCategories
    ucr_category_rows = {}
    for ucr_code, ucr_desc in ucr_categories.items():
        try:
            row = UCRCategory.objects.create(ucr_category=ucr_code, category_description=ucr_desc)
            ucr_category_rows[ucr_code] = row
        except Exception as e:
            print(f"  Warning: Could not create UCRCategory {ucr_code}: {e}")
    print(f"  Created {len(ucr_category_rows)} UCRCategories")

    # UCRCrimes
    ucr_crime_rows = {}
    for (crime_code, crime_desc), ucr_code in ucr_crimes.items():
        try:
            ucr_fk = ucr_category_rows.get(ucr_code) if ucr_code else None
            if ucr_code and ucr_code not in ucr_category_rows:
                print(f"  Warning: UCR code '{ucr_code}' not found for crime ({crime_code}, {crime_desc})")
            row = UCRCrime.objects.create(crime_code=crime_code, crime_type=crime_desc, ucr_category=ucr_fk)
            ucr_crime_rows[(crime_code, crime_desc)] = row
        except Exception as e:
            print(f"  Warning: Could not create UCRCrime ({crime_code}, {crime_desc}): {e}")
    print(f"  Created {len(ucr_crime_rows)} UCRCrimes")

    return (location_type_rows, council_district_rows, sector_rows, district_rows,
            census_block_group_rows, ucr_category_rows, ucr_crime_rows)

def create_incidents_and_clearances(incidents, location_type_rows, council_district_rows,
                                   sector_rows, district_rows, census_block_group_rows, ucr_crime_rows):
    """Create Incident records, links, and Clearance records."""
    print("Creating Incidents and Clearances...")
    incident_rows = {}
    clearance_count = 0
    error_count = 0

    for incident_number, incident_data in incidents.items():
        try:
            # Get foreign key references
            location_type_fk = location_type_rows.get(incident_data['location_type']) if incident_data['location_type'] else None
            council_district_fk = council_district_rows.get(incident_data['council_district']) if incident_data['council_district'] else None
            census_block_group_fk = census_block_group_rows.get(incident_data['census_block_group']) if incident_data['census_block_group'] else None

            # Get district FK
            district_fk = None
            if incident_data['sector_code'] and incident_data['district_num']:
                district_fk = district_rows.get((incident_data['sector_code'], incident_data['district_num']))

            # Create Incident
            incident_row = Incident.objects.create(
                incident_number=incident_number,
                family_violence=incident_data['family_violence'],
                occ_date=incident_data['occ_date'],
                occ_time=incident_data['occ_time'],
                rep_date=incident_data['rep_date'],
                rep_time=incident_data['rep_time'],
                location_type=location_type_fk,
                council_district=council_district_fk,
                census_block_group=census_block_group_fk,
                district=district_fk
            )
            incident_rows[incident_number] = incident_row

            # Link crime to incident
            crime_key = (incident_data['crime_code'], incident_data['crime_desc'])
            if crime_key in ucr_crime_rows:
                IncidentCrimeLink.objects.create(incident=incident_row, crime=ucr_crime_rows[crime_key])

            # Create Clearance record
            if incident_data['clearance_status']:
                Clearance.objects.create(
                    incident=incident_row,
                    clearance_status=incident_data['clearance_status'],
                    clearance_date=incident_data['clearance_date']
                )
                clearance_count += 1

        except Exception as e:
            error_count += 1
            if error_count <= 10:  # Print first 10 errors
                print(f"  Warning: Could not create Incident {incident_number}: {e}")
            elif error_count == 11:
                print(f"  ... and {len(incidents) - 10} more errors (suppressed)")

    print(f"  Created {len(incident_rows)} Incidents and {clearance_count} Clearances")
    if error_count > 0:
        print(f"  {error_count} errors encountered during incident creation")
    return incident_rows

def main(data_file):
    """Main execution flow."""
    # Parse CSV
    incidents, location_types, council_districts, sectors, districts, ucr_categories, ucr_crimes, census_block_groups = parse_csv(data_file)

    # Clear existing data
    clear_database()

    # Create reference data
    create_reference_data(location_types, council_districts, sectors, districts,
                         ucr_categories, ucr_crimes, census_block_groups)

    # Create FK mappings for reference data (need to re-fetch for incidents)
    location_type_rows = {lt.location_type: lt for lt in LocationType.objects.all()}
    council_district_rows = {cd.council_district: cd for cd in CouncilDistrict.objects.all()}
    sector_rows = {s.name: s for s in Sector.objects.all()}
    district_rows = {(d.sector.name, d.number): d for d in District.objects.all()}
    census_block_group_rows = {cbg.census_block_group: cbg for cbg in CensusBlockGroup.objects.all()}
    ucr_crime_rows = {(uc.crime_code, uc.crime_type): uc for uc in UCRCrime.objects.all()}

    # Create incidents
    create_incidents_and_clearances(incidents, location_type_rows, council_district_rows,
                                   sector_rows, district_rows, census_block_group_rows, ucr_crime_rows)

    print("\nDatabase population complete!")

if __name__ == '__main__':
    data_file = os.path.join(PROJECT_ROOT, 'data', 'Crime_Reports_sample.csv')
    main(data_file)
