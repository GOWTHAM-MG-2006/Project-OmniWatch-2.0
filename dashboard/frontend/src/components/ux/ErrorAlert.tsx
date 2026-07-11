interface ErrorAlertProps {
  message: string
  onRetry?: () => void
}

export default function ErrorAlert({ message, onRetry }: ErrorAlertProps) {
  return (
    <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <svg className="w-5 h-5 text-red-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="flex-1">
          <p className="text-sm text-red-300">{message}</p>
          {onRetry && (
            <button onClick={onRetry} className="mt-2 text-sm text-red-400 hover:text-red-300 underline">
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}