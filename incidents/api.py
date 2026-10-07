from rest_framework import generics, mixins, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Incident, IncidentCrimeLink, Clearance, LocationType, UCRCategory
from .serializers import IncidentSerializer


class IncidentList(generics.ListAPIView):
    """Return a paginated list of all incidents."""
    queryset = Incident.objects.all().order_by('incident_number')
    serializer_class = IncidentSerializer
    pagination_class = PageNumberPagination


class IncidentDetail(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     generics.GenericAPIView):
    """Retrieve (GET), create (POST), update (PUT), or delete (DELETE) a single incident."""
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        incident = self.get_object()
        # Delete related records first to avoid foreign key constraint errors
        IncidentCrimeLink.objects.filter(incident=incident).delete()
        Clearance.objects.filter(incident=incident).delete()
        return self.destroy(request, *args, **kwargs)


class IncidentFamilyViolenceAssaultList(generics.ListAPIView):
    """Return incidents flagged as family violence with UCR aggravated assault category (13A)."""
    serializer_class = IncidentSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Incident.objects.filter(
            family_violence=True,
            crimes__ucr_category__ucr_category='13A'
        ).distinct().order_by('-occ_date', '-occ_time', 'pk')


class IncidentNoClearanceList(generics.ListAPIView):
    """Return incidents that have not been cleared (clearance_date is null)."""
    serializer_class = IncidentSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Incident.objects.filter(
            clearance__clearance_date__isnull=True
        ).order_by('-occ_date', '-occ_time', 'pk')


class IncidentByLocationTypeList(generics.ListAPIView):
    """Return incidents for a given location type pk."""
    serializer_class = IncidentSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        location_type = get_object_or_404(LocationType, pk=self.kwargs['location_type_id'])
        return Incident.objects.filter(
            location_type=location_type
        ).order_by('-occ_date', '-occ_time', 'pk')


class IncidentByUCRCategoryList(generics.ListAPIView):
    """Return incidents linked to a given UCR crime category pk."""
    serializer_class = IncidentSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        ucr_category = get_object_or_404(UCRCategory, pk=self.kwargs['ucr_category_id'])
        return Incident.objects.filter(
            crimes__ucr_category=ucr_category
        ).distinct().order_by('-occ_date', '-occ_time', 'pk')