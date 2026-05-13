import { describe, it, expect, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { useTheme } from '@/hooks/useTheme'
import useThemeStore from '@/stores/themeStore'

function Probe() {
  useTheme()
  return null
}

describe('useTheme', () => {
  beforeEach(() => {
    useThemeStore.setState({ theme: 'light', isDark: false })
    document.documentElement.classList.remove('light', 'dark')
    localStorage.clear()
  })

  it('syncs document class with store theme on mount', () => {
    useThemeStore.setState({ theme: 'dark', isDark: true })
    render(<Probe />)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})
