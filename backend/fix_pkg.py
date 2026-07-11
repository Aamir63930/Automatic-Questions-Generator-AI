import json, re

with open("package.json", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the # commented lines
content = re.sub(r'\s*#"cloudinary":[^\n]+,?\n', '\n', content)
content = re.sub(r'\s*#"multer-storage-cloudinary":[^\n]+,?\n', '\n', content)

# Fix trailing commas before }
content = re.sub(r',(\s*[}\]])', r'\1', content)

# Verify it's valid JSON
try:
    pkg = json.loads(content)
    # Make sure cloudinary is removed
    pkg.get('dependencies', {}).pop('cloudinary', None)
    pkg.get('dependencies', {}).pop('multer-storage-cloudinary', None)
    
    with open("package.json", "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=2)
    print("package.json fixed!")
except Exception as e:
    print("Error:", e)
    print("Content around error:")
    print(content[550:650])