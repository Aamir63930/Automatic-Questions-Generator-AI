with open("prisma/schema.prisma", "r", encoding="utf-8") as f:
    schema = f.read()

if "directUrl" not in schema:
    schema = schema.replace(
        'datasource db {\n  provider = "postgresql"\n  url      = env("DATABASE_URL")',
        'datasource db {\n  provider = "postgresql"\n  url      = env("DATABASE_URL")\n  directUrl = env("DIRECT_URL")'
    )
    with open("prisma/schema.prisma", "w", encoding="utf-8") as f:
        f.write(schema)
    print("Schema fixed!")
else:
    print("Already has directUrl")