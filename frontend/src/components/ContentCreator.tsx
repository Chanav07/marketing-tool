import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import type { Brand, ContentForm } from '../types'

const FORMAT_SUGGESTIONS: Record<ContentForm, string[]> = {
  long: ['Blog post', 'Article', 'Newsletter', 'Case study', 'Whitepaper', 'Landing page', 'Video script', 'LinkedIn article'],
  short: ['Instagram caption', 'Instagram script', 'WhatsApp message', 'X / Tweet', 'SMS', 'Ad copy', 'Reel script', 'Push notification'],
}

const PLATFORMS = ['WhatsApp', 'RCS', 'Google Ad'] as const
const OTHER = 'Other'

export function ContentCreator() {
  const [brands, setBrands] = useState<Brand[]>([])
  const [brandId, setBrandId] = useState('')

  const [form, setForm] = useState<ContentForm | ''>('')
  const [format, setFormat] = useState('')
  const [platform, setPlatform] = useState<string>('')
  const [customPlatform, setCustomPlatform] = useState('')

  const [script, setScript] = useState('')
  const [generated, setGenerated] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    api.listBrands().then(setBrands)
  }, [])

  const effectivePlatform = platform === OTHER ? customPlatform.trim() : platform
  const canGenerate =
    !!brandId && !!form && !!format.trim() && !!effectivePlatform && !generating

  async function generate() {
    if (!canGenerate) return
    setGenerating(true)
    setError(null)
    try {
      const res = await api.generateContent(brandId, {
        form: form as ContentForm,
        content_format: format.trim(),
        platform: effectivePlatform,
      })
      setScript(res.script)
      setGenerated(true)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setGenerating(false)
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(script)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      /* ignore */
    }
  }

  const suggestions = form ? FORMAT_SUGGESTIONS[form] : []

  return (
    <div className="phase-body">
      <header className="phase-head">
        <span className="phase-tag">Phase 5 · Content creation</span>
        <h1>Content creation</h1>
        <p>
          Pick a brand, choose the kind of content and where it will run, then generate a script
          grounded in your brand, personas and competitors — edit it live with a platform preview.
        </p>
      </header>

      <div className="icp-toolbar">
        <label className="brand-select">
          <span>Brand</span>
          <select value={brandId} onChange={(e) => setBrandId(e.target.value)}>
            <option value="">{brands.length === 0 ? 'No brands yet' : 'Select a brand…'}</option>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {!brandId ? (
        <div className="card muted">
          {brands.length === 0
            ? <>Create a brand in <strong>Brand inputs</strong> first.</>
            : <>Select a brand above to begin.</>}
        </div>
      ) : (
        <>
          <section className="card">
            <h3>Content type</h3>
            <p className="field-why">Is this a long-form piece or a short-form one?</p>
            <label className="brand-select">
              <span>Content type</span>
              <select
                value={form}
                onChange={(e) => {
                  setForm(e.target.value as ContentForm)
                  setFormat('')
                }}
              >
                <option value="">Select…</option>
                <option value="long">Long form</option>
                <option value="short">Short form</option>
              </select>
            </label>
          </section>

          {form && (
            <section className="card">
              <h3>What do you want to create?</h3>
              <p className="field-why">
                The specific format — e.g. {form === 'long' ? 'blog, case study' : 'Instagram script, WhatsApp message'}.
                Pick a suggestion or type your own.
              </p>
              <input
                className="text-input"
                list="format-suggestions"
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                placeholder={form === 'long' ? 'e.g. Blog post' : 'e.g. Instagram script'}
              />
              <datalist id="format-suggestions">
                {suggestions.map((s) => (
                  <option key={s} value={s} />
                ))}
              </datalist>
            </section>
          )}

          {form && format.trim() && (
            <section className="card">
              <h3>Where will it be posted?</h3>
              <p className="field-why">Choose a platform (its guidelines shape the output), or add your own.</p>
              <div className="platform-options">
                {PLATFORMS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    className={`platform-chip ${platform === p ? 'active' : ''}`}
                    onClick={() => setPlatform(p)}
                  >
                    {p}
                  </button>
                ))}
                <button
                  type="button"
                  className={`platform-chip ${platform === OTHER ? 'active' : ''}`}
                  onClick={() => setPlatform(OTHER)}
                >
                  Other…
                </button>
              </div>
              {platform === OTHER && (
                <input
                  className="text-input"
                  value={customPlatform}
                  onChange={(e) => setCustomPlatform(e.target.value)}
                  placeholder="Enter platform (e.g. LinkedIn, Email, Telegram)"
                  style={{ marginTop: 10 }}
                />
              )}
            </section>
          )}

          {error && <div className="alert">{error}</div>}

          <div className="actions">
            <button onClick={generate} disabled={!canGenerate}>
              {generating ? 'Generating…' : generated ? 'Regenerate' : 'Generate content'}
            </button>
            {generating && (
              <span className="saved">Analysing brand, personas, competitors &amp; {effectivePlatform} guidelines…</span>
            )}
          </div>

          {generated && (
            <section className="card">
              <div className="comp-fetch-head">
                <div>
                  <h3>Script &amp; preview</h3>
                  <p className="field-why">
                    Edit on the left — the {effectivePlatform} preview updates as you type.
                  </p>
                </div>
                <button className="ghost" onClick={copy}>{copied ? 'Copied ✓' : 'Copy'}</button>
              </div>
              <div className="content-panes">
                <div className="pane">
                  <div className="pane-label">Script (editable)</div>
                  <textarea
                    className="script-editor"
                    value={script}
                    onChange={(e) => setScript(e.target.value)}
                    spellCheck
                  />
                </div>
                <div className="pane">
                  <div className="pane-label">Preview · {effectivePlatform}</div>
                  <ContentPreview platform={effectivePlatform} text={script} brandName={brands.find((b) => b.id === brandId)?.name ?? 'Your brand'} />
                </div>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}

// --- Preview -----------------------------------------------------------

function ContentPreview({ platform, text, brandName }: { platform: string; text: string; brandName: string }) {
  const key = platform.trim().toLowerCase()
  if (!text.trim()) return <div className="preview-empty muted">Nothing to preview yet.</div>

  if (key === 'whatsapp') {
    return (
      <div className="pv-whatsapp">
        <div className="pv-wa-header">{brandName}</div>
        <div className="pv-wa-body">
          <div className="pv-wa-bubble">{renderBlocks(text)}</div>
        </div>
      </div>
    )
  }
  if (key === 'rcs') {
    return (
      <div className="pv-rcs">
        <div className="pv-rcs-brand">{brandName} · Verified business</div>
        <div className="pv-rcs-card">{renderBlocks(text)}</div>
      </div>
    )
  }
  if (key === 'google ad') {
    return <GoogleAdPreview text={text} brandName={brandName} />
  }
  // Default / custom / long-form: a clean document preview.
  return <div className="pv-doc">{renderBlocks(text)}</div>
}

function GoogleAdPreview({ text, brandName }: { text: string; brandName: string }) {
  const headlines: string[] = []
  const descriptions: string[] = []
  const other: string[] = []
  for (const raw of text.split('\n')) {
    const line = raw.trim()
    if (!line) continue
    const h = line.match(/^headline\s*\d*\s*[:\-]\s*(.+)$/i)
    const d = line.match(/^description\s*\d*\s*[:\-]\s*(.+)$/i)
    if (h) headlines.push(h[1].trim())
    else if (d) descriptions.push(d[1].trim())
    else other.push(line)
  }
  const title = headlines.length ? headlines.slice(0, 3).join(' | ') : other[0] ?? 'Your headline'
  const body = descriptions.length ? descriptions.join(' ') : other.slice(1).join(' ')
  const domain = brandName.toLowerCase().replace(/[^a-z0-9]+/g, '') || 'yourbrand'
  return (
    <div className="pv-ad">
      <div className="pv-ad-row">
        <span className="pv-ad-badge">Ad</span>
        <span className="pv-ad-url">www.{domain}.com</span>
      </div>
      <div className="pv-ad-title">{title}</div>
      <div className="pv-ad-desc">{body || '—'}</div>
    </div>
  )
}

// Minimal, safe markdown-ish renderer (headings, bullets, bold). No raw HTML.
function renderBlocks(text: string) {
  const lines = text.split('\n')
  const out: React.ReactNode[] = []
  let bullets: string[] = []

  const flush = () => {
    if (bullets.length) {
      out.push(
        <ul key={`ul-${out.length}`} className="pv-ul">
          {bullets.map((b, i) => <li key={i}>{renderInline(b)}</li>)}
        </ul>,
      )
      bullets = []
    }
  }

  lines.forEach((raw, idx) => {
    const line = raw.trimEnd()
    const t = line.trim()
    if (!t) { flush(); return }
    if (/^#{3}\s+/.test(t)) { flush(); out.push(<h5 key={idx} className="pv-h3">{renderInline(t.replace(/^#{3}\s+/, ''))}</h5>); return }
    if (/^#{2}\s+/.test(t)) { flush(); out.push(<h4 key={idx} className="pv-h2">{renderInline(t.replace(/^#{2}\s+/, ''))}</h4>); return }
    if (/^#\s+/.test(t)) { flush(); out.push(<h3 key={idx} className="pv-h1">{renderInline(t.replace(/^#\s+/, ''))}</h3>); return }
    if (/^[-*]\s+/.test(t)) { bullets.push(t.replace(/^[-*]\s+/, '')); return }
    flush()
    out.push(<p key={idx} className="pv-p">{renderInline(t)}</p>)
  })
  flush()
  return out
}

// Bold (**text**) inline; everything else plain text.
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((p, i) =>
    /^\*\*[^*]+\*\*$/.test(p) ? <strong key={i}>{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>,
  )
}
