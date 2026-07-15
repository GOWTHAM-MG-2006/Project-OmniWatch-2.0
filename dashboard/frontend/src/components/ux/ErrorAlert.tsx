interface ErrorAlertProps {
  message: string
  onRetry?: () => void
}

export default function ErrorAlert({ message, onRetry }: ErrorAlertProps) {
  return (
    <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 backdrop-blur-sm">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
          <span className="text-red-400 text-sm font-bold">!</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-red-200 font-medium">Error</p>
          <p className="text-sm text-red-300/80 mt-1">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 px-4 py-1.5 text-xs font-medium bg-red-500/20 text-red-300 border border-red-500/30 rounded-lg hover:bg-red-500/30 transition-colors duration-200"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
