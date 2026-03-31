import { useEffect } from 'react'
import { AppShell } from './components/layout/AppShell'
import { TopBar } from './components/layout/TopBar'
import { useAppStore } from './store/appStore'

export default function App() {
  const initSession = useAppStore((state) => state.initSession)
  const error = useAppStore((state) => state.error)
  const setError = useAppStore((state) => state.setError)

  useEffect(() => {
    void initSession().catch((caughtError) => {
      setError(caughtError instanceof Error ? caughtError.message : 'Unable to initialize the session')
    })
  }, [initSession, setError])

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-5 px-4 py-5 sm:px-6 lg:px-8">
      <TopBar />
      {error ? (
        <div className="rounded-[24px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          <button className="ml-3 underline" onClick={() => setError(null)}>
            Dismiss
          </button>
        </div>
      ) : null}
      <AppShell />
    </div>
  )
}
