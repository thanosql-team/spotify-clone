import React from 'react'
import Sidebar from './features/sidebar/Sidebar'
import Topbar from './features/topbar/Topbar'
import MainContent from './features/main-content/MainContent'
import Player from './features/player/Player'
import './App.css'

function App() {
  return (
    <div className="app">
      <div className="app-container">
        <Sidebar />
        <div className="main-view">
          <Topbar />
          <MainContent />
        </div>
      </div>
      <Player />
    </div>
  )
}

export default App
