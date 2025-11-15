import React, { useState, useEffect, useRef } from 'react'
import { apiClient } from '../api/client'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Card } from '../components/ui/card'
import { Chart } from '../components/Chart'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  MessageSquare, Plus, Send, Upload, LogOut,
  Building2, User, Loader2, AlertCircle,
  FileText, Globe2, Settings
} from 'lucide-react'

export default function ChatPage({ user, org, onLogout }) {
  const [conversations, setConversations] = useState([])
  const [currentConversation, setCurrentConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [availableSources, setAvailableSources] = useState([])
  const [selectedSources, setSelectedSources] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [message, setMessage] = useState('')
  const [showSources, setShowSources] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [showModeSettings, setShowModeSettings] = useState(false)
  const [generalKnowledge, setGeneralKnowledge] = useState(false)
  const [webSearch, setWebSearch] = useState(false)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    loadConversations()
    loadSources()
  }, [user])

  useEffect(() => {
    if (currentConversation) {
      loadConversationMessages(currentConversation.conversation_id)
    }
  }, [currentConversation])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadConversations = async () => {
    try {
      const response = await apiClient.get(`/conversations?user_id=${user.id}`)
      setConversations(response.data.conversations)
    } catch (err) {
      console.error('Error loading conversations:', err)
    }
  }

  const loadSources = async () => {
    try {
      const response = await apiClient.get(`/organizations/${user.org_id}/sources?user_id=${user.id}`)
      const sources = response.data.sources || []
      setAvailableSources(sources)
      const orgWide = sources.filter(s => s.visibility === 'org-wide')
      setSelectedSources(orgWide.map(s => s.source_id))
    } catch (err) {
      console.error('Error loading sources:', err)
    }
  }

  const loadConversationMessages = async (conversationId) => {
    try {
      const response = await apiClient.get(`/conversations/${conversationId}`)
      setMessages(response.data.messages)
    } catch (err) {
      console.error('Error loading messages:', err)
    }
  }

  const handleNewConversation = async () => {
    try {
      setLoading(true)
      const response = await apiClient.post('/conversations', { user_id: user.id })
      const newConversation = {
        conversation_id: response.data.conversation_id,
        title: 'New Conversation',
        created_at: new Date().toISOString()
      }
      setConversations([newConversation, ...conversations])
      setCurrentConversation(newConversation)
      setMessages([])
      setError(null)
    } catch (err) {
      setError('Failed to create conversation')
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!currentConversation || !message.trim()) return

    setLoading(true)
    setError(null)

    try {
      const validSources = selectedSources.filter(id => id != null && id !== '')

      // Determine mode
      let mode = 'rag' // default
      if (generalKnowledge) mode = 'general_knowledge'
      else if (webSearch) mode = 'web_search'

      const response = await apiClient.post(
        `/conversations/${currentConversation.conversation_id}/messages`,
        {
          user_id: user.id,
          question: message,
          selected_sources: validSources.length > 0 ? validSources : null,
          mode: mode
        }
      )

      setMessages(prev => [...prev, {
        message_id: Math.random(),
        role: 'user',
        content: message,
        created_at: new Date().toISOString()
      }])

      setMessages(prev => [...prev, {
        message_id: Math.random(),
        role: 'assistant',
        content: response.data.answer,
        sources_used: response.data.sources_used,
        full_context: response.data.full_context,
        chart: response.data.chart,
        data: response.data.data,
        created_at: new Date().toISOString()
      }])

      setMessage('')
      await loadConversations()
    } catch (err) {
      const detail = err.response?.data?.detail
      const errorMsg = typeof detail === 'string' ? detail :
                      Array.isArray(detail) ? JSON.stringify(detail) :
                      'Failed to send message'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleSourceSelect = (sourceId) => {
    if (!sourceId) return
    setSelectedSources(prev =>
      prev.includes(sourceId)
        ? prev.filter(id => id !== sourceId)
        : [...prev, sourceId]
    )
  }

  const handleFileUpload = async (file, visibility) => {
    try {
      setLoading(true)
      const formData = new FormData()
      formData.append('file', file)
      formData.append('user_id', user.id)
      formData.append('org_id', user.org_id)
      formData.append('visibility', visibility)

      await apiClient.post('/upload', formData)

      await loadSources()
      setError(null)
      setShowUpload(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      const detail = err.response?.data?.detail
      const errorMsg = typeof detail === 'string' ? detail :
                      Array.isArray(detail) ? JSON.stringify(detail) :
                      'Failed to upload file'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const selectFile = (visibility) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.txt,.md,.pdf,.docx,.csv,.xlsx,.xls'
    input.onchange = (e) => {
      const file = e.target.files?.[0]
      if (file) {
        handleFileUpload(file, visibility)
      }
    }
    input.click()
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar - Conversations */}
      <div className="w-64 border-r bg-card flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="h-5 w-5 text-primary" />
            <div className="flex-1 min-w-0">
              <div className="font-semibold truncate">{org?.name}</div>
              <div className="text-xs text-muted-foreground truncate">{user?.name}</div>
            </div>
          </div>
          <Button
            onClick={handleNewConversation}
            className="w-full"
            disabled={loading}
          >
            <Plus className="mr-2 h-4 w-4" />
            New Chat
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {conversations.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground p-4">
              No conversations yet
            </div>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.conversation_id}
                onClick={() => setCurrentConversation(conv)}
                className={`w-full text-left p-3 rounded-lg mb-1 transition-colors ${
                  currentConversation?.conversation_id === conv.conversation_id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                }`}
              >
                <div className="flex items-start gap-2">
                  <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">
                      {conv.title || 'New Conversation'}
                    </div>
                    <div className="text-xs opacity-70">
                      {new Date(conv.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        <div className="p-4 border-t space-y-2">
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => setShowUpload(!showUpload)}
          >
            <Upload className="mr-2 h-4 w-4" />
            Upload
          </Button>
          {showUpload && (
            <Card className="p-2 space-y-1">
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start"
                onClick={() => selectFile('personal')}
              >
                <User className="mr-2 h-3 w-3" />
                Personal
              </Button>
              {isAdmin && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start"
                  onClick={() => selectFile('org-wide')}
                >
                  <Building2 className="mr-2 h-3 w-3" />
                  Organization
                </Button>
              )}
            </Card>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-destructive hover:text-destructive"
            onClick={onLogout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Sign Out
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {error && (
          <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-3 flex items-center gap-2 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        {!currentConversation ? (
          <div className="flex-1 flex items-center justify-center text-center p-8">
            <div className="max-w-md">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <h2 className="text-2xl font-semibold mb-2">Welcome to OrgRAG</h2>
              <p className="text-muted-foreground mb-4">
                Create a new conversation or select an existing one to start chatting with your organization's knowledge base.
              </p>
              <Button onClick={handleNewConversation}>
                <Plus className="mr-2 h-4 w-4" />
                Start New Conversation
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-muted-foreground">
                    <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Start by asking a question</p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.message_id}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <Card className={`max-w-[80%] p-4 ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}>
                      {msg.role === 'user' ? (
                        <div className="whitespace-pre-wrap break-words">
                          {msg.content}
                        </div>
                      ) : (
                        <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:font-semibold prose-h1:text-xl prose-h2:text-lg prose-h3:text-base prose-p:leading-relaxed prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5">
                          {msg.chart && <Chart config={msg.chart} />}
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              code({node, inline, className, children, ...props}) {
                                return inline ? (
                                  <code className="bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-slate-100 px-1.5 py-0.5 rounded text-sm font-mono border border-slate-300 dark:border-slate-700" {...props}>
                                    {children}
                                  </code>
                                ) : (
                                  <code className="font-mono text-sm" {...props}>
                                    {children}
                                  </code>
                                )
                              },
                              pre({children}) {
                                return (
                                  <pre className="bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100 p-4 rounded-lg border border-slate-300 dark:border-slate-700 overflow-x-auto my-4">
                                    {children}
                                  </pre>
                                )
                              }
                            }}
                          >
                            {msg.content?.replace('[CHART_PLACEHOLDER]', '')}
                          </ReactMarkdown>
                        </div>
                      )}
                      {msg.sources_used && msg.sources_used.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-border/20">
                          <div className="text-xs font-medium mb-2">Sources:</div>
                          <div className="flex flex-wrap gap-1">
                            {msg.sources_used.map((source, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                <FileText className="h-3 w-3 mr-1" />
                                {source}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </Card>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t p-4">
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setShowSources(!showSources)}
                  disabled={generalKnowledge || webSearch}
                  title="Select document sources"
                >
                  <FileText className="h-4 w-4" />
                </Button>
                <Button
                  type="button"
                  variant={(generalKnowledge || webSearch) ? "default" : "outline"}
                  size="icon"
                  onClick={() => setShowModeSettings(!showModeSettings)}
                  title="Query mode settings"
                >
                  <Settings className="h-4 w-4" />
                </Button>
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder={
                    generalKnowledge ? "Ask anything..." :
                    webSearch ? "Search the web..." :
                    "Ask a question..."
                  }
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

              {showModeSettings && (
                <Card className="mt-2 p-3">
                  <div className="text-sm font-medium mb-2">Query Mode</div>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer">
                      <input
                        type="checkbox"
                        checked={generalKnowledge}
                        onChange={() => {
                          setGeneralKnowledge(!generalKnowledge)
                          if (!generalKnowledge) setWebSearch(false)
                        }}
                        className="rounded"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium">General Knowledge</div>
                        <div className="text-xs text-muted-foreground">Use Claude's general knowledge without documents</div>
                      </div>
                    </label>
                    <label className="flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer">
                      <input
                        type="checkbox"
                        checked={webSearch}
                        onChange={() => {
                          setWebSearch(!webSearch)
                          if (!webSearch) setGeneralKnowledge(false)
                        }}
                        className="rounded"
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium">Web Search</div>
                        <div className="text-xs text-muted-foreground">Search the web for current information</div>
                      </div>
                    </label>
                  </div>
                </Card>
              )}

              {showSources && (
                <Card className="mt-2 p-3">
                  <div className="text-sm font-medium mb-2">Select Sources</div>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {availableSources.map((source) => (
                      <label
                        key={source.source_id}
                        className="flex items-center gap-2 p-2 rounded hover:bg-accent cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedSources.includes(source.source_id)}
                          onChange={() => handleSourceSelect(source.source_id)}
                          className="rounded"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm truncate">{source.name}</div>
                        </div>
                        {source.visibility === 'org-wide' ? (
                          <Globe2 className="h-3 w-3 text-muted-foreground" />
                        ) : (
                          <User className="h-3 w-3 text-muted-foreground" />
                        )}
                      </label>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
