from rest_framework import serializers
from .models import (
    Incident, LocationType, CouncilDistrict, CensusBlockGroup,
    District, UCRCrime, UCRCategory, IncidentCrimeLink, Clearance
)

class LocationTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField()

class CouncilDistrictSerializer(serializers.Serializer):
    council_district = serializers.IntegerField()

class CensusBlockGroupSerializer(serializers.Serializer):
    census_block_group = serializers.IntegerField()

class DistrictSerializer(serializers.Serializer):
    id = serializers.IntegerField()


class UCRCrimeSerializer(serializers.ModelSerializer):
    ucr_category = serializers.StringRelatedField()

    class Meta:
        model = UCRCrime
        fields = ['id', 'crime_code', 'crime_type', 'ucr_category']


class ClearanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clearance
        fields = ['clearance_status', 'clearance_date', 'last_updated']


class IncidentSerializer(serializers.ModelSerializer):
    incident_number = serializers.IntegerField(read_only=True)
    location_type = LocationTypeSerializer(required=False, allow_null=True)
    council_district = CouncilDistrictSerializer(required=False, allow_null=True)
    census_block_group = CensusBlockGroupSerializer(required=False, allow_null=True)
    district = DistrictSerializer(required=False, allow_null=True)
    crimes = UCRCrimeSerializer(many=True, required=False)
    clearance = ClearanceSerializer(required=False, allow_null=True)

    class Meta:
        model = Incident
        fields = [
            'incident_number',
            'family_violence',
            'occ_date',
            'occ_time',
            'rep_date',
            'rep_time',
            'location_type',
            'council_district',
            'census_block_group',
            'district',
            'crimes',
            'clearance',
        ]

    def validate(self, data):
        # Verify FK lookup values exist - only if provided
        lt = data.get('location_type')
        if lt and not LocationType.objects.filter(id=lt['id']).exists():
            raise serializers.ValidationError({'location_type': f"LocationType id={lt['id']} does not exist."})

        cd = data.get('council_district')
        if cd and not CouncilDistrict.objects.filter(council_district=cd['council_district']).exists():
            raise serializers.ValidationError({'council_district': f"CouncilDistrict {cd['council_district']} does not exist."})

        cbg = data.get('census_block_group')
        if cbg and not CensusBlockGroup.objects.filter(census_block_group=cbg['census_block_group']).exists():
            raise serializers.ValidationError({'census_block_group': f"CensusBlockGroup {cbg['census_block_group']} does not exist."})

        d = data.get('district')
        if d and not District.objects.filter(id=d['id']).exists():
            raise serializers.ValidationError({'district': f"District id={d['id']} does not exist."})

        for crime in data.get('crimes', []):
            if not UCRCrime.objects.filter(id=crime['id']).exists():
                raise serializers.ValidationError({'crimes': f"UCRCrime id={crime['id']} does not exist."})

        return data

    def create(self, validated_data):
        # Auto-generate incident_number (mirrors CreateIncident.form_valid in views.py)
        last = Incident.objects.order_by('-incident_number').first()
        validated_data['incident_number'] = (last.incident_number + 1) if last else 1

        # Extract nested data
        location_type_data = validated_data.pop('location_type', None)
        council_district_data = validated_data.pop('council_district', None)
        census_block_group_data = validated_data.pop('census_block_group', None)
        district_data = validated_data.pop('district', None)
        crimes_data = validated_data.pop('crimes', [])
        clearance_data = validated_data.pop('clearance', None)

        # Create main Incident object with scalar fields
        incident = Incident(**validated_data)

        # Resolve foreign keys - only if provided
        if location_type_data:
            incident.location_type = LocationType.objects.get(id=location_type_data['id'])

        if council_district_data:
            incident.council_district = CouncilDistrict.objects.get(
                council_district=council_district_data['council_district']
            )

        if census_block_group_data:
            incident.census_block_group = CensusBlockGroup.objects.get(
                census_block_group=census_block_group_data['census_block_group']
            )

        if district_data:
            incident.district = District.objects.get(id=district_data['id'])

        incident.save()

        # Handle many-to-many relationship
        for crime_data in crimes_data:
            crime = UCRCrime.objects.get(id=crime_data['id'])
            IncidentCrimeLink.objects.create(incident=incident, crime=crime)

        # Always create a Clearance record - use provided data or default to NOT_CLEARED
        if clearance_data:
            Clearance.objects.create(incident=incident, **clearance_data)
        else:
            Clearance.objects.create(
                incident=incident,
                clearance_status=Clearance.Status.NOT_CLEARED,
                clearance_date=None,
                last_updated=None,
            )

        return incident

    def update(self, instance, validated_data):
        # Extract nested data
        location_type_data = validated_data.pop('location_type', None)
        council_district_data = validated_data.pop('council_district', None)
        census_block_group_data = validated_data.pop('census_block_group', None)
        district_data = validated_data.pop('district', None)
        crimes_data = validated_data.pop('crimes', None)
        clearance_data = validated_data.pop('clearance', None)

        # Update scalar fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Resolve foreign keys - only if provided in payload
        if location_type_data is not None:
            instance.location_type = LocationType.objects.get(id=location_type_data['id']) if location_type_data else None

        if council_district_data is not None:
            instance.council_district = CouncilDistrict.objects.get(
                council_district=council_district_data['council_district']
            ) if council_district_data else None

        if census_block_group_data is not None:
            instance.census_block_group = CensusBlockGroup.objects.get(
                census_block_group=census_block_group_data['census_block_group']
            ) if census_block_group_data else None

        if district_data is not None:
            instance.district = District.objects.get(id=district_data['id']) if district_data else None

        instance.save()

        # Rebuild crime links if crimes were provided
        if crimes_data is not None:
            IncidentCrimeLink.objects.filter(incident=instance).delete()
            for crime_data in crimes_data:
                crime = UCRCrime.objects.get(id=crime_data['id'])
                IncidentCrimeLink.objects.create(incident=instance, crime=crime)

        # Update existing Clearance record if provided
        if clearance_data is not None:
            Clearance.objects.filter(incident=instance).update(**clearance_data)

        return instance