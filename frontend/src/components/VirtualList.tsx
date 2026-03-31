import React, { useRef, useState, useEffect, useCallback, memo } from 'react'

interface VirtualListProps<T> {
  items: T[]
  itemHeight: number
  containerHeight: number
  renderItem: (item: T, index: number) => React.ReactNode
  overscan?: number
  className?: string
  onEndReached?: () => void
  endReachedThreshold?: number
}

function VirtualListInner<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 3,
  className = '',
  onEndReached,
  endReachedThreshold = 0.8,
}: VirtualListProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [scrollTop, setScrollTop] = useState(0)

  const totalHeight = items.length * itemHeight

  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan)
  const endIndex = Math.min(
    items.length - 1,
    Math.floor((scrollTop + containerHeight) / itemHeight) + overscan
  )

  const visibleItems = items.slice(startIndex, endIndex + 1)

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget
    setScrollTop(target.scrollTop)

    if (onEndReached) {
      const scrollPercentage =
        (target.scrollTop + target.clientHeight) / target.scrollHeight
      if (scrollPercentage >= endReachedThreshold) {
        onEndReached()
      }
    }
  }, [onEndReached, endReachedThreshold])

  return (
    <div
      ref={containerRef}
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visibleItems.map((item, index) => {
          const actualIndex = startIndex + index
          return (
            <div
              key={actualIndex}
              style={{
                position: 'absolute',
                top: actualIndex * itemHeight,
                height: itemHeight,
                width: '100%',
              }}
            >
              {renderItem(item, actualIndex)}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export const VirtualList = memo(VirtualListInner) as typeof VirtualListInner

interface InfiniteScrollProps {
  children: React.ReactNode
  loadMore: () => Promise<void>
  hasMore: boolean
  isLoading: boolean
  threshold?: number
  loader?: React.ReactNode
  endMessage?: React.ReactNode
  className?: string
}

export function InfiniteScroll({
  children,
  loadMore,
  hasMore,
  isLoading,
  threshold = 200,
  loader,
  endMessage,
  className = '',
}: InfiniteScrollProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const loadingRef = useRef(false)

  const handleScroll = useCallback(async () => {
    if (loadingRef.current || !hasMore || isLoading) return

    const container = containerRef.current
    if (!container) return

    const { scrollTop, scrollHeight, clientHeight } = container
    const distanceToBottom = scrollHeight - scrollTop - clientHeight

    if (distanceToBottom < threshold) {
      loadingRef.current = true
      await loadMore()
      loadingRef.current = false
    }
  }, [hasMore, isLoading, loadMore, threshold])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.addEventListener('scroll', handleScroll)
    return () => container.removeEventListener('scroll', handleScroll)
  }, [handleScroll])

  return (
    <div ref={containerRef} className={`overflow-auto ${className}`}>
      {children}
      {isLoading && (loader || <DefaultLoader />)}
      {!hasMore && !isLoading && endMessage}
    </div>
  )
}

function DefaultLoader() {
  return (
    <div className="flex justify-center py-4">
      <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-primary-500"></div>
    </div>
  )
}

interface LazyImageProps {
  src: string
  alt: string
  placeholder?: string
  className?: string
  onLoad?: () => void
  onError?: () => void
}

export function LazyImage({
  src,
  alt,
  placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23374151" width="400" height="300"/%3E%3C/svg%3E',
  className = '',
  onLoad,
  onError,
}: LazyImageProps) {
  const imgRef = useRef<HTMLImageElement>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(false)

  useEffect(() => {
    const img = imgRef.current
    if (!img) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      { rootMargin: '100px' }
    )

    observer.observe(img)

    return () => observer.disconnect()
  }, [])

  const handleLoad = useCallback(() => {
    setIsLoaded(true)
    onLoad?.()
  }, [onLoad])

  const handleError = useCallback(() => {
    onError?.()
  }, [onError])

  return (
    <img
      ref={imgRef}
      src={isInView ? src : placeholder}
      alt={alt}
      className={`${className} ${isLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-300`}
      onLoad={handleLoad}
      onError={handleError}
      loading="lazy"
    />
  )
}

interface LazyComponentProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  rootMargin?: string
  threshold?: number
  className?: string
}

export function LazyComponent({
  children,
  fallback = null,
  rootMargin = '200px',
  threshold = 0.1,
  className = '',
}: LazyComponentProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
          observer.disconnect()
        }
      },
      { rootMargin, threshold }
    )

    observer.observe(element)

    return () => observer.disconnect()
  }, [rootMargin, threshold])

  return (
    <div ref={ref} className={className}>
      {isVisible ? children : fallback}
    </div>
  )
}

interface SkeletonProps {
  width?: string | number
  height?: string | number
  borderRadius?: string | number
  className?: string
}

export function Skeleton({
  width = '100%',
  height = '1rem',
  borderRadius = '0.25rem',
  className = '',
}: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-gray-700 ${className}`}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        borderRadius: typeof borderRadius === 'number' ? `${borderRadius}px` : borderRadius,
      }}
    />
  )
}

interface SkeletonTextProps {
  lines?: number
  lineHeight?: number
  className?: string
}

export function SkeletonText({ lines = 3, lineHeight = 16, className = '' }: SkeletonTextProps) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          height={lineHeight}
          width={i === lines - 1 ? '60%' : '100%'}
        />
      ))}
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="bg-dark-800 rounded-lg p-4 space-y-3">
      <Skeleton height={20} width="60%" />
      <SkeletonText lines={2} lineHeight={14} />
      <div className="flex space-x-2">
        <Skeleton height={32} width={80} borderRadius={4} />
        <Skeleton height={32} width={80} borderRadius={4} />
      </div>
    </div>
  )
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.props.onError?.(error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-semibold text-white mb-2">Something went wrong</h2>
            <p className="text-gray-400 mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
            >
              Try again
            </button>
          </div>
        )
      )
    }

    return this.props.children
  }
}

interface RetryProps {
  onRetry: () => void
  message?: string
  retryText?: string
}

export function Retry({ onRetry, message = 'Failed to load', retryText = 'Retry' }: RetryProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="text-yellow-500 text-4xl mb-4">🔄</div>
      <p className="text-gray-400 mb-4">{message}</p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
      >
        {retryText}
      </button>
    </div>
  )
}

interface EmptyStateProps {
  icon?: string
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function EmptyState({ icon = '📭', title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      {description && <p className="text-gray-400 mb-4">{description}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
