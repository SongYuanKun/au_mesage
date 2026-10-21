import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '@/App'

describe('App', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/app')
  })

  afterEach(() => {
    window.history.replaceState({}, '', '/')
  })

  it('renders home route by default', () => {
    render(<App />)
    expect(screen.getByText('实时金价监控')).toBeInTheDocument()
  })
})
