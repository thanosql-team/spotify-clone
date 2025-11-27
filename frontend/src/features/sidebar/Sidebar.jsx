import React from 'react'
import Icon from '../../components/Icon'
import './Sidebar.css'

function Sidebar() {
  // Hardcoded playlists for now
  const playlists = [
    'My Playlist #1',
    'Chill Vibes',
    'Workout Mix',
    'Focus Music',
    'Road Trip',
    'Party Hits'
  ]

  return (
    <div className="sidebar">
      <div className="sidebar-nav">
        <div className="logo">
          <img 
            src="/images/spotify_logo.svg" 
            alt="Spotify" 
            className="spotify-logo"
          />
        </div>

        <nav className="nav-menu">
          <a href="#" className="nav-item active">
            <Icon name="home" size="24" />
            <span>Home</span>
          </a>
          <a href="#" className="nav-item">
            <Icon name="search" size="24" />
            <span>Search</span>
          </a>
          <a href="#" className="nav-item">
            <Icon name="library" size="24" />
            <span>Your Library</span>
          </a>
        </nav>

        <nav className="nav-menu">
          <a href="#" className="nav-item">
            <Icon name="plus" size="24" />
            <span>Create Playlist</span>
          </a>
          <a href="#" className="nav-item">
            <Icon name="heart" size="24" />
            <span>Liked Songs</span>
          </a>
        </nav>
      </div>

      <div className="sidebar-playlists">
        {playlists.map((playlist, index) => (
          <a key={index} href="#" className="playlist-item">
            {playlist}
          </a>
        ))}
      </div>
    </div>
  )
}

export default Sidebar
