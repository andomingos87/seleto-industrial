import { LucideIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
    icon?: LucideIcon
  }
  secondaryAction?: {
    label: string
    onClick: () => void
  }
  className?: string
}

/**
 * Empty state component for when there's no data to display
 * Provides visual feedback and optional call-to-action
 */
export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action,
  secondaryAction,
  className 
}: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12 px-4 text-center animate-fade-in",
      className
    )}>
      <div className="rounded-full bg-muted p-4 mb-4">
        <Icon className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-muted-foreground max-w-md mb-6">{description}</p>
      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {action && (
            <Button onClick={action.onClick} className="btn-press">
              {action.icon && <action.icon className="mr-2 h-4 w-4" />}
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button variant="outline" onClick={secondaryAction.onClick} className="btn-press">
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Compact empty state for inline use (e.g., in tables)
 */
export function EmptyStateCompact({
  icon: Icon,
  message,
  action,
}: {
  icon: LucideIcon
  message: string
  action?: {
    label: string
    onClick: () => void
  }
}) {
  return (
    <div className="flex flex-col items-center gap-2 py-8 text-muted-foreground animate-fade-in">
      <Icon className="h-8 w-8" aria-hidden="true" />
      <p className="text-sm">{message}</p>
      {action && (
        <Button variant="link" size="sm" onClick={action.onClick} className="text-sm">
          {action.label}
        </Button>
      )}
    </div>
  )
}

/**
 * Error state component
 */
export function ErrorState({
  title = "Algo deu errado",
  description = "Não foi possível carregar os dados. Tente novamente.",
  onRetry,
  className,
}: {
  title?: string
  description?: string
  onRetry?: () => void
  className?: string
}) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12 px-4 text-center animate-fade-in",
      className
    )}>
      <div className="rounded-full bg-destructive/10 p-4 mb-4">
        <svg
          className="h-8 w-8 text-destructive"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h3 className="text-lg font-semibold mb-2 text-destructive">{title}</h3>
      <p className="text-muted-foreground max-w-md mb-6">{description}</p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="btn-press">
          Tentar novamente
        </Button>
      )}
    </div>
  )
}

/**
 * Loading state with spinner
 */
export function LoadingState({
  message = "Carregando...",
  className,
}: {
  message?: string
  className?: string
}) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12 px-4 text-center",
      className
    )}>
      <div className="relative mb-4">
        <div className="h-10 w-10 rounded-full border-4 border-muted" />
        <div className="absolute top-0 left-0 h-10 w-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
      </div>
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  )
}
