from django.db import models

class LocationType(models.Model):
    """Reference table storing APD premise descriptions for incidents.
 
    Enforces uniqueness on the premise name so every ``Incident.location_type``
    foreign key resolves to a single row.
 
    Attributes:
        id: Auto-generated primary key.
        location_type: Human-readable premise label (e.g. "RESIDENCE / HOME").
            Max 255 characters, unique.

    Methods:
        __str__: Returns the location type as a string.
    """

    location_type = models.CharField(max_length=255, unique=True, null=False, blank=False)

    def __str__(self):
        return self.location_type


class CouncilDistrict(models.Model):
    """Reference table storing Austin city council districts.
    
    Attributes:
        council_district: Integer representing the council district number (1-10).
            Unique and serves as the primary key.
    
    Methods:
        __str__: Returns the council district number as a string.
    """
    council_district = models.IntegerField(unique=True, primary_key=True, null=False, blank=False)
    
    def __str__(self):
        return str(self.council_district)


class CensusBlockGroup(models.Model):
    """Reference table storing census block group codes. 

    Serves as smallest political geographic unit for census data.

    Attributes:
        census_block_group: 10-digit census block group code (e.g. 4530406001).
            Primary key.

    Methods:
        __str__: Returns the census block group code as a string.
    """
    census_block_group = models.BigIntegerField(primary_key=True)

    def __str__(self):
        return str(self.census_block_group)


class Sector(models.Model):
    """Reference table storing APD sector codes.

    APD divides Austin into ten named sectors (Adam, Airport, Baker, Charlie,
    David, Edward, Frank, George, Henry, Ida). Each sector is subdivided into
    numbered districts (see class:`District`). The dataset stores the sector
    as a two-character code (e.g. `'HE'` for Henry); the full name is
    recovered via :meth:`get_name_display`.

    Attributes:
        name: Two-character sector code, unique, constrained to `'Name`` choices.

    Methods:
        __str__: Returns the human-readable sector name (e.g. "Henry").

    """

    class Name(models.TextChoices):
        ADAM    = "AD", "Adam"
        AIRPORT = "AI", "Airport"
        BAKER   = "BA", "Baker"
        CHARLIE = "CH", "Charlie"
        DAVID   = "DA", "David"
        EDWARD  = "ED", "Edward"
        FRANK   = "FR", "Frank"
        GEORGE  = "GE", "George"
        HENRY   = "HE", "Henry"
        IDA     = "ID", "Ida"

    name = models.CharField(max_length=2, unique=True, choices=Name.choices, null=False, blank=False)

    def __str__(self):
        return self.get_name_display()


class District(models.Model):
    """Reference table storing APD districts within a sector.

    A district is a subdivision of a class:`Sector`. The pair
    `'(sector, number)`` is the natural key and is enforced with a
    ``UniqueConstraint``; different sectors may each have a district ``1``,
    but a given sector cannot have two districts with the same number.

    Attributes:
        sector: Foreign key to the parent :class:`Sector`.
        number: District number within the sector (e.g. 1, 2, 3).

    Methods:
        __str__: Returns the concatenated label (e.g. "Adam1").
    """
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="districts")
    number = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sector", "number"],
                name="unique_sector_district",
            ),
        ]

    def __str__(self):
        return f"{self.sector}{self.number}"


class UCRCategory(models.Model):
    """Reference table storing UCR (Uniform Crime Reporting) category codes and their descriptions.

    The FBI created a standardized system of definitions in NIBRS to ensure consistent data
    collection across all law enforcement agencies. This practice ensures the national UCR
    Program considers and appropriately counts all criminal offenses of law, regardless of their
    different titles under state and local law or United States titles and statutes.

    Attributes:
        ucr_category: Short UCR category code (up to four characters, e.g. "09A", "13A", "23A").
        category_description: Human-readable label (e.g. "Murder and Nonnegligent Manslaughter").

    Methods:
        __str__: Returns the concatenated label (e.g. "09A:Murder and Nonnegligent Manslaughter").
    """
    ucr_category = models.CharField(max_length=4, null=False, blank=False)
    category_description = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return f"{self.ucr_category}:{self.category_description}"


class UCRCrime(models.Model):
    """Reference table storing APD "Highest Offense" codes and their descriptions.

    Each row is one distinct (code, description) pair drawn from the CSV's
    ``Highest Offense Code`` and ``Highest Offense Description`` columns.
    The mapping is not strictly 1:1 in the source data (e.g. code ``900``
    appears with both ``"ASSAULT WITH INJURY"`` and
    ``"ASSAULT WITH INJURY-FAM/DATING VIO"``), so ``(crime_code, crime_type)``
    is the natural key and is enforced with a ``UniqueConstraint``.

    Every crime is optionally categorised under the FBI's UCR / NIBRS scheme
    via ``ucr_category``. The FK is nullable because a small number of CSV
    rows arrive with a blank UCR classification (e.g. ``POSSESSION OF
    MARIJUANA,1803`` has no UCR category).

    Attributes:
        crime_code: APD offense code (e.g. 1803 for possession of marijuana).
        crime_type: Human-readable offense description.
        ucr_category: Optional FK to :class:`UCRCategory`.

    Methods:
        __str__: Returns the concatenated label (e.g. "1803:POSSESSION OF MARIJUANA").
    """
    crime_code = models.IntegerField(null=False, blank=False)
    crime_type = models.CharField(max_length=100, null=False, blank=False)
    ucr_category = models.ForeignKey(UCRCategory, on_delete=models.DO_NOTHING, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["crime_code", "crime_type"],
                name="unique_crime_code_type",
            ),
        ]

    def __str__(self):
        return f"{self.crime_code}:{self.crime_type}"


class Incident(models.Model):
    """Fact table storing one row per reported crime incident.

    ``incident_number`` is the APD-assigned identifier for the incident and
    is used directly as the primary key (it is guaranteed unique in the CSV
    and stable across systems). Every other column is either a scalar
    describing the incident or a foreign key into one of the reference
    tables above.

    All FKs into lookup tables use ``on_delete=DO_NOTHING`` so that removing
    a single lookup row never silently mutates the historical incident
    record. 
    
    The many-to-many ``crimes`` relationship is declared with an
    explicit ``through`` model so we can modify the dataset and list multiple 
    crimes to one incident, rather than just heighest sevarity.

    Times are stored as :class:`~django.db.models.TimeField` rather than
    the raw ``HHMM`` integers in the CSV

    Attributes:
        incident_number: APD-assigned identifier, primary key.
        family_violence: Boolean flag (CSV ``"Y"``/``"N"`` is coerced by the loader).
        occ_date, occ_time: Date and time the offence occurred.
        rep_date, rep_time: Date and time the offence was reported.
        location_type: FK to :class:`LocationType`.
        council_district: FK to :class:`CouncilDistrict`.
        census_block_group: FK to :class:`CensusBlockGroup`.
        district: FK to :class:`District` (which in turn FKs to :class:`Sector`).
        crimes: M2M to :class:`UCRCrime` via :class:`IncidentCrimeLink`.

    Methods:
        __str__: Returns the incident number as a string.
    """
    incident_number = models.BigIntegerField(null=False, blank=False, primary_key=True)
    family_violence = models.BooleanField(null=False, blank=False)
    occ_date = models.DateField(null=False, blank=False)
    occ_time = models.TimeField(null=False, blank=False)
    rep_date = models.DateField(null=False, blank=False)
    rep_time = models.TimeField(null=False, blank=False)
    location_type = models.ForeignKey(LocationType, on_delete=models.DO_NOTHING, null=True, blank=True)
    council_district = models.ForeignKey(CouncilDistrict, on_delete=models.DO_NOTHING, null=True, blank=True)
    census_block_group = models.ForeignKey(CensusBlockGroup, on_delete=models.DO_NOTHING, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.DO_NOTHING, null=True, blank=True)
    crimes = models.ManyToManyField(UCRCrime, through='IncidentCrimeLink')

    def __str__(self):
        return str(self.incident_number)
    def get_crimes(self):
        return self.crimes.all()
    def get_crime_codes(self):
        return [crime.crime_code for crime in self.crimes.all()]
    def get_crime_types(self):
        return [crime.crime_type for crime in self.crimes.all()]
    def get_ucr_categories(self):
        return [crime.ucr_category for crime in self.crimes.all()]
    def get_location_type_description(self):
        return self.location_type.location_type if self.location_type else None
    def get_council_district_number(self):
        return self.council_district.council_district if self.council_district else None
    def get_census_block_group_id(self):
        return self.census_block_group.census_block_group if self.census_block_group else None
    def get_district_number(self):
        return self.district.district if self.district else None


class IncidentCrimeLink(models.Model):
    """Explicit through-model for the :class:`Incident` \u2194 :class:`UCRCrime` M2M.

    Behaviour:
    - One incident, one crime: one row
    - One incident, multiple crimes: multiple rows with the same incident FK and different crime FKs
    - Same crime, different incidents: multiple rows with the same crime FK and different incident FKs


    Attributes:
        incident: FK to :class:`Incident`.
        crime: FK to :class:`UCRCrime`.
    """
    incident = models.ForeignKey(Incident, on_delete=models.DO_NOTHING)
    crime = models.ForeignKey(UCRCrime, on_delete=models.DO_NOTHING)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['incident', 'crime'], name='unique_incident_crime')
        ]


class Clearance(models.Model):
    """1:1 companion to :class:`Incident` recording the case's clearance.

    clearance_status: One-character code constrained to:
    (``C`` cleared by arrest, ``O`` cleared by exception, ``N`` not cleared).

    Attributes:
        clearance_status: One-character code constrained to
        clearance_date: Date the case was cleared (nullable while pending).
        last_updated: Timestamp of last modification (auto-updated).
        incident: OneToOne FK to :class:`Incident`.

    Methods:
        __str__: Returns ``"<incident_id>:<clearance_status>"``.
    """

    class Status(models.TextChoices):
        CLEARED_BY_ARREST    = "C", "Cleared by arrest"
        CLEARED_BY_EXCEPTION = "O", "Cleared by exception"
        NOT_CLEARED          = "N", "Not cleared"

    clearance_status = models.CharField(max_length=1, choices=Status.choices, null=False, blank=False)
    clearance_date = models.DateField(null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    incident = models.OneToOneField(Incident, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.incident_id}:{self.clearance_status}"
