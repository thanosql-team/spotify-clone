import React from 'react'

/**
 * image loading + fallback
 * @param {string} src
 * @param {string} alt
 * @param {string} fallback
 * @param {string} className
 * @param {object} style
 */
function ImageWithFallback({ 
  src, 
  alt = '', 
  fallback = '/images/default-cover.svg',
  className = '',
  style = {},
  ...props 
}) {
  const handleError = (e) => {
    e.target.onerror = null;
    e.target.src = fallback;
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      style={style}
      onError={handleError}
      {...props}
    />
  )
}

export default ImageWithFallback
