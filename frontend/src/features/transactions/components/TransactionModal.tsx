import { useState, useId } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useCreateTransaction, useAlertRegret } from '../hooks/use-transactions'
import { AlertModal } from './AlertModal'
import { TRANSACTION_CATEGORIES, type TransactionCategory } from '../constants/categories'


interface TransactionModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

function formatDateInput(d: Date) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function formatTimeInput(d: Date) {
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${min}`
}

function formatDateTimeISO(dateStr: string, timeStr: string) {
  return `${dateStr}T${timeStr}:00`
}

export function TransactionModal({ open, onOpenChange }: TransactionModalProps) {
  const [amount, setAmount] = useState('')
  const [description, setDescription] = useState('')
  const [date, setDate] = useState(formatDateInput(new Date()))
  const [time, setTime] = useState(formatTimeInput(new Date()))
  const [category, setCategory] = useState<TransactionCategory>(TRANSACTION_CATEGORIES[0])
  const amountId = useId()
  const descId = useId()
  const dateId = useId()
  const timeId = useId()
  const categoryId = useId()

  const [showAlert, setShowAlert] = useState(false)
  const [alertMessage, setAlertMessage] = useState('')
  const [pendingTransactionData, setPendingTransactionData] = useState<{
    amount: number
    description: string
    date: string
    category: string
  } | null>(null)

  const createTransaction = useCreateTransaction()
  const alertRegret = useAlertRegret()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const num = parseFloat(amount.replace(/,/g, '.'))
    if (Number.isNaN(num) || !description.trim() || !date || !time || !category.trim()) return

    const transactionData = {
      amount: num,
      description: description.trim(),
      date: formatDateTimeISO(date, time),
      category: category.trim(),
    }

    // Get alert first
    alertRegret.mutate(transactionData, {
      onSuccess: (data) => {
        setAlertMessage(data.alert)
        setPendingTransactionData(transactionData)
        setShowAlert(true)
      },
    })
  }

  const handleCancelAlert = () => {
    setShowAlert(false)
    setAlertMessage('')
    setPendingTransactionData(null)
  }

  const handleSkipAlert = () => {
    if (pendingTransactionData) {
      createTransaction.mutate(pendingTransactionData, {
        onSuccess: () => {
          setAmount('')
          setDescription('')
          setDate(formatDateInput(new Date()))
          setTime(formatTimeInput(new Date()))
          setCategory(TRANSACTION_CATEGORIES[0])
          onOpenChange(false)
          handleCancelAlert()
        },
      })
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent showClose={true}>
          <DialogHeader>
            <DialogTitle>Add transaction</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor={amountId}>Số tiền</Label>
              <Input
                id={amountId}
                type="text"
                inputMode="decimal"
                placeholder="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                disabled={createTransaction.isPending || alertRegret.isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={descId}>Description</Label>
              <Input
                id={descId}
                type="text"
                placeholder="Mô tả giao dịch"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={createTransaction.isPending || alertRegret.isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={dateId}>Date</Label>
              <Input
                id={dateId}
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                disabled={createTransaction.isPending || alertRegret.isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={timeId}>Time</Label>
              <Input
                id={timeId}
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                disabled={createTransaction.isPending || alertRegret.isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={categoryId}>Category</Label>
              <select
                id={categoryId}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={category}
                onChange={(e) => setCategory(e.target.value as TransactionCategory)}
                disabled={createTransaction.isPending || alertRegret.isPending}
              >
                {TRANSACTION_CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={createTransaction.isPending || alertRegret.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createTransaction.isPending || alertRegret.isPending || !amount || !description.trim()}>
                {alertRegret.isPending ? 'Đang kiểm tra...' : createTransaction.isPending ? 'Đang lưu...' : 'Thêm'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertModal
        open={showAlert}
        message={alertMessage}
        isLoading={createTransaction.isPending}
        onCancel={handleCancelAlert}
        onSkip={handleSkipAlert}
      />
    </>
  )
}
