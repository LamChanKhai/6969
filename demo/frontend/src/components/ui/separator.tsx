import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const Separator = forwardRef<
  HTMLHRElement,
  HTMLAttributes<HTMLHRElement> & { orientation?: 'horizontal' | 'vertical' }
>(({ className, orientation = 'horizontal', ...props }, ref) => (
  <hr
    ref={ref}
    className={cn(
      'shrink-0 bg-border',
      orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]',
      className
    )}
    {...props}
  />
))
Separator.displayName = 'Separator'
