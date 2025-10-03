import React from 'react'

/**
 * All icons are loaded from /images/icons/ folder. + FALLBACK
 * 
 * @param {string} name - Icon name (play pause heart)
 * @param {string} size - default: 24
 * @param {string} className
 * @param {string} alt
 */
function Icon({ name, size = '24', className = '', alt = '' }) {
  const handleError = (e) => {
    e.target.onerror = null;
    e.target.src = '/images/default-cover.svg';
  }

  return (
    <img
      src={`/images/icons/${name}.svg`}
      alt={alt || name}
      width={size}
      height={size}
      className={className}
      onError={handleError}
      style={{ display: 'block' }}
    />
  )
}

export default Icon
