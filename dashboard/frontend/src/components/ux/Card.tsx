import { ReactNode } from 'react'

interface CardProps {
  title?: string
  subtitle?: string
  header?: ReactNode
  footer?: ReactNode
  hover?: boolean
  padding?: boolean
  className?: string
  children: ReactNode
}

export default function Card({
  title,
  subtitle,
  header,
  footer,
  hover = true,
  padding = true,
  className = '',
  children,
}: CardProps) {
  return (
    <div className={`
      bg-[#1a1a2e] rounded-xl border border-[#2a2a3e]
      ${hover ? 'hover:border-[#7f5af0] transition-colors duration-200' : ''}
      ${className}
    `}>
      {(title || header) && (
        <div className="px-6 py-4 border-b border-[#2a2a3e]">
          {header || (
            <div>
              {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
              {subtitle && <p className="text-sm text-gray-400 mt-1">{subtitle}</p>}
            </div>
          )}
        </div>
      )}
      <div className={padding ? 'p-6' : ''}>{children}</div>
      {footer && (
        <div className="px-6 py-4 border-t border-[#2a2a3e]">{footer}</div>
      )}
    </div>
  )
}
