import { describe, it, expect, beforeEach } from 'vitest'
import useThemeStore from '@/stores/themeStore'

describe('themeStore', () => {
  beforeEach(() => {
    // Reset to light theme
    useThemeStore.setState({ theme: 'light', isDark: false })
    document.documentElement.classList.remove('light', 'dark')
    localStorage.clear()
  })

  it('should have initial theme state', () => {
    const state = useThemeStore.getState()
    expect(state.theme).toBe('light')
    expect(state.isDark).toBe(false)
  })

  it('should toggle from light to dark', () => {
    useThemeStore.getState().toggleTheme()

    const state = useThemeStore.getState()
    expect(state.theme).toBe('dark')
    expect(state.isDark).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem('theme')).toBe('dark')
  })

  it('should toggle from dark to light', () => {
    useThemeStore.setState({ theme: 'dark', isDark: true })

    useThemeStore.getState().toggleTheme()

    const state = useThemeStore.getState()
    expect(state.theme).toBe('light')
    expect(state.isDark).toBe(false)
    expect(document.documentElement.classList.contains('light')).toBe(true)
    expect(localStorage.getItem('theme')).toBe('light')
  })

  it('should set theme directly', () => {
    useThemeStore.getState().setTheme('dark')

    const state = useThemeStore.getState()
    expect(state.theme).toBe('dark')
    expect(state.isDark).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem('theme')).toBe('dark')
  })

  it('should remove previous theme class when toggling', () => {
    document.documentElement.classList.add('light')
    useThemeStore.getState().toggleTheme()

    expect(document.documentElement.classList.contains('light')).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})
