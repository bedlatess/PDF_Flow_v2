type LocaleTree = Record<string, unknown>

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
