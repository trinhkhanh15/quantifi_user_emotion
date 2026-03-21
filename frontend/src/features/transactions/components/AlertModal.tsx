import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { AlertTriangle } from 'lucide-react'

interface AlertModalProps {
  open: boolean
  message: string
  isLoading?: boolean
  onCancel: () => void
  onSkip: () => void
}

export function AlertModal({
  open,
  message,
  isLoading = false,
  onCancel,
  onSkip,
}: AlertModalProps) {
  return (
    <Dialog open={open}>
      <DialogContent showClose={false}>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            <DialogTitle>Financial Alert</DialogTitle>
          </div>
        </DialogHeader>
        
        <div className="py-4 text-sm text-gray-700 leading-relaxed">
          {message}
        </div>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={onSkip}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Skip & Continue
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
