<script setup>
import { computed } from 'vue'
import 'github-markdown-css/github-markdown-light.css'

const props = defineProps({
  content: { type: String, default: '' },
})

const escapeHtml = (s) => s
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;')

const inline = (s) => {
  return s
    .replace(/`([^`]+)`/g, (m, code) => `<code>${escapeHtml(code)}</code>`)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
    .replace(/~~([^~]+)~~/g, '<del>$1</del>')
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
}

const render = computed(() => {
  const raw = props.content || ''
  const lines = raw.replace(/\r\n/g, '\n').split('\n')
  const html = []
  let i = 0
  let inCode = false
  let codeBuf = []
  let codeLang = ''
  let listType = null  // 'ul' | 'ol'
  let quoteBuf = []

  const flushList = () => {
    if (listType) { html.push(`</${listType}>`); listType = null }
  }
  const flushQuote = () => {
    if (quoteBuf.length) {
      html.push(`<blockquote>${quoteBuf.map(l => `<p>${inline(l)}</p>`).join('')}</blockquote>`)
      quoteBuf = []
    }
  }

  for (; i < lines.length; i++) {
    const line = lines[i]

    if (line.trim().startsWith('```')) {
      if (!inCode) {
        flushList(); flushQuote()
        inCode = true
        codeBuf = []
        codeLang = line.trim().slice(3).trim()
        continue
      }
      inCode = false
      const langClass = codeLang ? ` class="language-${escapeHtml(codeLang)}"` : ''
      html.push(`<pre${langClass}><code>${escapeHtml(codeBuf.join('\n'))}</code></pre>`)
      continue
    }
    if (inCode) { codeBuf.push(line); continue }

    if (!line.trim()) { flushList(); flushQuote(); continue }

    const h = line.match(/^(#{1,4})\s+(.*)$/)
    if (h) {
      flushList(); flushQuote()
      const level = h[1].length
      html.push(`<h${level}>${inline(h[2])}</h${level}>`)
      continue
    }

    if (/^([-*_])\s*(\1\s*){2,}$/.test(line)) { flushList(); flushQuote(); html.push('<hr />'); continue }

    if (line.startsWith('>')) {
      flushList()
      quoteBuf.push(line.replace(/^>\s?/, ''))
      continue
    }

    const ul = line.match(/^\s*[-*+]\s+(.*)$/)
    if (ul) {
      flushQuote()
      const task = ul[1].match(/^\[( |x|X)\]\s+(.*)$/)
      if (task) {
        if (listType !== 'ul') { flushList(); html.push('<ul>'); listType = 'ul' }
        const checked = task[1] !== ' '
        html.push(`<li class="task-list-item"><input type="checkbox" disabled ${checked ? 'checked' : ''}> ${inline(task[2])}</li>`)
      } else {
        if (listType !== 'ul') { flushList(); html.push('<ul>'); listType = 'ul' }
        html.push(`<li>${inline(ul[1])}</li>`)
      }
      continue
    }

    const ol = line.match(/^\s*\d+[.)]\s+(.*)$/)
    if (ol) {
      flushQuote()
      if (listType !== 'ol') { flushList(); html.push('<ol>'); listType = 'ol' }
      html.push(`<li>${inline(ol[1])}</li>`)
      continue
    }

    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const headerCells = line.trim().slice(1, -1).split('|').map(c => c.trim())
      const next = lines[i + 1]
      if (next && /^\s*\|?[\s:|-]+\|?\s*$/.test(next) && next.includes('-')) {
        flushList(); flushQuote()
        const sepCells = next.trim().slice(1, -1).split('|').map(c => c.trim())
        const alignments = sepCells.map(c => {
          if (c.startsWith(':') && c.endsWith(':')) return ' style="text-align:center"'
          if (c.endsWith(':')) return ' style="text-align:right"'
          if (c.startsWith(':')) return ' style="text-align:left"'
          return ''
        })
        html.push('<table><thead><tr>')
        headerCells.forEach((c, idx) => {
          html.push(`<th${alignments[idx] || ''}>${inline(c)}</th>`)
        })
        html.push('</tr></thead><tbody>')
        i += 1
        while (i + 1 < lines.length && lines[i + 1].trim().startsWith('|') && lines[i + 1].trim().endsWith('|')) {
          i += 1
          const cells = lines[i].trim().slice(1, -1).split('|').map(c => c.trim())
          html.push('<tr>')
          cells.forEach((c, idx) => {
            html.push(`<td${alignments[idx] || ''}>${inline(c)}</td>`)
          })
          html.push('</tr>')
        }
        html.push('</tbody></table>')
        continue
      }
    }

    flushList(); flushQuote()
    html.push(`<p>${inline(line)}</p>`)
  }
  flushList(); flushQuote()
  if (inCode) html.push(`<pre><code>${escapeHtml(codeBuf.join('\n'))}</code></pre>`)

  return html.join('\n')
})
</script>

<template>
  <div class="markdown-body md-renderer" v-html="render"></div>
</template>

<style>
.md-renderer {
  font-size: 15px;
  line-height: 1.7;
  word-break: break-word;
}
.md-renderer .task-list-item { list-style: none; margin-left: -20px; }
.md-renderer .task-list-item input { margin-right: 8px; }
</style>
