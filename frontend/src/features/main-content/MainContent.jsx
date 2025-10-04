import React from 'react'
import Icon from '../../components/Icon'
import './MainContent.css'

function MainContent() {
  // Hardcoded data for playlists and albums
  const playlists = [
    {
      id: 1,
      title: 'Today\'s Top Hits',
      description: 'Bestt 50!',
      image: '/images/playlists/playlist1.svg'
    },
    {
      id: 2,
      title: 'Rap',
      description: 'New music from Drake, Travis Scott and more.',
      image: '/images/playlists/playlist2.svg'
    },
    {
      id: 3,
      title: 'All Out 2010s',
      description: 'The best songs of 2010s.',
      image: '/images/playlists/playlist3.svg'
    },
    {
      id: 4,
      title: 'Rock Classics',
      description: 'Rock legends and classics',
      image: '/images/playlists/playlist4.svg'
    },
    {
      id: 5,
      title: 'Chill Hits',
      description: 'best new and recent chill hits.',
      image: '/images/playlists/playlist5.svg'
    },
    {
      id: 6,
      title: 'Latin',
      description: 'Today\'s top Latin hits.',
      image: '/images/playlists/playlist6.svg'
    }
  ]

  const recentlyPlayed = [
    {
      id: 1,
      title: 'Liked Songs',
      description: '50 songs',
      image: '/images/liked-songs.svg'
    },
    {
      id: 2,
      title: 'Discover Weekly',
      description: 'Your weekly mixtape of fresh music',
      image: '/images/albums/album1.svg'
    },
    {
      id: 3,
      title: 'Daily Mix 1',
      description: 'The daily music u find everywhere',
      image: '/images/albums/album2.svg'
    },
    {
      id: 4,
      title: 'Release Radar',
      description: 'Catch all the latest music from artists you follow',
      image: '/images/albums/album3.svg'
    }
  ]

  return (
    <div className="main-content">
      <div className="content-spacing">
        <section className="content-section">
          <div className="section-header">
            <h2>Good afternoon</h2>
          </div>
          <div className="grid-recently-played">
            {recentlyPlayed.map((item) => (
              <div key={item.id} className="recently-played-item">
                <img 
                  src={item.image} 
                  alt={item.title}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = '/images/default-cover.svg';
                  }}
                />
                <span className="item-title">{item.title}</span>
                <button className="play-button">
                  <Icon name="play" size="24" />
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="content-section">
          <div className="section-header">
            <h2>Spotify Playlists</h2>
            <a href="#" className="show-all">Show all</a>
          </div>
          <div className="grid-playlists">
            {playlists.map((playlist) => (
              <div key={playlist.id} className="playlist-card">
                <div className="card-image-container">
                  <img 
                    src={playlist.image} 
                    alt={playlist.title}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = '/images/default-cover.svg';
                    }}
                  />
                  <button className="card-play-button">
                    <Icon name="play" size="24" />
                  </button>
                </div>
                <div className="card-content">
                  <h3 className="card-title">{playlist.title}</h3>
                  <p className="card-description">{playlist.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default MainContent
