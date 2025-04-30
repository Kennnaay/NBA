import sqlite3 as sl

db = "players.db"
def create(fn):
    f = open(fn, "r")
    header = f.readline().strip().split(",")
    for i in range(len(header)):
        header[i] = "\'" + header[i] + "\'"
    header = ", ".join(header)
    f.close()

    conn = sl.connect(db)
    curs = conn.cursor()
    stmts = ["CREATE TABLE time_series_confirmed (" + header + ")",
             "CREATE TABLE time_series_recovered (" + header + ")"
             ]

    for stmt in stmts:
        curs.execute(stmt)
    conn.commit()

    stmts = ["SELECT name FROM sqlite_master WHERE type='table'",
             "pragma table_info(time_series_recovered)"
             ]
    for stmt in stmts:
        result = curs.execute(stmt)
        for item in result:
            print(item)

    conn.close()

def store_data(fn, table):
    conn = sl.connect(db)
    curs = conn.cursor()

    f = open(fn, "r")
    header = f.readline().strip().split(",")
    n = 0
    for line in f:
        line = line.strip()

        if "\"" in line:  # handle removal of comma inside double quotes
            iq = line.index("\"")
            ic = line[iq:].index(",") + iq
            line = line[:ic] + line[ic+1:]
        line = line.replace("\"", "")  # remove double quotes
        line = line.replace("'", "`")  # replace single quote with grave
        line = "'" + line
        icom0 = line.index(",")
        line = line[:icom0] + "','" + line[icom0+1:]
        icom1 = line[icom0+2:].index(",") + icom0 + 2
        line = line[:icom1] + "'" + line[icom1:]
        print(n, icom0, icom1, line)
        stmt = "INSERT INTO " + table + " VALUES (" + line + ")"  # combine with DML statment
        curs.execute(stmt)
        n += 1

    f.close()
    conn.commit()
    conn.close()

def main():
    pass


if __name__ == "__main__":
    main()
