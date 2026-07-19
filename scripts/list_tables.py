from sqlalchemy import create_engine, text

e = create_engine("postgresql://postgres:postgres@127.0.0.1:5432/intelligence")
with e.connect() as c:
    rows = c.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")
    ).fetchall()
    print("tables:", [r[0] for r in rows])
    enums = c.execute(
        text("SELECT typname FROM pg_type WHERE typtype='e' ORDER BY 1")
    ).fetchall()
    print("enums:", [r[0] for r in enums])
