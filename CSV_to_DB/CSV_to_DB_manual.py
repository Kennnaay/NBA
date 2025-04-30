import sqlite3 as sl
import pandas as pd

# Create/Connect database
conn = sl.connect('weather.db')
curs = conn.cursor()

# Create our table
# Manually specify table name, column names, and columns types
curs.execute('DROP TABLE IF EXISTS weather')
curs.execute('CREATE TABLE IF NOT EXISTS '
             'weather (`NAME` text, `DATE` text, `TOBS` number)')
conn.commit()  # don't forget to commit changes before continuing

values = []
with open('../Week13DataViz2of2Pandas/HW13_Starter_Code/weather.csv') as fin:
    for line in fin:
        # print(line)
        line = line.strip()
        if line:
            line = line.replace('\"', '')  # get rid of wrapping double quotes
            lineList = line.split(',')     # split on comma (CSV)
            # only accept rows w/ a last column that has a valid temp
            if lineList and lineList[-1].strip().isnumeric():
                # print(lineList
                #                     -4          -3         -2         -1
                # ['USC00454486', 'LANDSBURG', ' WA US', '2021-12-26', '23']
                valTuple = (lineList[-4] + ', ' + lineList[-3],  # re-combine city, state
                            lineList[-2], lineList[-1])
                values.append(valTuple)
for val in values:
    print(val)

for valTuple in values:
    stmt = 'INSERT OR IGNORE INTO weather VALUES (?, ?, ?)'
    curs.execute(stmt, valTuple)

# The rest is from the DB lecture and HW
print('\nFirst 3 db results:')
results = curs.execute('SELECT * FROM weather').fetchmany(3)
for result in results:
    print(result)

result = curs.execute('SELECT COUNT(*) FROM weather').fetchone()
# Note indexing into the always returned tuple w/ [0]
# even if it's a tuple of one
print('\nNumber of valid db rows:', result[0])

result = curs.execute('SELECT MAX(`TOBS`) FROM weather').fetchone()
print('Max Observed Temp', result[0])
