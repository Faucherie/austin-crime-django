# CM3035 Midterm Report — Austin Crime Reports REST API

## 1. Introduction and Dataset

This RESTful web service is based on the City of Austin's public Crime Reports dataset (Austin Open Data Portal). The dataset logs every incident recorded by the Austin Police Department (APD) since 2003 and contains over 2.6 million rows in full. Because the project requires fewer than 10,000 database entries, the repository ships with a `populate_austin_crime_test.py` loader that seeds the database with a 1,000-row sample — comfortably under the limit and fast enough for local development and testing. The full `populate_austin_crime.py` loader remains available for a larger slice; it loads the most recent twelve-month window from the full CSV, capped at 10,000 rows, so either loader keeps the database within the constraint.

I chose this dataset for two reasons. First, I thought the content was interesting. Second I was drawn to the ability to imrove the flat file with modeling the natural hierarchies present in the data. The UCR (FBI Uniform Crime Reporting) offense classification is broken into the categories set by the FBI, and the crimes under city Austin, Texas, and federal laws. The purpose for Austin PD to publish this data is for transparancy.

## 2. Data Model

### 2.1 Original Flat Dataset

The raw CSV supplied by the City of Austin contains 19 columns, each recording one attribute of a crime report. An illustrative slice is shown below.

| Incident Number | Highest Offense Description | Highest Offense Code | Family Violence | Occurred Date Time | Occurred Date | Occurred Time | Report Date Time | Report Date | Report Time | Location Type | Council District | APD Sector | APD District | Clearance Status | Clearance Date | UCR Category | Category Description | Census Block Group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20251820008 | FAMILY DISTURBANCE | 3400 | N | 07/01/2025 00:11 | 07/01/2025 | 11 | 07/01/2025 00:11 | 07/01/2025 | 11 | RESIDENCE / HOME | 7 | ID | 7 | N | 07/03/2025 | | | 4530015053 |
| 20251820019 | ASSAULT BY CONTACT-FAM/DATING VIO | 902 | Y | 07/01/2025 00:24 | 07/01/2025 | 24 | 07/01/2025 00:24 | 07/01/2025 | 24 | HOTEL / MOTEL / ETC. | 9 | GE | 1 | N | 07/08/2025 | | | 4530011032 |
| 20251820020 | AGG ASSAULT | 402 | N | 07/01/2025 00:31 | 07/01/2025 | 31 | 07/01/2025 00:31 | 07/01/2025 | 31 | HWY / ROAD / ALLEY/ STREET/ SIDEWALK | 1 | CH | 2 | C | 08/22/2025 | 13A | Aggravated Assault | 4530008042 |
| 20251820040 | POSSESSION OF MARIJUANA | 1803 | N | 07/01/2025 01:29 | 07/01/2025 | 129 | 07/01/2025 01:29 | 07/01/2025 | 129 | HWY / ROAD / ALLEY/ STREET/ SIDEWALK | 2 | FR | 8 | N | 07/09/2025 | | | 4530024411 |
| 20251820083 | AUTO THEFT | 700 | N | 07/01/2025 01:30 | 07/01/2025 | 130 | 07/01/2025 01:47 | 07/01/2025 | 147 | PARKING /DROP LOT/ GARAGE | 3 | CH | 1 | N | 09/02/2025 | 240 | Auto Theft | 4530021112 |
| 20251821046 | MURDER | 100 | N | 07/01/2025 18:10 | 07/01/2025 | 1810 | 07/01/2025 18:10 | 07/01/2025 | 1810 | RESIDENCE / HOME | 4 | ED | 1 | C | 07/02/2025 | 09A | Murder | 4530400003 |

This flat structure is convenient for publication but poor for storage and querying: it repeats location-type labels, offense descriptions, sector names, and UCR category text on every row, and it mixes temporal and jurisdictional dimensions with the core incident facts.

### 2.2 Research on Austin Jurisdictions

Before normalising, I reviewed how Austin’s geographic identifiers relate to one another. The Austin Police Department divides the city into ten sectors (Adam, Airport, Baker, Charlie, David, Edward, Frank, George, Henry, Ida), each commanded separately. Each sector is further divided into numbered districts; for example, *Charlie 8* is sector Charlie, district 8. This means the district number alone is not informative without the sector: district 2 in Charlie is a different place from district 2 in Adam. The CSV therefore has a functional dependency `district → sector`, so the two attributes should not sit side-by-side in the same table. The city also has ten council districts, but these boundaries are drawn for political representation and do not align one-to-one with police sectors, so they are modelled as an independent attribute of the incident.

Austin Open Data also supplies a Census Block Group map. A census block group is a Census Bureau geography of roughly 600–3,000 residents used to aggregate demographic and housing data. Because the source data includes a block-group code for every incident, it can be stored as its own reference table and used for location-based queries.

### 2.3 Normalisation

**1NF — Atomic values.** The source contains two composite columns, `Occurred Date Time` and `Report Date Time`, which merge a date and a time. Since the CSV also supplies the individual `Occurred Date`, `Occurred Time`, `Report Date`, and `Report Time` fields, the composite columns are discarded and the atomic fields are kept. Although each row currently lists only one offense, the design anticipates the possibility of multiple offenses per incident, so offense data is split out rather than left embedded in the incident table.

After 1NF the schema separates into an incident table and a crime table:

**Table: Austin Incident** (PK: `incident_number`)

| incident_number | family_violence | occ_date | occ_time | rep_date | rep_time | location_type | council_district | sector | district | clearance_status | clearance_date | census_block_group |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20251820008 | N | 07/01/2025 | 11 | 07/01/2025 | 11 | RESIDENCE / HOME | 7 | ID | 7 | N | 07/03/2025 | 4530015053 |
| 20251820019 | Y | 07/01/2025 | 24 | 07/01/2025 | 24 | HOTEL / MOTEL / ETC. | 9 | GE | 1 | N | 07/08/2025 | 4530011032 |

**Table: Crime** (PK: `crime_code`)

| crime_type | crime_code | ucr_category | category_description |
|---|---|---|---|
| FAMILY DISTURBANCE | 3400 | | |
| ASSAULT BY CONTACT-FAM/DATING VIO | 902 | | |
| AGG ASSAULT | 402 | 13A | Aggravated Assault |
| POSSESSION OF MARIJUANA | 1803 | | |
| AUTO THEFT | 700 | 240 | Auto Theft |
| MURDER | 100 | 09A | Murder |

**2NF — No partial-key dependencies.** Neither table has a composite primary key, so no partial-key dependencies exist.

**3NF — Eliminate transitive dependencies.** Three transitive dependencies are removed:

1. **Police geography.** `district` determines `sector` (`district 2 in Charlie` implies sector `CH`), so a separate `Sector` / `District` hierarchy is created. `Sector` stores the sector code/name, and `District` stores `(sector, district_number)` with a unique constraint, because different sectors may each contain a district 1.
2. **Clearance.** `clearance_status` and `clearance_date` describe a separate process that updates after the incident is filed, so they move to a one-to-one `Clearance` table keyed by `incident`.
3. **UCR classification.** `category_description` depends on `ucr_category`, not on `crime_code`, so a `UCRCategory` table is introduced; `UCRCrime` then holds `crime_code`, `crime_type`, and an FK to `UCRCategory`.

After 3NF the key tables are:

**Table: Austin Incident** (PK: `incident_number`)

| incident_number | family_violence | occ_date | occ_time | rep_date | rep_time | location_type_id | council_district_id | census_block_group_id | district_id |
|---|---|---|---|---|---|---|---|---|---|
| 20251820008 | N | 07/01/2025 | 11 | 07/01/2025 | 11 | 1 | 7 | 4530015053 | 7 |
| 20251820019 | Y | 07/01/2025 | 24 | 07/01/2025 | 24 | 2 | 9 | 4530011032 | 1 |

**Table: APD Sector–District** (PK: `district_id`; unique on `(sector_id, district_number)`)

| sector | district_number |
|---|---|
| ID | 7 |
| GE | 1 |
| CH | 2 |
| FR | 8 |
| CH | 1 |
| ED | 1 |

**Table: Clearance** (PK/FK: `incident_id`)

| incident_id | clearance_status | clearance_date |
|---|---|---|
| 20251820008 | N | 07/03/2025 |
| 20251820019 | N | 07/08/2025 |

**Table: UCR Crime** (natural key: `(crime_code, crime_type)`)

| crime_type | crime_code | ucr_category_id |
|---|---|---|
| FAMILY DISTURBANCE | 3400 | |
| ASSAULT BY CONTACT-FAM/DATING VIO | 902 | |
| AGG ASSAULT | 402 | 13A |
| POSSESSION OF MARIJUANA | 1803 | |
| AUTO THEFT | 700 | 240 |
| MURDER | 100 | 09A |

**Table: UCR Category** (PK: `ucr_category`)

| ucr_category | category_description |
|---|---|
| 13A | Aggravated Assault |
| 240 | Auto Theft |
| 09A | Murder |

Additional reference tables are extracted for repeating labels: `LocationType` (premise descriptions), `CouncilDistrict` (1–10), and `CensusBlockGroup` (the 12-digit block-group code).

### 2.4 Django Implementation

The normalised design is implemented as Django models. The seven reference tables are small, single-purpose classes. For example, `District` enforces the `district → sector` dependency discovered in 3NF with a unique `(sector, number)` pair, because different sectors may each contain a district 1:

```python
class District(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sector", "number"],
                name="unique_sector_district",
            ),
        ]
```

`UCRCrime` is similarly constrained on `(crime_code, crime_type)` because the source mapping is not one-to-one: code `900` appears with both `"ASSAULT WITH INJURY"` and `"ASSAULT WITH INJURY-FAM/DATING VIO"`, so the natural key must include both fields. Its FK to `UCRCategory` is nullable because some offenses arrive without a UCR classification.

The `Incident` fact table uses the APD-assigned `incident_number` as its primary key rather than a surrogate, because it is guaranteed unique and stable across systems. All incident-to-lookup FKs use `on_delete=DO_NOTHING`: Django's default cascade is inappropriate here because deleting a lookup row should never silently remove thousands of historical incidents. Offenses are attached through an explicit `ManyToManyField` with `through='IncidentCrimeLink'`, which keeps the join inspectable for the HTML and API views:

```python
class Incident(models.Model):
    incident_number = models.BigIntegerField(primary_key=True)
    ...
    district = models.ForeignKey(District, on_delete=models.DO_NOTHING, null=True, blank=True)
    crimes = models.ManyToManyField(UCRCrime, through='IncidentCrimeLink')
```

The `IncidentCrimeLink` model adds a unique `(incident, crime)` constraint to prevent duplicate associations. Its FKs use `DO_NOTHING`, so it is removed explicitly when an incident is deleted, keeping that destructive path visible. `Clearance` is a one-to-one companion table with a `Status` `TextChoices` enum and a nullable `clearance_date`; it uses `on_delete=CASCADE` so it is removed automatically when its incident is deleted.

## 3. Endpoints (R1c, R1d, R3)

URL routing uses named `path()` patterns resolved through `reverse()`, so templates and tests never hard-code URLs. The application exposes twenty browsable HTML routes plus six JSON API routes. The HTML routes reuse Django's generic class-based views; the filtered incident lists inherit from a common base that supplies pagination, ordering, and sidebar context, so each concrete subclass only overrides its queryset.

### REST API
The detail endpoint, `GET/POST/PUT/DELETE /api/incident/<pk>/`, composes four DRF mixins over `GenericAPIView`, giving one URL the full CRUD cycle:

```python
class IncidentDetail(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     generics.GenericAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        incident = self.get_object()
        IncidentCrimeLink.objects.filter(incident=incident).delete()
        Clearance.objects.filter(incident=incident).delete()
        return self.destroy(request, *args, **kwargs)
```

`delete()` explicitly removes the related `IncidentCrimeLink` and `Clearance` rows that `DO_NOTHING` FKs intentionally leave before destroying the incident. POST is the single mutation endpoint required by the brief; it creates a new incident via `IncidentSerializer` and returns 201 on success, 400 on validation failure.

The remaining five endpoints are read-only lists:

- `GET /api/incidents` — paginated list of all incidents.
- `GET /api/incidents/family_violence_assault/` — the most analytically interesting query, a three-hop join across the join table and UCR hierarchy answering "which family-violence incidents were aggravated assaults?".
- `GET /api/incidents/no_clearance/` — unresolved cases via a reverse one-to-one traversal.
- `GET /api/incidents/location_type/<id>/` — incidents at a given premise type.
- `GET /api/incidents/ucr_category/<id>/` — incidents under a given UCR category.

The family-violence assault query demonstrates why the join table is modelled explicitly:

```python
class IncidentFamilyViolenceAssaultList(generics.ListAPIView):
    serializer_class = IncidentSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Incident.objects.filter(
            family_violence=True,
            crimes__ucr_category__ucr_category='13A'
        ).distinct().order_by('-occ_date', '-occ_time', 'pk')
```

`crimes__ucr_category__ucr_category='13A'` traverses `Incident → IncidentCrimeLink → UCRCrime → UCRCategory`, and `distinct()` is required because the M2M join can duplicate incident rows. The parameterised list endpoints use `get_object_or_404` so an invalid id returns a clean JSON 404. All list endpoints share the same pagination envelope and deterministic ordering (`-occ_date`, `-occ_time`, `pk`), so results are stable across pages.

## 4. Forms, Validation and Serialization (R1b)

### 4.1 HTML Forms

HTML writes use paired `ModelForm`s: `IncidentForm` and `ClearanceForm` are validated and saved together from the same POST, so an incident is always created with a clearance. `IncidentForm` adds a `crimes` checkbox group that drives the M2M offense list, and its `clean()` enforces the domain rule that a crime cannot be reported before it occurs. `ClearanceForm` uses the same cross-field pattern to require a clearance date whenever the status is cleared.

```python
class IncidentForm(forms.ModelForm):
    crimes = forms.ModelMultipleChoiceField(
        queryset=UCRCrime.objects.all().order_by('ucr_category'),
        widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = Incident
        fields = ['family_violence', 'occ_date', 'occ_time', 'rep_date', 'rep_time',
                  'location_type', 'council_district', 'census_block_group', 'district']

    def clean(self):
        cleaned_data = super().clean()
        occ_date, occ_time = cleaned_data.get("occ_date"), cleaned_data.get("occ_time")
        rep_date, rep_time = cleaned_data.get("rep_date"), cleaned_data.get("rep_time")
        if occ_date and rep_date:
            if occ_date > rep_date or (occ_date == rep_date and occ_time and rep_time and occ_time > rep_time):
                raise forms.ValidationError("Occurrence cannot be after report")
        return cleaned_data
```

### 4.2 Serializers

`IncidentSerializer` is a `ModelSerializer` that nests a serializer inside it for each related object. This means a single JSON payload can both describe the incident and point at its related rows, for example:

```json
{
  "family_violence": false,
  "location_type": {"id": 1},
  "crimes": [{"id": 5}],
  "clearance": {"clearance_status": "N"}
}
```

`incident_number` is `read_only` because the server assigns it. The nested serializers for lookup objects (`LocationType`, `CouncilDistrict`, etc.) are plain `Serializer` classes rather than `ModelSerializer`. This is important because a `ModelSerializer` would try to *create* the nested object and enforce its unique constraints. If `location_type` already exists with id 1, a nested `ModelSerializer` would reject the payload with "location type with this id already exists" — even though we only want to *reference* it. Plain serializers only check that the payload has the right shape (e.g. `{"id": 1}` is an integer), and then `IncidentSerializer.validate()` looks the row up in the database itself. If it is missing, `validate()` returns a field-keyed 400 error such as `{"location_type": "LocationType id=1 does not exist."}`. `ClearanceSerializer` is the one nested serializer kept as a `ModelSerializer`, because a new incident really does create a new `Clearance` row.

### 4.3 Nested Writes

DRF does not write nested representations automatically, so `create()` and `update()` are implemented by hand. `create()` auto-generates the next `incident_number` as `max(existing) + 1`, resolves each nested lookup to an existing row, and guarantees every incident a `Clearance` — defaulting to "Not cleared" when omitted:

```python
    def create(self, validated_data):
        last = Incident.objects.order_by('-incident_number').first()
        validated_data['incident_number'] = (last.incident_number + 1) if last else 1

        location_type_data = validated_data.pop('location_type', None)
        crimes_data = validated_data.pop('crimes', [])
        clearance_data = validated_data.pop('clearance', None)
        # ... council_district, census_block_group, district popped likewise ...

        incident = Incident(**validated_data)
        if location_type_data:
            incident.location_type = LocationType.objects.get(id=location_type_data['id'])
        # ... remaining FKs resolved likewise ...
        incident.save()

        for crime_data in crimes_data:
            crime = UCRCrime.objects.get(id=crime_data['id'])
            IncidentCrimeLink.objects.create(incident=incident, crime=crime)

        if clearance_data:
            Clearance.objects.create(incident=incident, **clearance_data)
        else:
            Clearance.objects.create(incident=incident,
                clearance_status=Clearance.Status.NOT_CLEARED,
                clearance_date=None, last_updated=None)

        return incident
```

`update()` uses `is not None` guards so an omitted foreign key leaves the value unchanged while an explicit `null` clears it. Crime links are rebuilt wholesale when `crimes` is supplied, and `Clearance` is updated in place rather than deleted and recreated, preserving its one-to-one identity.

## 5. Bulk Loading (R4)

Data is loaded by a standalone script, `populate_austin_crime.py`, which bootstraps Django outside the request cycle and runs directly against the CSV:

```python
sys.path.append('/home/scott-swanson/University_of_London/CM3035_advanced_web_development/Midterm/PROJECT/austin_crime')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'austin_crime.settings')
django.setup()
```

The biggest friction in the loader is converting the CSV's date and time columns into Django's `DateField` and `TimeField`. Dates are stored as strings in `MM/DD/YYYY` format, but the time column is stored as a raw integer such as `30` for 00:30, `130` for 01:30, or `1430` for 14:30. The value is not zero-padded, so the same integer must be interpreted differently depending on its magnitude. The script therefore splits the integer into hours and minutes by integer division: `time_int // 100` gives the hours and `time_int % 100` gives the minutes. A value of `30` becomes `time(0, 30)`, while `1430` becomes `time(14, 30)`.

```python
def parse_time(time_str):
    if not time_str or time_str.strip() == '':
        return time(0, 0)
    try:
        time_int = int(time_str)
        return time(time_int // 100, time_int % 100)
    except (ValueError, TypeError):
        return time(0, 0)
```

Missing or malformed values are coerced to sensible defaults (`None` for dates, `00:00` for times) so a single bad cell does not abort the whole load.

The loading pipeline has three phases. First, `parse_csv()` walks the file once and collects de-duplicated reference sets (location types, council districts, sectors, districts, UCR categories, UCR crimes, and census block groups) while storing incident rows in a dictionary keyed by `incident_number`. It also skips rows where the APD district is non-numeric, which prevents downstream `ValueError`s.

Second, `clear_database()` deletes existing rows in dependency order — links and clearances first, then incidents, then reference tables — avoiding foreign-key constraint errors. `create_reference_data()` then inserts the reference tables and returns mappings by natural key.

Third, `main()` re-fetches the inserted reference rows to build fresh FK dictionaries, calls `create_incidents_and_clearances()`, and creates one `Incident`, one `IncidentCrimeLink`, and one `Clearance` per valid row. Errors are counted and reported, but the script keeps going so a few malformed rows do not stop the load.

A companion `populate_austin_crime_test.py` loads a 1,000-row sample CSV, keeping the total database size comfortably under the 10,000-row limit while still exercising every table and relationship.

## 6. Unit Testing (R1e)

The test suite contains 25 tests in seven `APITestCase` classes; DRF's test client exercises the full stack — routing, view, serializer, database — against an isolated test database created and destroyed per run. Fixtures come from Factory Boy, with a factory per model and `factory.SubFactory` chaining so a single `IncidentFactory.create()` populates the entire FK graph:

```python
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
```

Each `tearDown` deletes rows in dependency order and resets factory sequences so tests stay independent.

The tests cover four areas. **Serializer contract**: `IncidentSerializerTest` checks the exact field set and per-field data correctness. **Read/delete**: GET returns 200 with the right body, a bad pk returns 404, DELETE returns 204. **Creation**: the auto-generated incident number is deterministic (`max + 1`), and a `Clearance` defaulting to "Not cleared" is auto-created when the payload omits one — verified by querying the database directly, not just the response. **Validation**: an empty body, a malformed date (`"not-a-date"`), a malformed time (`"99:99:99"`), and a non-existent foreign key each return 400, confirming both DRF's field validation and the custom `validate()` referential check. Each list endpoint is additionally tested for status, pagination envelope, count correctness, and — critically — that filters *exclude* what they should. For example, the no-clearance test seeds one resolved and one unresolved case and asserts the cleared case is absent, not merely that the uncleared one is present:

```python
class IncidentNoClearanceListTest(APITestCase):

    def setUp(self):
        self.incident1 = IncidentFactory.create(incident_number=20260001)
        self.incident2 = IncidentFactory.create(incident_number=20260002)
        Clearance.objects.create(incident=self.incident1,
            clearance_status=Clearance.Status.NOT_CLEARED, clearance_date=None)
        Clearance.objects.create(incident=self.incident2,
            clearance_status=Clearance.Status.CLEARED_BY_ARREST, clearance_date='2026-01-15')
        self.url = reverse('api_incidents_no_clearance')

    def test_noClearanceListOnlyReturnsUnresolvedIncidents(self):
        response = self.client.get(self.url, format='json')
        data = json.loads(response.content)
        numbers = [item['incident_number'] for item in data['results']]
        self.assertIn(20260001, numbers)
        self.assertNotIn(20260002, numbers)
```

## 7. Critical Evaluation

Measured against current best practice, three things stand out. First, the mixin-composed `IncidentDetail` demonstrates DRF's architecture explicitly, but the state-of-the-art layout is a `ModelViewSet` registered on a `DefaultRouter` (or `RetrieveUpdateDestroyAPIView` + `ListCreateAPIView`), which generates consistent routes for free; likewise `django-filter` would replace the one-view-per-filter pattern with declarative query parameters. Second, the list endpoints serialize nested foreign keys without `select_related`/`prefetch_related`, so each page issues N+1 queries — acceptable at this dataset size, but the first thing to fix at scale. Third, nested-write serializers remain a known rough edge in DRF; my plain-`Serializer` workaround is pragmatic, but `SlugRelatedField`/`PrimaryKeyRelatedField` would be more idiomatic. The natural next steps beyond the course content would be `drf-spectacular` for an OpenAPI schema with Swagger UI served from the main page, property-based testing of the serializer validators with Hypothesis, and upgrading from Django 3.2 LTS (now end-of-life) to a supported 4.2/5.x release.

## 8. Running the Application

- **Environment:** developed on Ubuntu 24.04.4 LTS with Python 3.12.3 and the default SQLite3 database.
- **Packages** (pinned in `requirements.txt`, located next to `manage.py`): Django 3.2.25, djangorestframework 3.11.1, django-bootstrap4 2.2.0, factory_boy 3.0.1 (transitive: asgiref, pytz, sqlparse, Faker, beautifulsoup4, soupsieve).
- **Install:** unzip, then `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`.
- **Migrate & seed:** `python manage.py migrate`, then run the loading script: `python austin_crime/scripts/populate_austin_crime.py` (the test variant `populate_austin_crime_test.py` loads the 1,000-row sample).
- **Run:** `python manage.py runserver`, then browse `http://127.0.0.1:8000/` (API under `/api/...`).
- **Admin:** `http://127.0.0.1:8000/admin/` — username `admin`, password `password`.
- **Tests:** `python manage.py test incidents` (25 tests, all passing).
