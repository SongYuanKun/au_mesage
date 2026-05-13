import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import * as priceApi from '@/api/price'
import PriceTrendChart from '@/components/PriceTrendChart'

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="recharts-rc" style={{ width: 400, height: 300 }}>
      {children}
    </div>
  ),
  AreaChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: ({ content }: { content?: React.ReactNode }) => (
    <div data-testid="tooltip-slot">{content}</div>
  ),
}))

describe('PriceTrendChart', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('loads line data and shows chart type label', async () => {
    vi.spyOn(priceApi, 'fetchPriceTrend').mockResolvedValue({
      chart_type: 'line',
      data: [{ time: '10:00', price: 100 }],
    })
    render(<PriceTrendChart dataType="黄金" />)
    await waitFor(() => {
      expect(screen.getByText('图表类型：分时线')).toBeInTheDocument()
    })
  })

  it('shows empty state when no data', async () => {
    vi.spyOn(priceApi, 'fetchPriceTrend').mockResolvedValue({
      chart_type: 'line',
      data: [],
    })
    render(<PriceTrendChart dataType="白银" />)
    await waitFor(() => {
      expect(screen.getByText('暂无白银趋势数据')).toBeInTheDocument()
    })
  })

  it('shows error and retries', async () => {
    vi.spyOn(priceApi, 'fetchPriceTrend')
      .mockRejectedValueOnce(new Error('boom'))
      .mockResolvedValueOnce({
        chart_type: 'line',
        data: [{ time: '10:00', price: 1 }],
      })
    render(<PriceTrendChart dataType="黄金" />)
    await waitFor(() => {
      expect(screen.getByText(/boom/)).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('点击重试'))
    await waitFor(() => {
      expect(screen.getByText('图表类型：分时线')).toBeInTheDocument()
    })
  })

  it('switches range tab and refetches', async () => {
    const spy = vi.spyOn(priceApi, 'fetchPriceTrend').mockResolvedValue({
      chart_type: 'line',
      data: [{ time: '10:00', price: 1 }],
    })
    render(<PriceTrendChart dataType="黄金" />)
    await waitFor(() => expect(spy).toHaveBeenCalled())
    const initial = spy.mock.calls.length
    fireEvent.click(screen.getByRole('button', { name: '今日' }))
    await waitFor(() => {
      expect(spy.mock.calls.length).toBeGreaterThan(initial)
    })
    expect(spy).toHaveBeenCalledWith('黄金', '1d')
  })

  it('renders candlestick path as close in chart', async () => {
    vi.spyOn(priceApi, 'fetchPriceTrend').mockResolvedValue({
      chart_type: 'candlestick',
      data: [{ date: '2024-01-01', open: 1, high: 2, low: 0.5, close: 1.5 }],
    })
    render(<PriceTrendChart dataType="黄金" />)
    await waitFor(() => {
      expect(screen.getByText('图表类型：K线(收盘价)')).toBeInTheDocument()
    })
  })
})
