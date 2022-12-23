import os
from pathlib import Path

BASEDIR = Path(__file__).parent.parent.resolve().absolute()
DOWNLOAD_FOLDER = BASEDIR.joinpath("download")
# DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'download')
if not os.path.isdir(DOWNLOAD_FOLDER):
    os.mkdir(DOWNLOAD_FOLDER)

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_NAME = os.getenv("DATABASE_NAME", "soil_data")

# Keep in mind, all table here are filtered by mukey column values, so if
# chorizon table needs to be imported it shouldn't be pointed to porcess here,
# but instead separate import should be used
IMPORT_TABLES = [
    'component',
    'mapunit',
    'valu1',
    'muaggatt',
]

STATES = [
    'AK',
    'AL',
    'AR',
    'AS',
    'AZ',
    'CA',
    'CO',
    'CT',
    'DC',
    'DE',
    'FL',
    'FM',
    'GA',
    'GU',
    'HI',
    'IA',
    'ID',
    'IL',
    'IN',
    'KS',
    'KY',
    'LA',
    'MA',
    'MD',
    'ME',
    'MH',
    'MI',
    'MN',
    'MO',
    'MP',
    'MS',
    'MT',
    'NC',
    'ND',
    'NE',
    'NH',
    'NJ',
    'NM',
    'NV',
    'NY',
    'OH',
    'OK',
    'OR',
    'PA',
    'PRUSVI',
    'PW',
    'RI',
    'SC',
    'SD',
    'TN',
    'TX',
    'UT',
    'VA',
    'VT',
    'WA',
    'WI',
    'WV',
    'WY',
    ]
