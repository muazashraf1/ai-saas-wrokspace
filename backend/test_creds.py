import psycopg2

users = ['postgres', 'muaz', 'Muaz', 'asad', 'Asad', 'Administrator']
passwords = ['muaz2205802', 'Muaz2205802', 'postgres', 'admin', 'root']

found = None
for u in users:
    for p in passwords:
        try:
            conn = psycopg2.connect(
                host='127.0.0.1',
                port=5432,
                user=u,
                password=p,
                dbname='postgres'
            )
            print(f"SUCCESS: user='{u}', password='{p}'")
            conn.close()
            found = (u, p)
            break
        except Exception as e:
            err = str(e)
            if "password authentication failed" in err:
                pass  # user exists, wrong password
            elif "does not exist" in err:
                pass  # user does not exist
    if found:
        break

if not found:
    print("NO_COMBINATION_WORKED")
