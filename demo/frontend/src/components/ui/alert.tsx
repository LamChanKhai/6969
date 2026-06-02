import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const Alert = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & { variant?: 'default' | 'destructive' | 'success' }
>(({ className, variant = 'default', ...props }, ref) => {
  const variants = {
    default: 'border-border bg-card text-foreground',
    destructive: 'border-destructive/50 bg-destructive/10 text-destructive',
    success: 'border-primary/50 bg-primary/10 text-primary',
  }

  return (
    <div
      role="alert"
      className={cn(
        'relative w-full rounded-lg border p-4 text-sm',
        variants[variant],
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Alert.displayName = 'Alert'
