import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Navbar from '@/components/Navbar'
import useThemeStore from '@/stores/themeStore'

/** Wrap component with Router for NavLink support */
function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('Navbar', () => {
  beforeEach(() => {
    // Reset theme store to light
    useThemeStore.setState({ theme: 'light', isDark: false })
    document.documentElement.classList.remove('light', 'dark')
    localStorage.clear()
  })

  it('should render the title and emoji', () => {
    renderWithRouter(<Navbar />)

    expect(screen.getByText('实时金价监控')).toBeInTheDocument()
    expect(screen.getByText('🪙')).toBeInTheDocument()
  })

  it('should render a theme toggle button', () => {
    renderWithRouter(<Navbar />)

    const button = screen.getByRole('button', { name: '切换主题' })
    expect(button).toBeInTheDocument()
  })

  it('should toggle theme when button is clicked', () => {
    renderWithRouter(<Navbar />)

    const button = screen.getByRole('button', { name: '切换主题' })
    fireEvent.click(button)

    const state = useThemeStore.getState()
    expect(state.theme).toBe('dark')
    expect(state.isDark).toBe(true)
  })

  it('should toggle back to light on second click', () => {
    renderWithRouter(<Navbar />)

    const button = screen.getByRole('button', { name: '切换主题' })
    fireEvent.click(button)
    fireEvent.click(button)

    const state = useThemeStore.getState()
    expect(state.theme).toBe('light')
    expect(state.isDark).toBe(false)
  })

  it('should have navigation landmark', () => {
    renderWithRouter(<Navbar />)

    const nav = screen.getByRole('navigation', { name: '主导航' })
    expect(nav).toBeInTheDocument()
  })

  it('should render navigation links', () => {
    renderWithRouter(<Navbar />)

    expect(screen.getByText('实时')).toBeInTheDocument()
    expect(screen.getByText('历史')).toBeInTheDocument()
    expect(screen.getByText('分析')).toBeInTheDocument()
    expect(screen.getByText('提醒')).toBeInTheDocument()
  })
})
