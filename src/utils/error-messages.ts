import axios from 'axios'

export type ErrorArea = 'AUTH' | 'OCR' | 'FORM' | 'ANNOTATE' | 'AI' | 'OFFICE' | 'PROTECT' | 'UNLOCK' | 'REPAIR' | 'UPLOAD' | 'ENTERPRISE' | 'GENERAL'

export interface FormattedErrorOptions {
  area?: ErrorArea
  fallbackTitle?: string
  fallbackMessage?: string
}

export interface FormattedUserError {
  title: string
  message: string
  diagnosticCode: string
  supportHint: string
  status?: number
}

export function toUserStoreErrorMessage(
  input: unknown,
  options: FormattedErrorOptions = {},
) {
  const formatted = formatUserFacingError(input, options)
  return `${formatted.title}: ${formatted.message} (${formatted.diagnosticCode})`
}

interface ExtractedError {
  status?: number
  detail: string
}

const DEFAULT_SUPPORT_HINT =
  'If this keeps happening, keep the diagnostic code and submit feedback from the page.'

const AREA_DEFAULTS: Record<ErrorArea, { title: string; message: string }> = {
  AUTH: {
    title: 'Account action failed',
    message: 'We could not complete the sign-in request. Please check your details and try again.',
  },
  OCR: {
    title: 'OCR is unavailable right now',
    message: 'The file could not be processed for text recognition. Please retry with a clear file.',
  },
  FORM: {
    title: 'Form processing failed',
    message: 'We could not read or fill this PDF form just now. Please retry with a standard fillable PDF.',
  },
  ANNOTATE: {
    title: 'Annotation failed',
    message: 'We could not apply the annotation to this PDF. Please review the page and coordinates, then try again.',
  },
  AI: {
    title: 'AI analysis failed',
    message: 'The AI request did not finish successfully. Please retry in a moment.',
  },
  OFFICE: {
    title: 'Conversion failed',
    message: 'We could not convert this Office file right now. Please retry with a supported document.',
  },
  PROTECT: {
    title: 'Protection failed',
    message: 'We could not create a protected copy of this PDF. Please retry with a standard PDF file.',
  },
  UNLOCK: {
    title: 'Unlock failed',
    message: 'We could not unlock this PDF. Please confirm the password and retry with a standard protected PDF.',
  },
  REPAIR: {
    title: 'Repair failed',
    message: 'We could not rebuild this PDF. Please retry with a readable standard PDF file.',
  },
  UPLOAD: {
    title: 'Upload failed',
    message: 'The file could not be uploaded successfully. Please retry once the connection is stable.',
  },
  ENTERPRISE: {
    title: 'Enterprise workspace is unavailable',
    message: 'We could not load the requested enterprise data. Please retry in a moment.',
  },
  GENERAL: {
    title: 'Something went wrong',
    message: 'Please try again in a moment.',
  },
}

function extractError(input: unknown): ExtractedError {
  if (axios.isAxiosError(input)) {
    const data = input.response?.data as
      | string
      | {
        detail?: string
        error?: string
        message?: string
      }
      | undefined

    const detail = typeof data === 'string'
      ? data
      : data?.detail || data?.error || data?.message || input.message || ''

    return {
      status: input.response?.status,
      detail,
    }
  }

  if (input instanceof Error) {
    return { detail: input.message }
  }

  if (typeof input === 'string') {
    return { detail: input }
  }

  return { detail: '' }
}

function sanitizeDetail(detail: string) {
  return detail
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function looksInternal(detail: string) {
  const lower = detail.toLowerCase()
  return [
    'traceback',
    'sqlalchemy',
    'psycopg2',
    'invalid input value for enum',
    'stack',
    'exception',
    'celery',
    'internal server error',
    'importerror',
    'nameerror',
    'syntaxerror',
    '/tmp/',
    '\\app\\',
    'c:\\',
  ].some((token) => lower.includes(token))
}

function resolveReason(area: ErrorArea, status?: number, detail = '') {
  const lower = detail.toLowerCase()

  if (lower.includes('scanned') || lower.includes('image-based') || lower.includes('image only')) {
    return {
      code: `${area}-PDF-SCAN`,
      title: 'This PDF needs OCR first',
      message: 'This looks like a scanned or image-only PDF. Run OCR PDF first, then use the converted text with this tool.',
    }
  }

  if (lower.includes('encrypted') || lower.includes('password')) {
    return {
      code: `${area}-PDF-PASSWORD`,
      title: 'Password-protected PDF',
      message: 'This PDF appears to be encrypted or password-protected. Unlock it first, then try again.',
    }
  }

  if (lower.includes('no pages') || lower.includes('empty') || lower.includes('0 bytes')) {
    return {
      code: `${area}-FILE-EMPTY`,
      title: 'File looks empty',
      message: 'The file does not appear to contain readable content. Please choose another file.',
    }
  }

  if (status === 413 || lower.includes('too large') || lower.includes('exceed')) {
    return {
      code: `${area}-${status || 413}-SIZE`,
      title: 'File is too large',
      message: 'This file appears to exceed the current limit. Try a smaller file or split it before processing.',
    }
  }

  if (lower.includes('daily conversion limit') || lower.includes('quota') || lower.includes('limit reached')) {
    return {
      code: `${area}-${status || 403}-QUOTA`,
      title: 'Usage limit reached',
      message: 'You have reached the current limit for this tool. Check your account usage or upgrade before creating more tasks.',
    }
  }

  if (lower.includes('temporarily unavailable') || lower.includes('maintenance')) {
    return {
      code: `${area}-${status || 503}-MAINTENANCE`,
      title: 'Tool is temporarily unavailable',
      message: 'This tool is currently disabled or under maintenance. Please try another tool or come back later.',
    }
  }

  if (lower.includes('payment') && (lower.includes('not configured') || lower.includes('not ready') || lower.includes('disabled'))) {
    return {
      code: `${area}-${status || 503}-PAYMENT`,
      title: 'Payment is not ready',
      message: 'Checkout is not available right now because the payment provider is not ready.',
    }
  }

  if (
    status === 415
    || lower.includes('unsupported')
    || lower.includes('only accepts')
    || lower.includes('choose a pdf')
    || lower.includes('file type')
  ) {
    return {
      code: `${area}-${status || 415}-TYPE`,
      title: 'Unsupported file type',
      message: 'This file type is not supported for the current tool. Choose a supported file and try again.',
    }
  }

  if (area === 'AUTH') {
    if (status === 401 || lower.includes('incorrect') || lower.includes('invalid credentials')) {
      return {
        code: 'AUTH-401-CREDS',
        title: 'Sign-in failed',
        message: 'We could not verify that email and password. Please check them and try again.',
      }
    }

    if (status === 409 || lower.includes('already registered') || lower.includes('already exists')) {
      return {
        code: 'AUTH-409-EXISTS',
        title: 'Account may already exist',
        message: 'This email looks like it may already be registered. Try signing in or use another email address.',
      }
    }

    if (status === 422 || lower.includes('email') || lower.includes('password')) {
      return {
        code: 'AUTH-422-INPUT',
        title: 'Please review your details',
        message: 'One or more fields look invalid. Please review the email address and password requirements.',
      }
    }
  }

  if (status === 400 && lower.includes('invalid http request')) {
    return {
      code: `${area}-400-REQUEST`,
      title: 'Request could not be read',
      message: 'The upload request did not arrive correctly. Please refresh the page and try again.',
    }
  }

  if (status === 400 || status === 422) {
    return {
      code: `${area}-${status}-INPUT`,
      title: 'Please check the file and options',
      message: 'The file or request settings were not accepted. Please review the file type, size, and required fields.',
    }
  }

  if (status === 401) {
    return {
      code: `${area}-401-AUTH`,
      title: 'Please sign in again',
      message: 'Your session may have expired. Please sign in again before using this feature.',
    }
  }

  if (status === 403 || /\bpro\b/.test(lower) || lower.includes('subscription')) {
    return {
      code: `${area}-${status || 403}-ACCESS`,
      title: 'Access is limited for this account',
      message: 'This feature needs a signed-in account with the required access level. Check your plan and try again.',
    }
  }

  if (status === 404) {
    return {
      code: `${area}-404-MISSING`,
      title: 'Requested result was not found',
      message: 'The requested file or job is no longer available. Please retry the task from the beginning.',
    }
  }

  if (status === 429) {
    return {
      code: `${area}-429-BUSY`,
      title: 'Service is busy right now',
      message: 'There are too many requests at the moment. Please wait a little and try again.',
    }
  }

  if (status && status >= 500) {
    return {
      code: `${area}-${status}-SERVER`,
      title: 'Service is temporarily unavailable',
      message: 'The server could not finish the request just now. Please retry shortly.',
    }
  }

  if (lower.includes('network error') || lower.includes('failed to fetch') || lower.includes('timeout')) {
    return {
      code: `${area}-000-NETWORK`,
      title: 'Connection issue detected',
      message: 'The request was interrupted before it completed. Please confirm the server is reachable and try again.',
    }
  }

  if (lower.includes('timed out') || lower.includes('polling')) {
    return {
      code: `${area}-000-TIMEOUT`,
      title: 'This task took too long',
      message: 'The task started but did not finish in time. Please retry once and submit feedback if it repeats.',
    }
  }

  return null
}

export function formatUserFacingError(
  input: unknown,
  options: FormattedErrorOptions = {},
): FormattedUserError {
  const area = options.area || 'GENERAL'
  const fallback = AREA_DEFAULTS[area]
  const extracted = extractError(input)
  const detail = sanitizeDetail(extracted.detail)
  const resolved = resolveReason(area, extracted.status, detail)

  const title = resolved?.title || options.fallbackTitle || fallback.title
  const message = resolved?.message
    || (!looksInternal(detail) && detail ? detail : '')
    || options.fallbackMessage
    || fallback.message

  const code = resolved?.code || `${area}-${extracted.status || '000'}-GENERIC`

  return {
    title,
    message: looksInternal(detail) ? message : message,
    diagnosticCode: `PF-${code}`,
    supportHint: DEFAULT_SUPPORT_HINT,
    status: extracted.status,
  }
}
