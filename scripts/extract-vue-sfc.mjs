#!/usr/bin/env node
/**
 * Vue SFC 预处理脚本：提取 <script> / <style> 为独立文件，CSS 类名归一化
 *
 * 解决 jscpd 检测 Vue 重复代码的三个问题：
 * 1. <script> 和 <style> 被当作不同区块 → 提取为独立文件，跨文件比对
 * 2. minLines 过滤短克隆 → 配合 .jscpd.json 降低阈值
 * 3. CSS 类名不同但结构相同 → 类名替换为 __CLS_N__ 占位符
 */

import { readFileSync, writeFileSync, mkdirSync, rmSync, readdirSync, statSync } from 'fs'
import { join, relative, sep } from 'path'

const ROOT = join(import.meta.dirname, '..')
const VUE_SRC = join(ROOT, 'rag-web', 'src')
const OUT_DIR = join(ROOT, '.jscpd-extracted', 'rag-web')

// 清空输出目录
rmSync(OUT_DIR, { recursive: true, force: true })

function walkDir(dir, ext, files = []) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) {
      walkDir(full, ext, files)
    } else if (entry.endsWith(ext)) {
      files.push(full)
    }
  }
  return files
}

/**
 * 从 Vue SFC 内容中提取指定标签块
 */
function extractBlocks(content, tagName) {
  const blocks = []
  const regex = new RegExp(`<${tagName}[^>]*>([\\s\\S]*?)<\\/${tagName}>`, 'g')
  let match
  while ((match = regex.exec(content)) !== null) {
    blocks.push(match[1].trim())
  }
  return blocks
}

/**
 * CSS 类名归一化：将 .xxx 替换为 .__CLS_N__
 * 保留伪类和伪元素（:hover, ::before 等）
 */
function normalizeCssClassNames(css) {
  let counter = 0
  const classMap = new Map()

  return css.replace(/\.([a-zA-Z_][\w-]*)/g, (match, className) => {
    // 跳过已知的伪类/伪元素前缀
    if (className.startsWith('deep') || className.startsWith('global')) {
      return match
    }
    if (!classMap.has(className)) {
      classMap.set(className, `__CLS_${counter++}__`)
    }
    return `.${classMap.get(className)}`
  })
}

/**
 * 处理单个 Vue 文件
 */
function processVueFile(filePath) {
  const content = readFileSync(filePath, 'utf-8')
  const relPath = relative(VUE_SRC, filePath).replace(/\.vue$/, '')
  const outSubDir = join(OUT_DIR, relPath)
  mkdirSync(outSubDir, { recursive: true })

  // 提取 <script> 块
  const scriptBlocks = extractBlocks(content, 'script')
  scriptBlocks.forEach((block, i) => {
    const suffix = scriptBlocks.length > 1 ? `_${i}` : ''
    const ext = content.includes('lang="ts"') || content.includes("lang='ts'") ? 'ts' : 'js'
    writeFileSync(join(outSubDir, `script${suffix}.${ext}`), block + '\n')
  })

  // 提取 <style> 块，并做类名归一化
  const styleBlocks = extractBlocks(content, 'style')
  styleBlocks.forEach((block, i) => {
    const suffix = styleBlocks.length > 1 ? `_${i}` : ''
    const normalized = normalizeCssClassNames(block)
    writeFileSync(join(outSubDir, `style${suffix}.css`), normalized + '\n')
  })
}

// 主流程
const vueFiles = walkDir(VUE_SRC, '.vue')
console.log(`Found ${vueFiles.length} Vue files in rag-web/src`)

for (const file of vueFiles) {
  processVueFile(file)
}

console.log(`Extracted to ${OUT_DIR}`)
