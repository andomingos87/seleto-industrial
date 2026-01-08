import { Skeleton } from "@/components/ui/skeleton"

/**
 * Skeleton for card content with avatar and text
 */
export function SkeletonCard() {
  return (
    <div className="rounded-lg border bg-card p-6 space-y-4 animate-fade-in">
      <div className="flex items-center gap-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-[200px]" />
          <Skeleton className="h-3 w-[150px]" />
        </div>
      </div>
      <Skeleton className="h-20 w-full" />
    </div>
  )
}

/**
 * Skeleton for table rows
 */
export function SkeletonTable({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="space-y-3 animate-fade-in">
      {/* Header */}
      <div className="flex gap-4 p-4 border-b">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={`header-${i}`} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4 p-4 border-b last:border-0">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton 
              key={`row-${rowIndex}-col-${colIndex}`} 
              className="h-4 flex-1" 
              style={{ animationDelay: `${rowIndex * 0.05}s` }}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

/**
 * Skeleton for stats/metrics cards grid
 */
export function SkeletonStats({ count = 4 }: { count?: number }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div 
          key={i} 
          className="rounded-lg border bg-card p-6 space-y-3 animate-fade-in"
          style={{ animationDelay: `${i * 0.1}s` }}
        >
          <div className="flex items-center justify-between">
            <Skeleton className="h-4 w-[100px]" />
            <Skeleton className="h-5 w-5 rounded" />
          </div>
          <Skeleton className="h-8 w-[80px]" />
          <Skeleton className="h-3 w-[120px]" />
        </div>
      ))}
    </div>
  )
}

/**
 * Skeleton for page header
 */
export function SkeletonPageHeader() {
  return (
    <div className="space-y-2 animate-fade-in">
      <Skeleton className="h-9 w-[250px]" />
      <Skeleton className="h-5 w-[350px]" />
    </div>
  )
}

/**
 * Skeleton for form fields
 */
export function SkeletonForm({ fields = 4 }: { fields?: number }) {
  return (
    <div className="space-y-6 animate-fade-in">
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-[100px]" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
      <div className="flex gap-2 pt-4">
        <Skeleton className="h-10 w-[100px]" />
        <Skeleton className="h-10 w-[80px]" />
      </div>
    </div>
  )
}

/**
 * Skeleton for conversation/chat messages
 */
export function SkeletonConversation({ messages = 5 }: { messages?: number }) {
  return (
    <div className="space-y-4 animate-fade-in">
      {Array.from({ length: messages }).map((_, i) => {
        const isUser = i % 2 === 0
        return (
          <div 
            key={i} 
            className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
            style={{ animationDelay: `${i * 0.1}s` }}
          >
            <div className={`max-w-[70%] space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
              <Skeleton className={`h-4 ${isUser ? 'w-[60px] ml-auto' : 'w-[80px]'}`} />
              <Skeleton className={`h-16 ${isUser ? 'w-[200px]' : 'w-[250px]'} rounded-lg`} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

/**
 * Skeleton for lead detail card
 */
export function SkeletonLeadDetail() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Skeleton className="h-16 w-16 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-[180px]" />
            <Skeleton className="h-4 w-[140px]" />
          </div>
        </div>
        <Skeleton className="h-8 w-[100px]" />
      </div>
      
      {/* Info grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-1">
            <Skeleton className="h-3 w-[80px]" />
            <Skeleton className="h-5 w-[150px]" />
          </div>
        ))}
      </div>
      
      {/* Conversation */}
      <div className="space-y-3">
        <Skeleton className="h-5 w-[120px]" />
        <SkeletonConversation messages={3} />
      </div>
    </div>
  )
}
