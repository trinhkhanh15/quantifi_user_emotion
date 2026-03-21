import { FormEvent, useRef, useEffect, useState } from 'react'
import { Loader2, Send, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useChatbot } from '../hooks/use-chatbot'

// Simple markdown renderer component
function MarkdownContent({ content }: { content: string }) {
  const lines = content.split('\n')
  const elements: JSX.Element[] = []
  let bulletList: string[] = []

  const flushBulletList = () => {
    if (bulletList.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="list-disc list-inside space-y-1 my-2">
          {bulletList.map((item, i) => (
            <li key={`bullet-${i}`} className="text-sm">
              {item}
            </li>
          ))}
        </ul>
      )
      bulletList = []
    }
  }

  lines.forEach((line, idx) => {
    const trimmed = line.trim()

    // Heading levels: #, ##, ###, ####
    if (trimmed.startsWith('####')) {
      flushBulletList()
      const text = trimmed.replace(/^#+\s*/, '')
      elements.push(
        <h4 key={`h4-${idx}`} className="text-xs font-semibold mt-2 mb-1 text-gray-700 dark:text-gray-300">
          {text}
        </h4>
      )
      return
    }

    if (trimmed.startsWith('###')) {
      flushBulletList()
      const text = trimmed.replace(/^#+\s*/, '')
      elements.push(
        <h3 key={`h3-${idx}`} className="text-sm font-bold mt-3 mb-2">
          {text}
        </h3>
      )
      return
    }

    if (trimmed.startsWith('##')) {
      flushBulletList()
      const text = trimmed.replace(/^#+\s*/, '')
      elements.push(
        <h2 key={`h2-${idx}`} className="text-base font-bold mt-4 mb-2">
          {text}
        </h2>
      )
      return
    }

    if (trimmed.startsWith('#')) {
      flushBulletList()
      const text = trimmed.replace(/^#+\s*/, '')
      elements.push(
        <h1 key={`h1-${idx}`} className="text-lg font-bold mt-4 mb-2">
          {text}
        </h1>
      )
      return
    }

    // Bold or italic on its own line
    if ((trimmed.startsWith('**') && trimmed.endsWith('**')) || (trimmed.startsWith('_') && trimmed.endsWith('_'))) {
      flushBulletList()
      const text = trimmed.replace(/^\*\*|^_/, '').replace(/\*\*$|_$/, '')
      elements.push(
        <p key={`bold-${idx}`} className="text-sm font-semibold mt-2">
          {text}
        </p>
      )
      return
    }

    // Bullet points (-, *, +)
    if (trimmed.match(/^[-*+]\s+/)) {
      const bulletText = trimmed.replace(/^[-*+]\s+/, '')
      bulletList.push(bulletText)
      return
    }

    // Numbered list (1., 2., etc.)
    if (trimmed.match(/^\d+\.\s+/)) {
      flushBulletList()
      const itemText = trimmed.replace(/^\d+\.\s+/, '')
      elements.push(
        <ol key={`ol-${idx}`} className="list-decimal list-inside space-y-1 my-2">
          <li className="text-sm">{itemText}</li>
        </ol>
      )
      return
    }

    // Blockquote (>)
    if (trimmed.startsWith('>')) {
      flushBulletList()
      const quoteText = trimmed.replace(/^>\s*/, '')
      elements.push(
        <blockquote key={`quote-${idx}`} className="border-l-4 border-gray-300 pl-3 italic text-sm my-2 text-gray-600 dark:text-gray-400">
          {quoteText}
        </blockquote>
      )
      return
    }

    // Empty line
    if (trimmed === '') {
      flushBulletList()
      elements.push(<div key={`empty-${idx}`} className="h-2" />)
      return
    }

    // Regular paragraph text
    flushBulletList()
    elements.push(
      <p key={`p-${idx}`} className="text-sm leading-relaxed">
        {trimmed}
      </p>
    )
  })

  flushBulletList()

  return <div className="space-y-1">{elements}</div>
}

export function ChatbotPage() {
  const { messages, send, clearMessages, isLoading, error } = useChatbot()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const message = input
    setInput('')
    await send(message)
  }

  const handleClear = () => {
    if (window.confirm('Clear all messages?')) {
      clearMessages()
    }
  }

  return (
    <div className="h-full flex flex-col p-6 gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Financial Advisor Chat</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Get personalized financial advice based on your spending patterns.
          </p>
        </div>
        {messages.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleClear}
            disabled={isLoading}
            className="gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Clear
          </Button>
        )}
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardHeader className="border-b">
          <CardTitle className="text-base">Conversation</CardTitle>
          <CardDescription>Chat with your AI financial advisor</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center text-center">
              <div>
                <p className="text-muted-foreground text-sm mb-2">
                  No messages yet. Start a conversation by asking a question about your finances.
                </p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100'
                }`}
              >
                {msg.role === 'user' ? (
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                ) : (
                  <MarkdownContent content={msg.content} />
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2 flex gap-2 items-center">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-gray-700 dark:text-gray-300">Thinking...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="flex justify-center">
              <div className="bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200 rounded-lg px-4 py-2 text-sm">
                {error.message}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me about your finances..."
          disabled={isLoading}
          className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground disabled:opacity-50"
        />
        <Button
          type="submit"
          disabled={!input.trim() || isLoading}
          size="icon"
          className="gap-2"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </form>
    </div>
  )
}
