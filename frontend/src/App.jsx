import { useState, useEffect } from 'react'
import api from './services/api'
import './App.css'

function App() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    api.get('/health/')
      .then(res => setStatus(res.data))
      .catch(err => console.error(err))
  }, [])

  return (
    <div className="App">
      <h1>AdmireHR</h1>
      <p>Backend Status: {status ? status.message : 'Loading...'}</p>
    </div>
  )
}

export default App
