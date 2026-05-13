import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import * as priceApi from '@/api/price'
import GoldSilverRatioChart from '@/components/GoldSilverRatioChart'

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="recharts-rc" style={{ width: 400, height: 300 }}>
      {children}
    </div>
  ),
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}))

describe('GoldSilverRatioChart', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders header and ratio series', async () => {
    vi.spyOn(priceApi, 'fetchGoldSilverRatio').mockResolvedValue([
      { date: '2024-01-01', ratio: 82.5 },
      { date: '2024-01-02', ratio: 83.1 },
    ])
    render(<GoldSilverRatioChart />)
    await waitFor(() => {
      expect(screen.getByText('金银比走势')).toBeInTheDocument()
    })
    expect(screen.getByText('金价 / 银价 比率')).toBeInTheDocument()
  })

  it('shows empty state', async () => {
    vi.spyOn(priceApi, 'fetchGoldSilverRatio').mockResolvedValue([])
    render(<GoldSilverRatioChart />)
    await waitFor(() => {
      expect(screen.getByText('暂无金银比数据')).toBeInTheDocument()
    })
  })

  it('shows error and retries', async () => {
    vi.spyOn(priceApi, 'fetchGoldSilverRatio')
      .mockRejectedValueOnce(new Error('ratio-fail'))
      .mockResolvedValueOnce([{ date: '2024-01-01', ratio: 80 }])
    render(<GoldSilverRatioChart />)
    await waitFor(() => {
      expect(screen.getByText(/ratio-fail/)).toBeInTheDocument()
    })
    fireEvent.click(screen.getByText('点击重试'))
    await waitFor(() => {
      expect(screen.queryByText(/ratio-fail/)).not.toBeInTheDocument()
    })
  })

  it('changes range and refetches', async () => {
    const spy = vi.spyOn(priceApi, 'fetchGoldSilverRatio').mockResolvedValue([
      { date: '2024-01-01', ratio: 80 },
    ])
    render(<GoldSilverRatioChart />)
    await waitFor(() => expect(spy).toHaveBeenCalled())
    fireEvent.click(screen.getByRole('button', { name: '1年' }))
    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith('1y')
    })
  })
})
