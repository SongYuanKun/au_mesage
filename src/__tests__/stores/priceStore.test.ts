import { describe, it, expect, vi, beforeEach } from 'vitest'
import { act } from '@testing-library/react'

// Mock the API module
vi.mock('@/api/price', () => ({
  fetchPriceOverview: vi.fn(),
}))

import { fetchPriceOverview } from '@/api/price'
import usePriceStore from '@/stores/priceStore'

const mockFetchPriceOverview = fetchPriceOverview as ReturnType<typeof vi.fn>

describe('priceStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset store state
    usePriceStore.setState({
      goldPrice: null,
      silverPrice: null,
      loading: false,
      error: null,
      lastFetchedAt: null,
    })
  })

  it('should have correct initial state', () => {
    const state = usePriceStore.getState()
    expect(state.goldPrice).toBeNull()
    expect(state.silverPrice).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
    expect(state.lastFetchedAt).toBeNull()
  })

  it('should fetch overview and set gold/silver prices', async () => {
    const mockData = [
      { data_type: '黄金', recycle_price: 580, real_time_price: 590, today_high: 595, today_low: 575, change: 5, change_pct: 0.85, updated_at: '2024-01-01T10:00:00Z' },
      { data_type: '白银', recycle_price: 7.2, real_time_price: 7.5, today_high: 7.8, today_low: 7.0, change: -0.1, change_pct: -1.32, updated_at: '2024-01-01T10:00:00Z' },
    ]
    mockFetchPriceOverview.mockResolvedValueOnce(mockData)

    await act(async () => {
      await usePriceStore.getState().fetchOverview()
    })

    const state = usePriceStore.getState()
    expect(state.goldPrice).toEqual(mockData[0])
    expect(state.silverPrice).toEqual(mockData[1])
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()
    expect(state.lastFetchedAt).toBeGreaterThan(0)
  })

  it('should set error when fetch fails', async () => {
    mockFetchPriceOverview.mockRejectedValueOnce(new Error('网络连接失败'))

    await act(async () => {
      await usePriceStore.getState().fetchOverview()
    })

    const state = usePriceStore.getState()
    expect(state.error).toBe('网络连接失败')
    expect(state.loading).toBe(false)
    expect(state.goldPrice).toBeNull()
  })

  it('should prevent concurrent fetches', async () => {
    mockFetchPriceOverview.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    )

    // Set loading to true to simulate in-progress fetch
    usePriceStore.setState({ loading: true })

    await act(async () => {
      await usePriceStore.getState().fetchOverview()
    })

    // Should NOT have called the API since loading was already true
    expect(mockFetchPriceOverview).not.toHaveBeenCalled()
  })

  it('should set loading=true during fetch', async () => {
    let resolvePromise: (value: any) => void
    const promise = new Promise((resolve) => { resolvePromise = resolve })
    mockFetchPriceOverview.mockReturnValueOnce(promise)

    // Start fetch (don't await)
    const fetchPromise = usePriceStore.getState().fetchOverview()

    // Check loading is true
    expect(usePriceStore.getState().loading).toBe(true)

    // Resolve and await
    resolvePromise!([])
    await fetchPromise

    expect(usePriceStore.getState().loading).toBe(false)
  })
})
