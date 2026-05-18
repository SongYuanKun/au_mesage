import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Home from '@/pages/Home'
import usePriceStore from '@/stores/priceStore'
import * as priceApi from '@/api/price'

/** Wrap component with Router for NavLink support in Navbar */
function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="recharts-rc" style={{ width: 400, height: 300 }}>
      {children}
    </div>
  ),
  AreaChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Area: () => null,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}))

const gold = {
  data_type: '黄金',
  recycle_price: 1,
  real_time_price: 590,
  today_high: 595,
  today_low: 580,
  change: 1,
  change_pct: 0.1,
  updated_at: '2024-01-01T10:00:00Z',
}
const silver = {
  data_type: '白银',
  recycle_price: 1,
  real_time_price: 7,
  today_high: 8,
  today_low: 6,
  change: 0,
  change_pct: 0,
  updated_at: '2024-01-01T10:00:00Z',
}

describe('Home', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    usePriceStore.setState({
      goldPrice: null,
      silverPrice: null,
      loading: false,
      error: null,
      lastFetchedAt: null,
    })
    vi.spyOn(priceApi, 'fetchPriceTrend').mockResolvedValue({
      chart_type: 'line',
      data: [{ time: '10:00', price: 590 }],
    })
    vi.spyOn(priceApi, 'fetchGoldSilverRatio').mockResolvedValue([
      { date: '2024-01-01', ratio: 80 },
    ])
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders price cards after successful overview fetch', async () => {
    vi.spyOn(priceApi, 'fetchPriceOverview').mockResolvedValue([gold, silver])
    renderWithRouter(<Home />)
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '黄金' })).toBeInTheDocument()
    })
    expect(screen.getByRole('heading', { name: '白银' })).toBeInTheDocument()
  })

  it('shows empty state when overview returns no rows', async () => {
    vi.spyOn(priceApi, 'fetchPriceOverview').mockResolvedValue([])
    renderWithRouter(<Home />)
    await waitFor(() => {
      expect(screen.getByText('暂无价格数据')).toBeInTheDocument()
    })
  })

  it('shows error banner and retries on button click', async () => {
    vi.spyOn(priceApi, 'fetchPriceOverview')
      .mockRejectedValueOnce(new Error('网络不可用'))
      .mockResolvedValueOnce([gold, silver])
    renderWithRouter(<Home />)
    await waitFor(() => {
      expect(screen.getByText(/网络不可用/)).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: '重试' }))
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: '黄金' })).toBeInTheDocument()
    })
  })
})
