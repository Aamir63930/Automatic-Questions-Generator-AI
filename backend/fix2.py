with open("src/app.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the problematic options line completely
content = content.replace("app.options('(.*)', require('cors')())\n", "")
content = content.replace("app.options('*', require('cors')())\n", "")
content = content.replace('app.options("*", require(\'cors\')())\n', "")

with open("src/app.ts", "w", encoding="utf-8") as f:
    f.write(content)

print("Done!")