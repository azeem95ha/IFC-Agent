import { ApiKeyInput } from '../session/ApiKeyInput'
import { SessionControls } from '../session/SessionControls'
import { DownloadButton } from '../model/DownloadButton'
import { FileUploader } from '../model/FileUploader'
import { ModelInfoCard } from '../model/ModelInfoCard'
import { Card, Separator } from '../ui/primitives'

export function Sidebar() {
  return (
    <aside className="space-y-5">
      <Card className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">Configuration</p>
          <h2 className="mt-1 text-lg font-semibold">Workspace Controls</h2>
        </div>
        <ApiKeyInput />
        <Separator />
        <FileUploader />
        <ModelInfoCard />
        <DownloadButton />
        <Separator />
        <SessionControls />
      </Card>
    </aside>
  )
}
