const dateLabel = value => new Intl.DateTimeFormat('en-US', {
  month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC',
}).format(new Date(`${value}T12:00:00Z`))

export function suggestedQuestions(catalog) {
  const saved = catalog?.zips?.find(zip => zip.nights.length)
  if (!saved) return []
  const night = saved.nights[0]
  const label = dateLabel(night)
  const questions = [
    { label: 'Find the cheapest', text: `Show the three cheapest saved hotels near ZIP ${saved.postcode} for the night of ${label}, with at least one room available.` },
    { label: 'Stay within a budget', text: `Which saved hotels near ZIP ${saved.postcode} cost $150 or less for the night of ${label}, with at least one room available?` },
  ]
  const next = new Date(`${night}T12:00:00Z`)
  next.setUTCDate(next.getUTCDate() + 1)
  if (saved.nights.includes(next.toISOString().slice(0, 10))) {
    next.setUTCDate(next.getUTCDate() + 1)
    questions.push({ label: 'Compare two nights', text: `Compare the cheapest saved hotels near ZIP ${saved.postcode}, checking in ${label} and checking out ${dateLabel(next.toISOString().slice(0, 10))}. Show full stay totals and available rooms.` })
  }
  return questions
}

// Text nodes only: no HTML injection or dependency on Markdown rendering.
export function answerBlocks(text) {
  const blocks = []
  for (const paragraph of text.trim().split(/\n\s*\n/)) {
    const lines = paragraph.split('\n')
    if (lines.every(line => /^\s*(?:\d+[.)]|[-•])\s+/.test(line))) {
      const items = lines.map(line => line.replace(/^\s*(?:\d+[.)]|[-•])\s+/, ''))
      const previous = blocks.at(-1)
      if (previous?.kind === 'list') previous.items.push(...items)
      else blocks.push({ kind: 'list', items })
    } else {
      blocks.push({ kind: 'paragraph', text: paragraph })
    }
  }
  return blocks
}

export function readableError(text) {
  if (/query must|only one bounded|query rejected|model must specify|query parameters/i.test(text)) {
    return 'I couldn’t complete that comparison. Try a suggested question with a saved ZIP and exact stay dates.'
  }
  return text
}
