# Austin Crime Reports REST API

Coursework for the University of London BSc Computer Science, Advanced Web Development (CM3035) midterm, 2026.

A Django REST API over the City of Austin's public crime reports, with a normalized data model and CSV loading.

## Running locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DJANGO_SECRET_KEY='any-local-value'
python manage.py migrate
python manage.py runserver
```

`data/` holds sample extracts. The full dataset is on the [City of Austin open data portal](https://data.austintexas.gov/). The write-up is in `report/report_final.md`.

---

Scott Swanson
