from . import config
from .db import sync_session
import pandas as pd
from datetime import datetime


def log_event(txt, ltype: str= 'info') -> None:
    with sync_session() as session:
        eng = session.get_bind()
        pd.DataFrame({
            'timelog': [datetime.now()],
            'description': [txt],
            'ltype': ltype,
        }).to_sql(
            name='importlog',
            con=eng,
            schema='ssurgo',
            if_exists='append',
            index=False
        )
