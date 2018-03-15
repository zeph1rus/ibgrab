import sqlite3
db_location = '/opt/ibgrab/db/ibgrab.db'
conn = sqlite3.connect(db_location)
c = conn.cursor()
c.execute('''CREATE TABLE images (imageurl text, date text)''')
conn.commit()
conn.close()
