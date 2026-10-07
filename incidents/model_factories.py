import factory
from .models import *

class LocationTypeFactory(factory.django.DjangoModelFactory):
    location_type = "RESIDENCE / HOME"

    class Meta:
        model = LocationType
        django_get_or_create = ('location_type',)


class CouncilDistrictFactory(factory.django.DjangoModelFactory):
    council_district = 1

    class Meta:
        model = CouncilDistrict
        django_get_or_create = ('council_district',)


class CensusBlockGroupFactory(factory.django.DjangoModelFactory):
    census_block_group = 4530406001

    class Meta:
        model = CensusBlockGroup
        django_get_or_create = ('census_block_group',)


class SectorFactory(factory.django.DjangoModelFactory):
    name = Sector.Name.ADAM

    class Meta:
        model = Sector
        django_get_or_create = ('name',)


class DistrictFactory(factory.django.DjangoModelFactory):
    sector = factory.SubFactory(SectorFactory)
    number = 1

    class Meta:
        model = District
        django_get_or_create = ('sector', 'number')


class UCRCategoryFactory(factory.django.DjangoModelFactory):
    ucr_category = "13A"
    category_description = "Aggravated Assault"

    class Meta:
        model = UCRCategory
        django_get_or_create = ('ucr_category', 'category_description')


class UCRCrimeFactory(factory.django.DjangoModelFactory):
    crime_code = 1300
    crime_type = "AGG ASSAULT"
    ucr_category = factory.SubFactory(UCRCategoryFactory)

    class Meta:
        model = UCRCrime
        django_get_or_create = ('crime_code', 'crime_type')


class IncidentFactory(factory.django.DjangoModelFactory):
    incident_number = 20260001
    family_violence = False
    occ_date = "2026-01-01"
    occ_time = "12:00:00"
    rep_date = "2026-01-01"
    rep_time = "13:00:00"
    location_type = factory.SubFactory(LocationTypeFactory)
    council_district = factory.SubFactory(CouncilDistrictFactory)
    census_block_group = factory.SubFactory(CensusBlockGroupFactory)
    district = factory.SubFactory(DistrictFactory)

    class Meta:
        model = Incident


class ClearanceFactory(factory.django.DjangoModelFactory):
    incident = factory.SubFactory(IncidentFactory)
    clearance_status = Clearance.Status.NOT_CLEARED
    clearance_date = None
    last_updated = None

    class Meta:
        model = Clearance
