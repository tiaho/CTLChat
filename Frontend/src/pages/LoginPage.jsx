import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'
import { Building2, Users, LogIn } from 'lucide-react'

export default function LoginPage({ onLogin, loading, demoUsers }) {
  const [selectedUser, setSelectedUser] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (selectedUser) {
      onLogin(selectedUser, navigate)
    }
  }

  const userGroups = {
    'CTLC': ['user_sample_001', 'user_sample_002']
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-background to-purple-50 p-4">
      <Card className="w-full max-w-md shadow-lg p-6">
        <div className="space-y-2 text-center mb-6">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <Building2 className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold">CTLChat</h1>
          <p className="text-base text-muted-foreground">
            AI-Powered Team Building & Planning
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            {Object.entries(userGroups).map(([org, users]) => (
              <div key={org} className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Building2 className="h-4 w-4" />
                  <span>{org}</span>
                </div>
                <div className="grid gap-2">
                  {users.map((userId) => {
                    const user = demoUsers[userId]
                    return (
                      <Button
                        key={userId}
                        type="button"
                        variant={selectedUser === userId ? "default" : "outline"}
                        className="justify-start h-auto py-3"
                        onClick={() => setSelectedUser(userId)}
                      >
                        <Users className="h-4 w-4 mr-2" />
                        <div className="flex flex-col items-start text-left">
                          <div className="font-medium">{user.name}</div>
                          <div className="text-xs opacity-70">{user.title}</div>
                        </div>
                      </Button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={!selectedUser || loading}
          >
            {loading ? (
              "Signing in..."
            ) : (
              <>
                <LogIn className="mr-2 h-4 w-4" />
                Sign In
              </>
            )}
          </Button>
        </form>

        <div className="mt-6 text-center text-xs text-muted-foreground">
          Select a demo user to continue
        </div>
      </Card>
    </div>
  )
}
