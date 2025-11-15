import React, { useState, useEffect, useRef } from 'react'
import { apiClient } from '../api/client'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Card } from '../components/ui/card'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Send, Upload, Loader2, AlertCircle, FileText, Database, Trash2
} from 'lucide-react'

export default function SimpleChatPage() {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState('')
  const [stats, setStats] = useState(null)
  const [uploadFile, setUploadFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadStats()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadStats = async () => {
    try {
      const response = await apiClient.getStats()
      setStats(response.data)
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!message.trim()) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setMessage('')
    setLoading(true)
    setError(null)

    try {
      // Filter out system messages and only include user/assistant messages
      const conversationHistory = messages
        .filter(msg => msg.role === 'user' || msg.role === 'assistant')
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }))

      const response = await apiClient.chat(message, conversationHistory, 5)

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources || [],
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to send message'
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async () => {
    if (!uploadFile) return

    setUploading(true)
    setError(null)

    try {
      const response = await apiClient.uploadFile(uploadFile)
      setUploadFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''

      // Show success message
      const successMessage = {
        id: Date.now(),
        role: 'system',
        content: `Successfully uploaded ${response.data.filename}. Added ${response.data.chunks_added} chunks. Total documents: ${response.data.total_documents}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, successMessage])

      // Reload stats
      await loadStats()
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to upload file'
      setError(detail)
    } finally {
      setUploading(false)
    }
  }

  const handleClearChat = () => {
    setMessages([])
    setError(null)
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">CTLChat RAG</h1>
            <p className="text-sm text-muted-foreground">
              Retrieval-Augmented Generation Chatbot
            </p>
          </div>
          <div className="flex items-center gap-4">
            {stats && (
              <div className="flex items-center gap-2 text-sm">
                <Database className="h-4 w-4" />
                <span className="text-muted-foreground">
                  {stats.total_documents} documents
                </span>
                <Badge variant="outline" className="text-xs">
                  {stats.embedding_model}
                </Badge>
              </div>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearChat}
              disabled={messages.length === 0}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-3">
          <div className="max-w-4xl mx-auto flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto">×</button>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-muted-foreground">
                <Database className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <h2 className="text-xl font-semibold mb-2">Welcome to CTLChat</h2>
                <p className="mb-4">Upload documents and start asking questions</p>
                <div className="text-sm space-y-2">
                  <p>Supported formats: .txt, .pdf, .docx, .md</p>
                  {stats && <p className="text-xs">Currently {stats.total_documents} documents indexed</p>}
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <Card className={`max-w-[80%] p-4 ${
                  msg.role === 'user' ? 'bg-primary text-primary-foreground' :
                  msg.role === 'system' ? 'bg-green-50 dark:bg-green-900/20 border-green-200' :
                  'bg-muted'
                }`}>
                  {msg.role === 'user' ? (
                    <div className="whitespace-pre-wrap break-words">
                      {msg.content}
                    </div>
                  ) : msg.role === 'system' ? (
                    <div className="text-sm text-green-800 dark:text-green-200">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border/20">
                      <div className="text-xs font-medium mb-2">Sources:</div>
                      <div className="flex flex-wrap gap-2">
                        {msg.sources.map((source, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            <FileText className="h-3 w-3 mr-1" />
                            {source.source}
                            <span className="ml-1 opacity-70">
                              ({(source.distance * 100).toFixed(0)}%)
                            </span>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground mt-2">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </Card>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t p-4 bg-card">
        <div className="max-w-4xl mx-auto">
          {/* File Upload */}
          <div className="mb-3 flex items-center gap-2">
            <Input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.pdf,.docx"
              onChange={(e) => setUploadFile(e.target.files?.[0])}
              disabled={uploading}
              className="flex-1"
            />
            <Button
              onClick={handleFileUpload}
              disabled={!uploadFile || uploading}
              variant="outline"
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload
                </>
              )}
            </Button>
          </div>

          {/* Message Input */}
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={loading}
              className="flex-1"
            />
            <Button type="submit" disabled={!message.trim() || loading}>
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
