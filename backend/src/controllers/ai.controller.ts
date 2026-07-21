import { Request, Response } from 'express'
import { success, error } from '../utils/response'
import prisma from '../config/db'
import axios from 'axios'
import fs from 'fs'
import path from 'path'

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions'
const GROQ_KEY = process.env.GROQ_API_KEY || ''
const MODEL = 'llama-3.1-8b-instant'

async function callGroq(system: string, user: string, maxTokens = 3500): Promise<string> {
  if (!GROQ_KEY) throw new Error('GROQ_API_KEY not set')
  const res = await fetch(GROQ_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: 'system', content: system }, { role: 'user', content: user }],
      max_tokens: maxTokens,
      temperature: 0.7,
    })
  })
  if (!res.ok) throw new Error('Groq error: ' + res.status)
  const d = await res.json() as { choices: { message: { content: string } }[] }
  return d.choices?.[0]?.message?.content || ''
}

// Extract text from PDF URL
async function extractPdfText(url: string): Promise<string> {
  try {
    if (!url) return ''
    console.log('Extracting from:', url.slice(0, 80))

    const pdfParse = require('pdf-parse').default || require('pdf-parse')
    const mammoth = require('mammoth')

    let buffer: Buffer | null = null

    if (url.startsWith('http')) {
      // For Cloudinary - try multiple approaches
      const urlsToTry: string[] = [url]

      // If raw/upload URL - also try image/upload as fallback
      if (url.includes('/raw/upload/')) {
        urlsToTry.push(url.replace('/raw/upload/', '/image/upload/'))
      }
      // If image/upload - also try raw/upload
      if (url.includes('/image/upload/')) {
        urlsToTry.push(url.replace('/image/upload/', '/raw/upload/'))
      }

      for (const tryUrl of urlsToTry) {
        try {
          const response = await fetch(tryUrl, {
            headers: { 'Accept': '*/*' },
            signal: AbortSignal.timeout(15000)
          })
          console.log('Fetch status:', response.status, 'URL:', tryUrl.slice(0, 60))

          if (response.ok) {
            const arrayBuf = await response.arrayBuffer()
            buffer = Buffer.from(arrayBuf)
            console.log('Downloaded:', buffer.length, 'bytes')
            if (buffer.length > 100) break
          }
        } catch (fetchErr: any) {
          console.log('Fetch attempt failed:', fetchErr.message)
        }
      }
    } else {
      // Local file
      const fs = require('fs')
      const path = require('path')
      const fp = path.join(process.cwd(), url)
      if (fs.existsSync(fp)) {
        buffer = fs.readFileSync(fp)
      }
    }

    if (!buffer || buffer.length < 100) {
      console.log('Could not download file or file too small')
      return ''
    }

    const urlLower = url.toLowerCase()
    if (urlLower.includes('.docx')) {
      const r = await mammoth.extractRawText({ buffer })
      const text = (r.value || '').trim()
      console.log('DOCX text extracted:', text.length, 'chars')
      return text.slice(0, 4000)
    } else {
      const d = await pdfParse(buffer)
      const text = (d.text || '').trim()
      console.log('PDF text extracted:', text.length, 'chars')
      return text.slice(0, 4000)
    }

  } catch (e: any) {
    console.log('Extract error:', e.message)
    return ''
  }
}


export const getMaterialUnits = async (req: Request, res: Response) => {
  try {
    const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
    const cid = college?.id || ''
    const { subject } = req.query

    const materials = await prisma.material.findMany({
      where: {
        collegeId: cid,
        isPyq: false,
        ...(subject && { subject: { contains: subject as string, mode: 'insensitive' } })
      },
      select: { unit: true, subject: true, title: true, fileUrl: true }
    })

    const pyqs = await prisma.material.findMany({
      where: {
        collegeId: cid,
        isPyq: true,
        ...(subject && { subject: { contains: subject as string, mode: 'insensitive' } })
      },
      select: { year: true, examType: true, title: true, fileUrl: true }
    })

    const units = Array.from(new Set(materials.map((m: any) => m.unit).filter(Boolean))) as string[]
    const years = Array.from(new Set(pyqs.map((m: any) => m.year?.toString()).filter(Boolean))) as string[]

    // Group materials by unit
    const unitMaterials: Record<string, { title: string; fileUrl: string }[]> = {}
    materials.forEach((m: any) => {
      if (m.unit) {
        if (!unitMaterials[m.unit]) unitMaterials[m.unit] = []
        unitMaterials[m.unit].push({ title: m.title, fileUrl: m.fileUrl })
      }
    })

    return success(res, {
      units,
      years,
      unitMaterials,
      hasMaterials: materials.length > 0,
      hasPyqs: pyqs.length > 0
    })
  } catch (err: any) { return error(res, err.message, 500) }
}

export const generateQuestions = async (req: Request, res: Response) => {
  try {
    const { subject, units, extraTopics, sections, difficulty, pyqYears, usePyqs } = req.body

    const selectedTopics: string[] = [
      ...(Array.isArray(units) ? units.filter(Boolean) : []),
      ...(Array.isArray(extraTopics) ? extraTopics.filter(Boolean) : [])
    ]

    if (selectedTopics.length === 0) {
      return error(res, 'Please select at least one unit or topic', 400)
    }

    const college = await prisma.college.findFirst({ orderBy: { createdAt: 'asc' } })
    const cid = college?.id || ''

    // Fetch actual materials for selected units
    const materials = await prisma.material.findMany({
      where: {
        collegeId: cid,
        isPyq: false,
        subject: { contains: subject, mode: 'insensitive' },
        unit: { in: selectedTopics }
      },
      select: { unit: true, title: true, fileUrl: true, fileName: true }
    })

    console.log('Found materials for generation:', materials.length)

    // Extract PDF content from each material
    let materialContent = ''
    for (const mat of materials.slice(0, 5)) { // Max 5 files to avoid timeout
      console.log('Extracting from:', mat.title, mat.fileUrl)
      const ext = path.extname(mat.fileName || '').toLowerCase()
      if (ext === '.pdf' || mat.fileUrl?.includes('.pdf') || mat.fileUrl?.includes('cloudinary')) {
        const text = await extractPdfText(mat.fileUrl)
        if (text.trim()) {
          materialContent += '\n--- ' + mat.unit + ': ' + mat.title + ' ---\n' + text.slice(0, 1500) + '\n'
          console.log('Extracted', text.length, 'chars from', mat.title)
        }
      }
    }

    // Fetch PYQ content if requested
    let pyqContent = ''
    if (usePyqs && pyqYears?.length > 0) {
      const pyqMats = await prisma.material.findMany({
        where: {
          collegeId: cid,
          isPyq: true,
          year: { in: pyqYears.map((y: string) => parseInt(y)) }
        },
        select: { title: true, fileUrl: true, year: true, fileName: true }
      })
      for (const pq of pyqMats.slice(0, 2)) {
        const ext = path.extname(pq.fileName || '').toLowerCase()
        if (ext === '.pdf' || pq.fileUrl?.includes('cloudinary')) {
          const text = await extractPdfText(pq.fileUrl)
          if (text.trim()) {
            pyqContent += '\nPYQ ' + pq.year + ' - ' + pq.title + ':\n' + text.slice(0, 1000) + '\n'
          }
        }
      }
    }

    const topicList = selectedTopics.map((t: string, i: number) => (i + 1) + '. ' + t).join('\n')
    const sectionsDesc = (sections || []).map((s: any) =>
      'Section ' + s.name + ': ' + s.total + ' questions of ' + s.marks + ' marks each'
    ).join('\n')

    const hasContent = materialContent.trim().length > 0

    const sysPrompt = hasContent
      ? 'You are an exam paper setter. The study material content is given below. You MUST generate questions ONLY from this exact content. Do NOT use any outside knowledge. Every question answer must be found in the provided content. Return ONLY JSON array.'
      : 'You are a university exam paper setter. Generate questions ONLY from these topics: ' + selectedTopics.join(', ') + '. Return ONLY JSON array.'

    const userPrompt = 'Create exam questions for: ' + subject + '\n' +
      'Topics/Units: ' + topicList + '\n' +
      'Difficulty: ' + (difficulty || 'mixed') + '\n\n' +
      (hasContent
        ? 'STUDY MATERIAL CONTENT (generate questions FROM THIS CONTENT ONLY):\n' + materialContent + '\n'
        : '') +
      (pyqContent ? 'PREVIOUS YEAR PAPER STYLE REFERENCE:\n' + pyqContent + '\n' : '') +
      '\nSections needed:\n' + sectionsDesc + '\n\n' +
      'RULES:\n' +
      '- Questions must come from the ' + (hasContent ? 'study material content above' : 'given topics') + '\n' +
      '- "unit" field = exact unit/topic name from: ' + selectedTopics.join(' | ') + '\n' +
      '- Cover all units\n' +
      '\nReturn ONLY JSON array:\n' +
      '[{"id":1,"section":"A","questionNo":1,"text":"specific question from the material","marks":' +
      (sections?.[0]?.marks || 2) + ',"unit":"' + (selectedTopics[0] || subject) +
      '","difficulty":"easy","type":"short"}]'

    console.log('Generating with content length:', materialContent.length)
    const raw = await callGroq(sysPrompt, userPrompt)

    let questions = []
    try {
      const cleaned = raw.replace(/```json|```/g, '').trim()
      const match = cleaned.match(/\[[\s\S]*\]/)
      questions = JSON.parse(match ? match[0] : cleaned)
    } catch {
      return error(res, 'AI format error. Try again.', 500)
    }

    if (!Array.isArray(questions) || questions.length === 0) {
      return error(res, 'No questions generated. Try again.', 500)
    }

    return success(res, {
      questions,
      metadata: {
        subject,
        topics: selectedTopics,
        totalQuestions: questions.length,
        contentExtracted: hasContent,
        materialsScanned: materials.length
      }
    })
  } catch (err: any) {
    console.error('Generate error:', err)
    return error(res, err.message, 500)
  }
}

export const aiChat = async (req: Request, res: Response) => {
  try {
    const { message, subject, history, image } = req.body
    if (!GROQ_KEY) return error(res, 'GROQ_API_KEY not configured', 500)

    const userContent = image
      ? (message || 'Analyze and solve this problem') +
        '\n[Student shared an image about ' + (subject || 'their subject') +
        '. Provide detailed step-by-step solution.]'
      : message

    if (!userContent) return error(res, 'Message required', 400)

    const msgs = [
      ...(history || []).slice(-6).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user', content: userContent }
    ]

    const res2 = await fetch(GROQ_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + GROQ_KEY },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          {
            role: 'system',
            content: 'You are HAYAT, an expert AI tutor for ' +
              (subject || 'all subjects') +
              ' at K.R Mangalam University. Be helpful and educational.'
          },
          ...msgs
        ],
        max_tokens: 2048,
        temperature: 0.7,
      })
    })

    if (!res2.ok) return error(res, 'AI service error: ' + res2.status, 500)
    const d = await res2.json() as { choices: { message: { content: string } }[] }
    const reply = d.choices?.[0]?.message?.content
    if (!reply) return error(res, 'No response from AI', 500)
    return success(res, { reply })
  } catch (err: any) { return error(res, 'AI unavailable: ' + err.message, 500) }
}

export const checkAnswer = async (req: Request, res: Response) => {
  try {
    const { question, answer, subject, marks } = req.body
    const raw = await callGroq(
      'Grade this answer. Return ONLY valid JSON.',
      'Q: ' + question + '\nA: ' + answer + '\nSubject: ' + subject +
      '\nMax marks: ' + marks +
      '\nReturn: {"marksAwarded":0,"percentage":0,"grade":"A","feedback":"text"}'
    )
    const match = raw.match(/\{[\s\S]*\}/)
    return success(res, JSON.parse(match ? match[0] : raw.replace(/```json|```/g, '').trim()))
  } catch (err: any) { return error(res, err.message, 500) }
}
