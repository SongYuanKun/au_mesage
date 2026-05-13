import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Navbar from '@/components/Navbar'
import useThemeStore from '@/stores/themeStore'

describe('Navbar', () => {
  beforeEach(() => {
    // Reset theme store to light
    useThemeStore.setState({ theme: 'light', isDark: false })
    document.documentElement.classList.remove('light', 'dark')
    localStorage.clear()
  })

  it('should render the title and emoji', () => {
    render(<Navbar />)

    expect(screen.getByText('实时金价监控')).toBeInTheDocument()
    expect(screen.getByText('🪙')).toBeInTheDocument()
  })

  it('should render a theme toggle button', () => {
    render(<Navbar />)

    const button = screen.getByRole('button', { name: '切换主题' })
    expect(button).toBeInTheDocument()
  })

  it('should toggle theme when button is clicked', () => {
    render(<Navbar />)

    const button = screen.getByRole('button', { name: '切换主题' })
    fireEvent.click(button)

    const state = useThemeStore.getState()
    expect(state.theme).toBe('dark')
    expect(state.isDark).toBe(true)
  })

  it('should toggle back to light on second click', () => {
    render(<Navbar />)

    const button = screen.getByRole('button', { name: '切换主题' })
    fireEvent.click(button)
    fireEvent.click(button)

    const state = useThemeStore.getState()
    expect(state.theme).toBe('light')
    expect(state.isDark).toBe(false)
  })

  it('should have navigation landmark', () => {
    render(<Navbar />)

    const nav = screen.getByRole('navigation', { name: '主导航' })
    expect(nav).toBeInTheDocument()
  })
})
