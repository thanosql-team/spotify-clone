import React, { useState } from 'react'
import Icon from '../../components/Icon'
import './Player.css'

function Player() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(30)
  const [volume, setVolume] = useState(70)

  // Hardcoded song data
  const currentSong = {
    title: 'Shape of You',
    artist: 'Ed Sheeran',
    album: '÷ (Divide)',
    image: '/images/albums/album4.svg',
    duration: 233, // in seconds current time and duration- max value for current time
    currentTime: 70
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="player">
      <div className="player-left">
        <img 
          src={currentSong.image} 
          alt={currentSong.title} 
          className="song-image"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = '/images/default-cover.svg';
          }}
        />
        <div className="song-info">
          <div className="song-title">{currentSong.title}</div>
          <div className="song-artist">{currentSong.artist}</div>
        </div>
        <button className="player-icon-button like-button">
          <Icon name="heart" size="16" />
        </button>
      </div>

      <div className="player-center">
        <div className="player-controls">
          <button className="player-icon-button">
            <Icon name="shuffle" size="16" />
          </button>
          <button className="player-icon-button">
            <Icon name="skip-back" size="16" />
          </button>
          <button 
            className="player-play-button"
            onClick={() => setIsPlaying(!isPlaying)}
          >
            <Icon name={isPlaying ? "pause" : "play"} size="16" />
          </button>
          <button className="player-icon-button">
            <Icon name="skip-forward" size="16" />
          </button>
          <button className="player-icon-button">
            <Icon name="repeat" size="16" />
          </button>
        </div>
        <div className="player-timeline">
          <span className="time-label">{formatTime(currentSong.currentTime)}</span>
          <div className="progress-bar">
            <input
              type="range"
              min="0"
              max="100"
              value={progress}
              onChange={(e) => setProgress(e.target.value)}
              className="progress-slider"
              style={{ '--progress': `${progress}%` }}
            />
          </div>
          <span className="time-label">{formatTime(currentSong.duration)}</span>
        </div>
      </div>

      <div className="player-right">
        <button className="player-icon-button">
          <Icon name="volume" size="16" />
        </button>
        <div className="volume-bar">
          <input
            type="range"
            min="0"
            max="100"
            value={volume}
            onChange={(e) => setVolume(e.target.value)}
            className="volume-slider"
            style={{ '--volume': `${volume}%` }}
          />
        </div>
      </div>
    </div>
  )
}

export default Player
