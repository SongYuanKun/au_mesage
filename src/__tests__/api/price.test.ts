import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios module
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      isAxiosError: vi.fn(),
    },
    __mockInstance: mockAxiosInstance,
  }
})

// We need to get the mock instance
const { __mockInstance: mockApi } = await import('axios') as any

// Import after mocking
const { fetchPriceOverview, fetchPriceTrend, fetchGoldSilverRatio, fetchLast7Days } = await import('@/api/price')

describe('API: price.ts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset timer mocks
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('fetchPriceOverview', () => {
    it('should return price data on success', async () => {
      vi.useRealTimers()
      const mockData = [
        { data_type: '黄金', recycle_price: 580, real_time_price: 590, today_high: 595, today_low: 575, change: 5, change_pct: 0.85, updated_at: '2024-01-01' },
      ]
      mockApi.get.mockResolvedValueOnce({
        data: { success: true, data: mockData },
      })

      const result = await fetchPriceOverview()
      expect(result).toEqual(mockData)
      expect(mockApi.get).toHaveBeenCalledWith('/api/price-overview')
    })

    it('should throw error when success is false', async () => {
      vi.useRealTimers()
      mockApi.get.mockResolvedValueOnce({
        data: { success: false, message: '服务端错误' },
      })

      await expect(fetchPriceOverview()).rejects.toThrow()
    })

    it('should retry on network error (no response)', async () => {
      vi.useRealTimers()
      const networkError = new Error('Network Error') as any
      networkError.response = undefined
      ;(axios.isAxiosError as any).mockReturnValue(true)
      networkError.code = undefined

      mockApi.get
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(networkError)

      await expect(fetchPriceOverview()).rejects.toThrow('网络连接失败，请检查网络后重试')
      // 1 initial + 2 retries = 3 calls
      expect(mockApi.get).toHaveBeenCalledTimes(3)
    })

    it('should NOT retry on 4xx client error', async () => {
      vi.useRealTimers()
      const clientError = new Error('Not Found') as any
      clientError.response = { status: 404 }
      ;(axios.isAxiosError as any).mockReturnValue(true)

      mockApi.get.mockRejectedValueOnce(clientError)

      await expect(fetchPriceOverview()).rejects.toThrow('服务请求失败，请稍后重试')
      expect(mockApi.get).toHaveBeenCalledTimes(1)
    })
  })

  describe('fetchPriceTrend', () => {
    it('should return trend data with chart_type', async () => {
      vi.useRealTimers()
      const mockData = [{ time: '10:00', price: 590 }]
      mockApi.get.mockResolvedValueOnce({
        data: { success: true, data: mockData, chart_type: 'candlestick' },
      })

      const result = await fetchPriceTrend('黄金', '1d')
      expect(result).toEqual({ chart_type: 'candlestick', data: mockData })
      expect(mockApi.get).toHaveBeenCalledWith('/api/price-trend', {
        params: { data_type: '黄金', range: '1d' },
      })
    })

    it('should default chart_type to "line" when not provided', async () => {
      vi.useRealTimers()
      const mockData = [{ time: '10:00', price: 590 }]
      mockApi.get.mockResolvedValueOnce({
        data: { success: true, data: mockData },
      })

      const result = await fetchPriceTrend('黄金', '7d')
      expect(result.chart_type).toBe('line')
    })
  })

  describe('fetchGoldSilverRatio', () => {
    it('should return ratio data on success', async () => {
      vi.useRealTimers()
      const mockData = [{ date: '2024-01-01', ratio: 85.5 }]
      mockApi.get.mockResolvedValueOnce({
        data: { success: true, data: mockData },
      })

      const result = await fetchGoldSilverRatio('30d')
      expect(result).toEqual(mockData)
      expect(mockApi.get).toHaveBeenCalledWith('/api/gold-silver-ratio', {
        params: { range: '30d' },
      })
    })
  })

  describe('fetchLast7Days', () => {
    it('should return 7-day data on success', async () => {
      vi.useRealTimers()
      const mockData = [
        { date: '2024-01-01', price: 580 },
        { date: '2024-01-02', price: 585 },
      ]
      mockApi.get.mockResolvedValueOnce({
        data: { success: true, data: mockData },
      })

      const result = await fetchLast7Days('黄金')
      expect(result).toEqual(mockData)
      expect(mockApi.get).toHaveBeenCalledWith('/api/last-7-days', {
        params: { data_type: '黄金' },
      })
    })
  })
})
