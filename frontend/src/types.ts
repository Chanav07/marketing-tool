export interface Brand {
  id: string
  name: string
  vision: string | null
  goal: string | null
  moat: string | null
  created_at: string
  updated_at: string
}

export interface BrandInput {
  name: string
  vision?: string | null
  goal?: string | null
  moat?: string | null
}
