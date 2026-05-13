import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Empty from '@/components/Empty'

describe('Empty', () => {
  it('renders placeholder text', () => {
    render(<Empty />)
    expect(screen.getByText('Empty')).toBeInTheDocument()
  })
})
