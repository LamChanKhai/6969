import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const Badge = forwardRef<HTMLSpanElement, HTMLAttributes<HTMLSpanElement>>(
  ({ className, ...props }, ref) => {
    return (
      <span
        className={cn(
          'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Badge.displayName = 'Badge'
