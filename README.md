# histmark: smarter historic marker discovery

This service uses natural language processing to determine similarities between historic markers in Washington, D.C. based primarily on the text on the historic markers, and is able to construct suggested walking tour routes for users.

The code for a web app is in `/app/`. The app is built in Flask and queries a SQL database containing historic marker information and the results of NLP analysis.

## Dependencies

- `flask`
- `numpy`
- `openrouteservice`
- `ortools`
- `pandas`
- `psycopg2`
- `sqlalchemy`
