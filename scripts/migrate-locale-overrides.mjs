import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const ts = require('typescript')

const root = process.cwd()
const localesDir = path.join(root, 'src', 'locales')
const defaultSource = path.join(localesDir, 'overrides.ts')
const localeFiles = {
  en: path.join(localesDir, 'en.json'),
  zh: path.join(localesDir, 'zh.json'),
  es: path.join(localesDir, 'es.json'),
}

const args = new Set(process.argv.slice(2))
const write = args.has('--write')
const sourceArgIndex = process.argv.indexOf('--source')
const sourceFile =
  sourceArgIndex >= 0 && process.argv[sourceArgIndex + 1]
    ? path.resolve(process.argv[sourceArgIndex + 1])
    : defaultSource

const isPlainObject = (value) =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const deepMerge = (base, overrides) => {
  const result = { ...base }

  for (const [key, value] of Object.entries(overrides ?? {})) {
    if (isPlainObject(value) && isPlainObject(result[key])) {
      result[key] = deepMerge(result[key], value)
    } else {
      result[key] = value
    }
  }

  return result
}

const readJson = (file) => JSON.parse(fs.readFileSync(file, 'utf8'))
const stableJson = (value) => `${JSON.stringify(value, null, 2)}\n`

const loadLegacyOverrides = (file) => {
  const source = fs.readFileSync(file, 'utf8')
  if (!source.includes('localeOverrides') || !source.includes('sharedEn')) {
    return null
  }

  const transpiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
    fileName: file,
  }).outputText

  const sandbox = {
    exports: {},
    module: { exports: {} },
  }
  vm.runInNewContext(transpiled, sandbox, { filename: file, timeout: 5000 })

  return sandbox.exports.localeOverrides ?? sandbox.module.exports.localeOverrides ?? null
}

const migratedOverridesSource = `type LocaleTree = Record<string, unknown>

const isPlainObject = (value: unknown): value is LocaleTree =>
  typeof value === 'object' && value !== null && !Array.isArray(value)

const deepMerge = (base: LocaleTree, overrides: LocaleTree): LocaleTree => {
  const result: LocaleTree = { ...base }

  for (const [key, value] of Object.entries(overrides)) {
    if (isPlainObject(value) && isPlainObject(result[key])) {
      result[key] = deepMerge(result[key] as LocaleTree, value)
    } else {
      result[key] = value
    }
  }

  return result
}

export const mergeLocaleMessages = <T extends LocaleTree>(base: T, overrides: LocaleTree): T =>
  deepMerge(base, overrides) as T

export const localeOverrides = {
  en: {},
  zh: {},
  es: {},
} as const
`

const validateJsonFiles = () => {
  for (const [locale, file] of Object.entries(localeFiles)) {
    readJson(file)
    console.log(`validated ${locale}: ${path.relative(root, file)}`)
  }
}

const legacyOverrides = loadLegacyOverrides(sourceFile)

if (!legacyOverrides) {
  validateJsonFiles()
  console.log('No legacy override payload found; locale JSON files are already the baseline source.')
  process.exit(0)
}

const mergedMessages = Object.fromEntries(
  Object.entries(localeFiles).map(([locale, file]) => [
    locale,
    deepMerge(readJson(file), legacyOverrides[locale] ?? {}),
  ]),
)

if (!write) {
  for (const [locale, messages] of Object.entries(mergedMessages)) {
    console.log(
      `${locale}: ${Object.keys(messages).length} top-level namespaces ready for migration`,
    )
  }
  console.log('Dry run only. Re-run with --write to update locale JSON and shrink overrides.ts.')
  process.exit(0)
}

for (const [locale, file] of Object.entries(localeFiles)) {
  fs.writeFileSync(file, stableJson(mergedMessages[locale]), 'utf8')
  console.log(`wrote ${path.relative(root, file)}`)
}

if (path.resolve(sourceFile) === path.resolve(defaultSource)) {
  fs.writeFileSync(defaultSource, migratedOverridesSource, 'utf8')
  console.log(`wrote ${path.relative(root, defaultSource)}`)
} else {
  console.log('source file was not the active overrides.ts; compatibility wrapper was not rewritten.')
}
