export interface Phase {
  id: number
  key: string
  label: string
  blurb: string
  status: 'active' | 'upcoming'
}

// Mirrors the "Brand brain" stages from the AIMark spec.
export const PHASES: Phase[] = [
  { id: 1, key: 'brand-inputs', label: 'Brand inputs', blurb: 'Vision, goal, moat', status: 'active' },
  { id: 2, key: 'icp-builder', label: 'ICP builder', blurb: 'Personas + variants', status: 'upcoming' },
  { id: 3, key: 'voice-codifier', label: 'Voice codifier', blurb: 'Samples + banned words', status: 'upcoming' },
  { id: 4, key: 'competitor-kb', label: 'Competitor & KB', blurb: 'Scans + knowledge base', status: 'upcoming' },
  { id: 5, key: 'pillar-synthesis', label: 'Pillar synthesis', blurb: '4–6 approved pillars', status: 'upcoming' },
  { id: 6, key: 'brand-context', label: 'Brand context store', blurb: 'The brand brain', status: 'upcoming' },
]
