import sqlite3

conn = sqlite3.connect('data/neovance.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM risk_monitor')
total = cursor.fetchone()[0]
print(f'\nTotal records: {total}\n')

cursor.execute('SELECT timestamp, patient_id, hr, spo2, rr, temp, map, risk_score, status FROM risk_monitor ORDER BY created_at DESC LIMIT 5')
print('Latest 5 records with NEW RISK FORMULA:')
print('='*90)
for row in cursor.fetchall():
    print(f'{row[0]} | Patient:{row[1]} | HR:{row[2]:.0f} SpO2:{row[3]:.0f}% RR:{row[4]:.0f} Temp:{row[5]:.1f} MAP:{row[6]:.0f} | Risk:{row[7]:.2f} | {row[8]}')

conn.close()
