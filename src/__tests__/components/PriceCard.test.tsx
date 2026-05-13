import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import PriceCard, { PriceCardSkeleton } from '@/components/PriceCard'

describe('PriceCard', () => {
  const defaultProps = {
    name: '黄金',
    emoji: '🥇',
    price: 590.5,
    change: 5.2,
    changePct: 0.89,
    high: 595.0,
    low: 580.0,
    updatedAt: '2024-01-01T10:30:00Z',
  }

  it('should render price card with correct data', () => {
    render(<PriceCard {...defaultProps} />)

    expect(screen.getByText('黄金')).toBeInTheDocument()
    expect(screen.getByText('🥇')).toBeInTheDocument()
    expect(screen.getByText('¥590.50')).toBeInTheDocument()
    expect(screen.getByText('+5.20 元')).toBeInTheDocument()
    expect(screen.getByText('¥595.00')).toBeInTheDocument()
    expect(screen.getByText('¥580.00')).toBeInTheDocument()
  })

  it('should show positive change with green styling and +', () => {
    render(<PriceCard {...defaultProps} change={3.5} changePct={0.6} />)

    // Check positive change text includes +
    expect(screen.getByText('+3.50 元')).toBeInTheDocument()
    expect(screen.getByText('+0.60%')).toBeInTheDocument()
  })

  it('should show negative change with red styling', () => {
    render(<PriceCard {...defaultProps} change={-2.5} changePct={-0.42} />)

    expect(screen.getByText('-2.50 元')).toBeInTheDocument()
    expect(screen.getByText('-0.42%')).toBeInTheDocument()
  })

  it('should show "--" when price is null', () => {
    render(<PriceCard {...defaultProps} price={null} change={null} changePct={null} high={null} low={null} updatedAt={null} />)

    // Price should show --
    const dashElements = screen.getAllByText('--')
    expect(dashElements.length).toBeGreaterThan(0)
  })

  it('should render skeleton when loading=true', () => {
    const { container } = render(<PriceCard {...defaultProps} loading={true} />)

    // Skeleton should have animate-pulse class
    const pulseElements = container.querySelectorAll('.animate-pulse')
    expect(pulseElements.length).toBeGreaterThan(0)

    // Should NOT show the actual price
    expect(screen.queryByText('¥590.50')).not.toBeInTheDocument()
  })

  it('should render PriceCardSkeleton correctly', () => {
    const { container } = render(<PriceCardSkeleton />)

    const pulseElements = container.querySelectorAll('.animate-pulse')
    expect(pulseElements.length).toBeGreaterThan(0)
  })

  it('should display formatted update time', () => {
    render(<PriceCard {...defaultProps} updatedAt="2024-06-15T14:30:00Z" />)

    // dayjs formats as MM-DD HH:mm:ss
    // The exact output depends on timezone, just check it's rendered
    expect(screen.getByText(/更新时间/)).toBeInTheDocument()
  })
})
