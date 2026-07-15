# Run from BACKEND folder
with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Find and fix the generate function system prompt
old = """    const systemPrompt = `You are a strict university exam paper setter.
ABSOLUTE RULE: You MUST ONLY create questions from these EXACT topics: ${selectedTopics.join(', ')}
DO NOT use any other topics. DO NOT add general knowledge questions.
Every single question text must clearly mention or relate to one of the given topics.
Return ONLY valid JSON array. No markdown. No explanation. No text before or after the JSON.`"""

new = """    const systemPrompt = `You are a university exam paper setter for K.R. Mangalam University.
CRITICAL RULES - MUST FOLLOW:
1. ONLY generate questions from these SPECIFIC topics: ${selectedTopics.join(', ')}
2. NEVER add questions from topics not in this list
3. Each question's "unit" field must exactly match one of: ${selectedTopics.join(' | ')}
4. Return ONLY a valid JSON array - no markdown, no backticks, no explanation
5. If asked about "${selectedTopics[0]}", only ask about "${selectedTopics[0]}"
6. Distribute questions EVENLY across all ${selectedTopics.length} given topics`"""

if old in content:
    content = content.replace(old, new)
    print("System prompt fixed!")
else:
    # Find any systemPrompt in generateQuestions
    content = re.sub(
        r'const systemPrompt = `.*?`',
        f"""const systemPrompt = `You are a university exam setter.
STRICT RULE: ONLY use these topics: ${{selectedTopics.join(', ')}}
NO other topics allowed. Return ONLY JSON array.`""",
        content,
        flags=re.DOTALL,
        count=1
    )
    print("System prompt replaced!")

# Fix userPrompt to be more explicit
old_user = "const userPrompt ="
if old_user in content:
    # Add topic verification
    content = content.replace(
        "return success(res, {\n      questions: verifiedQuestions.length > 0 ? verifiedQuestions : questions,",
        """// Double-check: filter questions not matching topics
    const finalQuestions = questions.filter((q: any) => {
      if (!q.text) return false
      const textLower = (q.text + ' ' + (q.unit || '')).toLowerCase()
      return selectedTopics.some((t: string) => 
        t.toLowerCase().split(' ').some(word => word.length > 3 && textLower.includes(word.toLowerCase()))
      )
    })
    
    return success(res, {
      questions: finalQuestions.length >= 3 ? finalQuestions : questions,"""
    )

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("AI controller updated!")