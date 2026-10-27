import { createAnalysisClient } from '@8values/shared/api'
import { createReportClient } from '@8values/shared/reports'
import { labSessionStorage } from './storage/labSession'
declare const __API_BASE_URL__: string
declare const __WEB_BASE_URL__: string
export const API_BASE_URL = __API_BASE_URL__
export const WEB_BASE_URL = __WEB_BASE_URL__
export const client = createAnalysisClient(API_BASE_URL, undefined, 'extension', labSessionStorage)
export const reportClient = createReportClient(API_BASE_URL)
