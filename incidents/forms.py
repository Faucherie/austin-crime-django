from django import forms
from .models import Incident, UCRCrime, LocationType, Clearance

# Form for creating a new incident
class IncidentForm(forms.ModelForm):
    crimes = forms.ModelMultipleChoiceField(queryset=UCRCrime.objects.all().order_by('ucr_category'), label='Crimes', widget=forms.CheckboxSelectMultiple, required=False)
    
    class Meta:
        model = Incident
        fields = ['family_violence', 'occ_date', 'occ_time', 'rep_date', 'rep_time', 
                  'location_type', 'council_district', 'census_block_group', 'district']
        widgets = {
            'family_violence': forms.CheckboxInput(),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        occ_date = cleaned_data.get("occ_date")
        occ_time = cleaned_data.get("occ_time")
        rep_date = cleaned_data.get("rep_date")
        rep_time = cleaned_data.get("rep_time")
        
        # Validate that occurrence date/time is before or equal to report date/time
        if occ_date and rep_date:
            if occ_date > rep_date:
                raise forms.ValidationError("Occurrence date cannot be after report date")
            elif occ_date == rep_date and occ_time and rep_time:
                if occ_time > rep_time:
                    raise forms.ValidationError("Occurrence time cannot be after report time on the same day")
        
        return cleaned_data

# Form for creating a new location type
class LocationTypeForm(forms.ModelForm):
    class Meta:
        model = LocationType
        fields = ['location_type']

# Form for creating a new clearance
class ClearanceForm(forms.ModelForm):
    class Meta:
        model = Clearance
        fields = ['clearance_status', 'clearance_date']
    
    def clean(self):
        cleaned_data = super().clean()
        clearance_status = cleaned_data.get("clearance_status")
        clearance_date = cleaned_data.get("clearance_date")
        
        # If status is C or O, clearance_date is required
        if clearance_status in ['C', 'O'] and not clearance_date:
            raise forms.ValidationError("Clearance date is required when status is 'Cleared by arrest' or 'Cleared by exception'")
        
        return cleaned_data