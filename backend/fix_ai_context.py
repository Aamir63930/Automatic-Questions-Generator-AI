# Run from BACKEND folder
with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Find getMaterialUnits and add material titles to response
old = """    const units = Array.from(new Set(materials.map((m: any) => m.unit).filter(Boolean))) as string[]
    const years = Array.from(new Set(pyqs.map((m: any) => m.year?.toString()).filter(Boolean))) as string[]
    return success(res, { units, years, hasMaterials: materials.length > 0, hasPyqs: pyqs.length > 0 })"""

new = """    const units = Array.from(new Set(materials.map((m: any) => m.unit).filter(Boolean))) as string[]
    const years = Array.from(new Set(pyqs.map((m: any) => m.year?.toString()).filter(Boolean))) as string[]
    
    // Get material titles per unit for AI context
    const unitDetails: Record<string, string[]> = {}
    materials.forEach((m: any) => {
      if (m.unit) {
        if (!unitDetails[m.unit]) unitDetails[m.unit] = []
        unitDetails[m.unit].push(m.title)
      }
    })
    
    return success(res, { units, years, unitDetails, hasMaterials: materials.length > 0, hasPyqs: pyqs.length > 0 })"""

if old in content:
    content = content.replace(old, new)
    print("getMaterialUnits updated!")
else:
    print("Pattern not found - checking...")
    idx = content.find("return success(res, { units, years")
    if idx > 0:
        print("Found at:", content[idx:idx+100])

# Fix generateQuestions to use subject context with unit names
old_prompt = "    const sysPrompt = 'You are a university exam paper setter. ' +"
new_prompt = """    // Build context from unit names + subject
    const unitContext = selectedTopics.map((t: string) => {
      return t + ' (in context of ' + subject + ')'
    }).join(', ')
    
    const sysPrompt = 'You are a university exam paper setter for ' + subject + '. ' +"""

if old_prompt in content:
    content = content.replace(old_prompt, new_prompt)
    print("System prompt updated!")

# Fix userPrompt to give better context
old_user = "    const userPrompt = 'Subject: ' + subject + '\\\\n' +"
new_user = """    const userPrompt = 'Create specific exam questions for subject: ' + subject + '\\n' +
      'These units/topics are from ' + subject + ' syllabus:\\n' +"""

if old_user in content:
    content = content.replace(old_user, new_user)
    print("User prompt updated!")

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("AI controller saved!")