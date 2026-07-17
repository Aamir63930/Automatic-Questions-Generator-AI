with open("src/controllers/ai.controller.ts", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the system prompt to be VERY strict about using content
old = """    const sysPrompt = hasContent
      ? 'You are an expert exam paper setter. Generate questions STRICTLY from the provided study material content. Every question must be based on the actual content given below.'
      : 'You are a university exam paper setter. Generate questions ONLY from these topics: ' + selectedTopics.join(', ') + '. No other topics allowed.'"""

new = """    const sysPrompt = hasContent
      ? 'You are an exam paper setter. The study material content is given below. You MUST generate questions ONLY from this exact content. Do NOT use any outside knowledge. Every question answer must be found in the provided content. Return ONLY JSON array.'
      : 'You are a university exam paper setter. Generate questions ONLY from these topics: ' + selectedTopics.join(', ') + '. Return ONLY JSON array.'"""

content = content.replace(old, new)

# Make userPrompt stronger
old2 = """      (hasContent
        ? 'STUDY MATERIAL CONTENT (generate questions FROM THIS CONTENT ONLY):\\\\n' + materialContent + '\\\\n'
        : '') +"""

new2 = """      (hasContent
        ? 'STUDY MATERIAL CONTENT:\\n' +
          '=== START OF MATERIAL ===\\n' + materialContent + '\\n=== END OF MATERIAL ===\\n' +
          '\\nIMPORTANT: Read the above content carefully. Generate questions ONLY from facts, concepts, and information present in the above material. Do NOT use any outside knowledge.\\n'
        : '') +"""

content = content.replace(old2, new2)

with open("src/controllers/ai.controller.ts", "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed!")