import { Sidebar } from './Sidebar'
import { ChatPanel } from '../chat/ChatPanel'

export function AppShell() {
  return (
    <div className="grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
      <Sidebar />
      <ChatPanel />
    </div>
  )
}
