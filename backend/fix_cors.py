with open("src/app.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the wildcard options route
content = content.replace(
    "app.options('*', require('cors')())",
    "app.options('(.*)', require('cors')())"
)

# Also fix if it's written differently  
content = content.replace(
    'app.options("*", require(\'cors\')())',
    "app.options('(.*)', require('cors')())"
)

with open("src/app.ts", "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed! Now run: npm run dev")