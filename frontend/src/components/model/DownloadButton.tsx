import { Download } from 'lucide-react'
import { useAppStore } from '../../store/appStore'
import { Button } from '../ui/primitives'

export function DownloadButton() {
  const modelInfo = useAppStore((state) => state.modelInfo)
  const downloadModel = useAppStore((state) => state.downloadModel)
  const setError = useAppStore((state) => state.setError)

  return (
    <Button
      className="w-full justify-center"
      disabled={!modelInfo}
      onClick={async () => {
        try {
          await downloadModel()
        } catch (error) {
          setError(error instanceof Error ? error.message : 'Download failed')
        }
      }}
    >
      <Download className="h-4 w-4" />
      Download Model
    </Button>
  )
}
