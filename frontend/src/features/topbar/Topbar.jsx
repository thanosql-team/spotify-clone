import React, { useState } from 'react'
import Icon from '../../components/Icon'
import './Topbar.css'

function Topbar() {
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <div className="topbar">
      <div className="topbar-left">
        <div className="topbar-nav-buttons">
          <button className="nav-button" aria-label="Go back">
            <Icon name="chevron-left" size="24" />
          </button>
          <button className="nav-button" aria-label="Go forward">
            <Icon name="chevron-right" size="24" />
          </button>
        </div>
        
        <div className="topbar-search">
          <Icon name="search" size="20" className="search-icon" />
          <input
            type="text"
            placeholder="What do you want to listen to?"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      <div className="topbar-user">
        <button className="user-button">
          <img 
            src="/images/user-avatar.svg" 
            alt="User" 
            className="user-avatar"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = '/images/default-user.svg';
            }}
          />
          <span>User</span>
        </button>
      </div>
    </div>
  )
}

export default Topbar
