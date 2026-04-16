import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'
const SESSION_STORAGE_KEY = 'file-sharing-platform:keys'

type UploadRecord = {
  id: number
  key: string
  filename: string
  status: 'Pending' | 'Downloaded'
  uploaded_at: string
  downloaded_at: string | null
}

const api = axios.create({
  baseURL: API_BASE_URL,
})

function readStoredKeys() {
  try {
    const raw = window.localStorage.getItem(SESSION_STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === 'string') : []
  } catch {
    return []
  }
}

function persistKey(key: string) {
  const keys = Array.from(new Set([key, ...readStoredKeys()]))
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(keys))
}

function formatDate(value: string | null) {
  if (!value) {
    return 'Not downloaded yet'
  }

  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadMessage, setUploadMessage] = useState('')
  const [latestKey, setLatestKey] = useState('')
  const [downloadKey, setDownloadKey] = useState('')
  const [downloadMessage, setDownloadMessage] = useState('')
  const [downloadError, setDownloadError] = useState('')
  const [downloading, setDownloading] = useState(false)
  const [records, setRecords] = useState<UploadRecord[]>([])
  const [loadingRecords, setLoadingRecords] = useState(true)
  const [recordsError, setRecordsError] = useState('')

  async function loadRecords(showLoading = false) {
    const keys = readStoredKeys()
    if (showLoading) {
      setLoadingRecords(true)
    }

    if (!keys.length) {
      setRecords([])
      setRecordsError('')
      setLoadingRecords(false)
      return
    }

    try {
      const response = await api.get<UploadRecord[]>('/files/', {
        params: { keys: keys.join(',') },
      })
      setRecords(response.data)
      setRecordsError('')
    } catch {
      setRecordsError('Could not refresh the dashboard right now.')
    } finally {
      setLoadingRecords(false)
    }
  }

  useEffect(() => {
    void loadRecords(true)

    const intervalId = window.setInterval(() => {
      void loadRecords()
    }, 4000)

    return () => {
      window.clearInterval(intervalId)
    }
  }, [])

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const fileInput = form.elements.namedItem('file') as HTMLInputElement | null

    if (!selectedFile) {
      setUploadError('Choose a file before uploading.')
      return
    }

    setUploading(true)
    setUploadError('')
    setUploadMessage('')
    setLatestKey('')

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await api.post<{ key: string }>('/upload/', formData)
      setLatestKey(response.data.key)
      setUploadMessage('Upload completed successfully.')
      persistKey(response.data.key)
      setSelectedFile(null)
      if (fileInput) {
        fileInput.value = ''
      }
      void loadRecords()
    } catch (error) {
      setLatestKey('')
      setUploadMessage('')
      if (axios.isAxiosError(error) && typeof error.response?.data === 'object' && error.response?.data) {
        const detail = (error.response.data as { detail?: string }).detail
        setUploadError(detail ?? 'Upload failed. Please try again.')
      } else {
        setUploadError('Upload failed. Please try again.')
      }
    } finally {
      setUploading(false)
    }
  }

  async function handleDownload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setDownloadError('')
    setDownloadMessage('')
    setUploadMessage('')

    const trimmedKey = downloadKey.trim()
    if (!/^\d{6}$/.test(trimmedKey)) {
      setDownloadError('Enter a valid 6-digit key.')
      return
    }

    setDownloading(true)

    try {
      const response = await api.post('/download/', { key: trimmedKey }, { responseType: 'blob' })
      const contentDisposition = response.headers['content-disposition'] as string | undefined
      const filenameMatch = contentDisposition?.match(/filename="?(.*?)"?$/)
      const filename = filenameMatch?.[1] ?? `download-${trimmedKey}`
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      window.URL.revokeObjectURL(url)
      setDownloadMessage('File downloaded successfully. This key is now expired.')
      setDownloadKey('')
      void loadRecords()
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
        const message = await error.response.data.text()
        try {
          const parsed = JSON.parse(message) as { detail?: string }
          setDownloadError(parsed.detail ?? 'Download failed.')
        } catch {
          setDownloadError('Download failed.')
        }
      } else {
        setDownloadError('Download failed.')
      }
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="page-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Temporary File Sharing</p>
          <h1>Upload a file, share a key, and let it vanish after one download.</h1>
          <p className="hero-copy">
            This workspace uses Django for the API and React for a fast, simple client. Keys are tracked only in
            this browser, so your dashboard stays session-scoped.
          </p>
        </div>
        <div className="hero-card">
          <span>One-time flow</span>
          <strong>Upload</strong>
          <strong>Share key</strong>
          <strong>Download once</strong>
          <strong>Expire immediately</strong>
        </div>
      </header>

      <main className="content-grid">
        <section className="panel">
          <h2>Upload File</h2>
          <p className="panel-copy">Choose any file and receive a unique 6-digit key.</p>
          <form onSubmit={handleUpload} className="stack">
            <label className="file-picker">
              <span>Select file</span>
              <input
                id="file"
                name="file"
                type="file"
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              />
            </label>
            <button type="submit" disabled={uploading}>
              {uploading ? 'Uploading...' : 'Upload and generate key'}
            </button>
          </form>
          {uploadError ? <p className="feedback error">{uploadError}</p> : null}
          {uploadMessage ? <p className="feedback success">{uploadMessage}</p> : null}
          {latestKey ? (
            <div className="key-card">
              <span>Your key</span>
              <strong>{latestKey}</strong>
            </div>
          ) : null}
        </section>

        <section className="panel">
          <h2>Download File</h2>
          <p className="panel-copy">Enter the 6-digit key to trigger the one-time download.</p>
          <form onSubmit={handleDownload} className="stack">
            <label>
              <span>Download key</span>
              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                placeholder="123456"
                value={downloadKey}
                onChange={(event) => setDownloadKey(event.target.value.replace(/\D/g, '').slice(0, 6))}
              />
            </label>
            <button type="submit" disabled={downloading}>
              {downloading ? 'Preparing download...' : 'Download file'}
            </button>
          </form>
          {downloadError ? <p className="feedback error">{downloadError}</p> : null}
          {downloadMessage ? <p className="feedback success">{downloadMessage}</p> : null}
        </section>

        <section className="panel panel-wide">
          <div className="panel-header">
            <div>
              <h2>Session Dashboard</h2>
              <p className="panel-copy">Only keys created in this browser session are shown here.</p>
            </div>
            <button type="button" className="ghost-button" onClick={() => void loadRecords(true)}>
              Refresh
            </button>
          </div>

          {loadingRecords ? <p className="empty-state">Loading uploaded files...</p> : null}
          {recordsError ? <p className="feedback error">{recordsError}</p> : null}
          {!loadingRecords && records.length === 0 ? (
            <p className="empty-state">No uploads tracked in this browser yet.</p>
          ) : null}
          {records.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>File</th>
                    <th>Status</th>
                    <th>Uploaded</th>
                    <th>Downloaded</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => (
                    <tr key={record.id}>
                      <td className="mono">{record.key}</td>
                      <td>{record.filename}</td>
                      <td>
                        <span className={`status-pill ${record.status.toLowerCase()}`}>{record.status}</span>
                      </td>
                      <td>{formatDate(record.uploaded_at)}</td>
                      <td>{formatDate(record.downloaded_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  )
}
