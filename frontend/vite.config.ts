import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const currentDir = path.dirname(fileURLToPath(import.meta.url))

function loadEnvSettings() {
  const envPath = path.resolve(currentDir, '..', '.env')
  if (!fs.existsSync(envPath)) {
    return {}
  }

  const content = fs.readFileSync(envPath, 'utf8')
  const values: Record<string, string> = {}

  for (const line of content.split(/\r?\n/)) {
    const cleaned = line.trim()
    if (!cleaned || cleaned.startsWith('#') || !cleaned.includes('=')) {
      continue
    }

    const [key, ...rest] = cleaned.split('=')
    values[key.trim()] = rest.join('=').trim().replace(/^['"]|['"]$/g, '')
  }

  return values
}

const envSettings = loadEnvSettings()
const frontendHost = envSettings.FRONTEND_HOST ?? '0.0.0.0'
const frontendPort = Number(envSettings.FRONTEND_PORT ?? '5173')
const backendHost = envSettings.BACKEND_HOST ?? '127.0.0.1'
const backendPort = Number(envSettings.BACKEND_PORT ?? '8000')
const apiBaseUrl = envSettings.VITE_API_BASE_URL ?? '/api'
const backendTarget = `http://${backendHost}:${backendPort}`
const frontendPublicUrl = envSettings.NGROK_FRONTEND_URL ?? ''

function extractHost(value: string) {
  if (!value) {
    return ''
  }

  try {
    return new URL(value).host
  } catch {
    return value.replace(/^https?:\/\//, '').split('/')[0]
  }
}

const allowedHosts = Array.from(
  new Set(['localhost', '127.0.0.1', extractHost(frontendPublicUrl)].filter(Boolean)),
)

export default defineConfig({
  plugins: [react()],
  server: {
    host: frontendHost,
    port: frontendPort,
    allowedHosts,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
      },
      '/media': {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
  define: {
    'import.meta.env.VITE_API_BASE_URL': JSON.stringify(apiBaseUrl),
  },
})
