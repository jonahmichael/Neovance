from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///./neonatal_ehr.db')

with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) as cnt FROM live_vitals')).fetchone()
    print(f'Total records in live_vitals: {result[0]}')
    
    if result[0] > 0:
        latest = conn.execute(text('SELECT * FROM live_vitals ORDER BY timestamp DESC LIMIT 5')).fetchall()
        print('\nLatest 5 records:')
        for row in latest:
            print(f'  {row}')
    else:
        print('\n WARNING: No records found! Pathway ETL might not be writing.')
