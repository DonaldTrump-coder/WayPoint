#!/usr/bin/env node
const fs = require('fs')
const path = require('path')

const file = path.join(__dirname, '..', 'node_modules', 'frappe-gantt', 'dist', 'frappe-gantt.umd.js')
const fileEs = path.join(__dirname, '..', 'node_modules', 'frappe-gantt', 'dist', 'frappe-gantt.es.js')
const marker = '/*wp-clientx-drag-patch*/'
const markerV2 = '/*wp-clientx-drag-patch-v2*/'

if (!fs.existsSync(file)) {
  console.warn('[patch-frappe-gantt] 未找到 frappe-gantt.umd.js，跳过')
  process.exit(0)
}

let src = fs.readFileSync(file, 'utf-8')
let srcEs = fs.existsSync(fileEs) ? fs.readFileSync(fileEs, 'utf-8') : null

if (src.includes('wp-clientx-drag-patch-v2')) {
  console.log('[patch-frappe-gantt] 已打过最新补丁（v2），跳过')
  process.exit(0)
}
if (src.includes(marker)) {
  console.log('[patch-frappe-gantt] 检测到 v1 旧补丁，升级到 v2（滚动补偿）...')
}

const replacements = [
  ['let t=!1,e=0,i=0', 'let t=!1,e=0,w=0,i=0'],
  ['Math.abs((l.offsetX||l.layerX)-g)>10', 'Math.abs((l.clientX)-g)>10'],
  ['e=l.offsetX||l.layerX', 'e=l.clientX,w=this.$container.scrollLeft'],
  ['e=l.clientX,a=p.getAttribute', 'e=l.clientX,w=this.$container.scrollLeft,a=p.getAttribute'],
  ['(l.offsetX||l.layerX)-e', '(l.clientX)-e+(this.$container.scrollLeft-w)'],
  ['(l.clientX)-e;o.forEach', '(l.clientX)-e+(this.$container.scrollLeft-w);o.forEach'],
  ['c.on(this.$svg,"mousemove",".bar-wrapper, .handle"', 'c.on(document,"mousemove",".bar-wrapper, .handle"'],
  ['c.on(this.$svg,"mousemove",l=>', 'c.on(document,"mousemove",l=>'],
  ['get_snap_position(t,e){let i=1;', 'get_snap_position(t,e){return t;let i=1;'],
  ['const t=this.$bar,e=3', 'const t=this.$bar,e=6'],
  ['t.getEndX()-e/2,y:t.getY()', 't.getEndX(),y:t.getY()'],
  ['t.getX()-e/2,y:t.getY()', 't.getX()-e,y:t.getY()'],
  ['querySelector(".handle.left").setAttribute("x",t.getX())', 'querySelector(".handle.left").setAttribute("x",t.getX()-6)'],
]

let applied = 0
const isV1 = src.includes(marker)
const expected = isV1 ? 4 : 5
for (const [from, to] of replacements) {
  if (src.includes(from)) {
    src = src.split(from).join(to)
    applied++
  }
}

if (srcEs) {
  const esReplacements = [
    ['let t = !1, e = 0, i = 0', 'let t = !1, e = 0, w = 0, i = 0'],
    ['Math.abs((l.offsetX || l.layerX) - g) > 10', 'Math.abs((l.clientX) - g) > 10'],
    ['e = l.offsetX || l.layerX', 'e = l.clientX, w = this.$container.scrollLeft'],
    ['(l.offsetX || l.layerX) - e', '(l.clientX) - e + (this.$container.scrollLeft - w)'],
    ['p.on(this.$svg, "mousemove", ".bar-wrapper, .handle"', 'p.on(document, "mousemove", ".bar-wrapper, .handle"'],
    ['p.on(this.$svg, "mousemove", (l) => {', 'p.on(document, "mousemove", (l) => {'],
    ['p.on(this.$svg, "mousemove", (o) => {', 'p.on(document, "mousemove", (o) => {'],
    ['get_snap_position(t, e) {\n    let i = 1;', 'get_snap_position(t, e) {\n    return t;\n    let i = 1;'],
    ['const t = this.$bar, e = 3;', 'const t = this.$bar, e = 6;'],
    ['x: t.getEndX() - e / 2,', 'x: t.getEndX(),'],
    ['x: t.getX() - e / 2,', 'x: t.getX() - e,'],
    ['querySelector(".handle.left").setAttribute("x", t.getX())', 'querySelector(".handle.left").setAttribute("x", t.getX() - 6)'],
  ]
  let esApplied = 0
  for (const [from, to] of esReplacements) {
    if (srcEs.includes(from)) {
      srcEs = srcEs.split(from).join(to)
      esApplied++
    }
  }
  if (!srcEs.includes('wp-clientx-drag-patch-v2')) {
    srcEs = '/*!wp-clientx-drag-patch-v2 clientX drag patch v2 (auto) */\n' + srcEs
  }
  fs.writeFileSync(fileEs, srcEs, 'utf-8')
  console.log(`[patch-frappe-gantt] es.js 补丁应用成功（${esApplied} 处替换）`)
}

if (applied >= expected) {
  src = src.replace(/\/\*\*?!/, `/*!${markerV2} clientX drag patch v2 (scroll-compensated, auto) */\n/**!`)
  if (!src.includes(markerV2)) src = `/*!${markerV2} clientX drag patch v2 (auto) */\n` + src
  fs.writeFileSync(file, src, 'utf-8')
  console.log(`[patch-frappe-gantt] umd.js 补丁应用成功（${applied}/${expected} 处替换）`)
} else {
  console.warn(`[patch-frappe-gantt] umd.js 仅替换 ${applied}/${expected} 处，库版本可能已变化，请检查！`)
  process.exit(1)
}
