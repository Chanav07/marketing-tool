import { BrandInputs } from './components/BrandInputs'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <main className="stage">
        <div className="topbar">
          AIMark<span>Brand Brain</span>
        </div>
        <BrandInputs />
      </main>
    </div>
  )
}
