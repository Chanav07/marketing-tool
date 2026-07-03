import type { Brand, BrandInput } from './types'

const BASE = '/api'

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return res.json() as Promise<T>
}

export const api = {
  listBrands: () => fetch(`${BASE}/brands`).then(handle<Brand[]>),

  getBrand: (id: string) => fetch(`${BASE}/brands/${id}`).then(handle<Brand>),

  createBrand: (data: BrandInput) =>
    fetch(`${BASE}/brands`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handle<Brand>),

  updateBrand: (id: string, data: Partial<BrandInput>) =>
    fetch(`${BASE}/brands/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(handle<Brand>),
}
