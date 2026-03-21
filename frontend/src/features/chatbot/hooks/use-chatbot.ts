import { useState, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { sendChatbotMessage } from '../api'

export type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function useChatbot() {
  const [messages, setMessages] = useState<Message[]>([])

  const mutation = useMutation({
    mutationFn: (content: string) => sendChatbotMessage(content),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: data,
          timestamp: new Date(),
        },
      ])
    },
  })

  const send = useCallback(
    (content: string) => {
      if (!content.trim()) return
      
      // Add user message optimistically
      setMessages((prev) => [
        ...prev,
        {
          id: `user-${Date.now()}`,
          role: 'user',
          content,
          timestamp: new Date(),
        },
      ])
      
      return mutation.mutateAsync(content)
    },
    [mutation]
  )

  const clearMessages = useCallback(() => setMessages([]), [])

  return {
    messages,
    send,
    clearMessages,
    isLoading: mutation.isPending,
    error: mutation.error as Error | null,
  }
}
