import { api } from '@/api/axios'

export type ChatbotResponse = string

export async function sendChatbotMessage(content: string): Promise<ChatbotResponse> {
  // Send content as query param and transaction with default values in body
  // Note: amount must be > 0 according to backend validation
  // Note: omit date field to use backend default (avoids timezone mismatch)
  const response = await api.post<ChatbotResponse>(
    '/chatbot/request',
    {
      amount: 0.01, // Must be > 0 per backend validation
      category: 'uncategorized',
      description: 'consultation',
    },
    {
      params: { content },
    }
  )
  return response.data
}
