export function initTracker(): void

export function trackPageView(page?: string): void

export function track(
  eventType: string,
  options?: {
    page?: string
    duration?: number
    metadata?: Record<string, unknown>
  },
): void
