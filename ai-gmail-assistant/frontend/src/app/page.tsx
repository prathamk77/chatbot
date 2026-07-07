'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Mail, Sparkles, Send, Calendar, BarChart3, Settings, LogOut, Moon, Sun, Plus } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [isDark, setIsDark] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [token, setToken] = useState<string | null>(null)
  const [analytics, setAnalytics] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    // Check for saved token
    const savedToken = localStorage.getItem('auth_token')
    if (savedToken) {
      setToken(savedToken)
      checkAuth(savedToken)
    }
    
    // Check dark mode preference
    const isDarkMode = localStorage.getItem('dark_mode') === 'true'
    setIsDark(isDarkMode)
    if (isDarkMode) {
      document.documentElement.classList.add('dark')
    }
  }, [])

  const checkAuth = async (authToken: string) => {
    try {
      const res = await axios.get(`${API_URL}/api/auth/status`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      if (res.data.authenticated) {
        setIsAuthenticated(true)
        fetchUser(authToken)
        fetchAnalytics(authToken)
      }
    } catch (error) {
      localStorage.removeItem('auth_token')
      setToken(null)
      setIsAuthenticated(false)
    }
  }

  const fetchUser = async (authToken: string) => {
    try {
      const res = await axios.get(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      setUser(res.data)
    } catch (error) {
      console.error('Failed to fetch user')
    }
  }

  const fetchAnalytics = async (authToken: string) => {
    try {
      const res = await axios.get(`${API_URL}/api/analytics/`, {
        headers: { Authorization: `Bearer ${authToken}` }
      })
      setAnalytics(res.data)
    } catch (error) {
      console.error('Failed to fetch analytics')
    }
  }

  const handleLogin = async () => {
    try {
      const res = await axios.get(`${API_URL}/api/auth/login`)
      window.location.href = res.data.authorization_url
    } catch (error) {
      console.error('Login failed', error)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    setToken(null)
    setIsAuthenticated(false)
    setUser(null)
    setAnalytics(null)
  }

  const toggleDarkMode = () => {
    setIsDark(!isDark)
    localStorage.setItem('dark_mode', String(!isDark))
    document.documentElement.classList.toggle('dark')
  }

  // Handle OAuth callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    
    if (code) {
      handleOAuthCallback(code)
    }
  }, [])

  const handleOAuthCallback = async (code: string) => {
    try {
      const res = await axios.get(`${API_URL}/api/auth/callback?code=${code}`)
      const { access_token } = res.data
      localStorage.setItem('auth_token', access_token)
      setToken(access_token)
      setIsAuthenticated(true)
      fetchUser(access_token)
      fetchAnalytics(access_token)
      // Clean URL
      window.history.replaceState({}, document.title, '/')
    } catch (error) {
      console.error('OAuth callback failed', error)
    }
  }

  const stats = [
    { label: 'Emails Sent', value: analytics?.total_emails_sent || 0, icon: Send },
    { label: 'Drafts', value: analytics?.total_drafts || 0, icon: Mail },
    { label: 'Scheduled', value: analytics?.total_scheduled || 0, icon: Calendar },
    { label: 'Reply Rate', value: `${analytics?.reply_rate || 0}%`, icon: BarChart3 },
  ]

  return (
    <div className={`min-h-screen ${isDark ? 'dark bg-gray-900' : 'bg-gradient-to-br from-blue-50 via-white to-purple-50'}`}>
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <motion.div 
            className="flex items-center gap-3"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <div className="p-2 rounded-xl gradient-primary">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                AI Gmail Assistant
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">Powered by Ollama AI</p>
            </div>
          </motion.div>

          <div className="flex items-center gap-4">
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            
            {isAuthenticated && user && (
              <>
                <div className="flex items-center gap-2">
                  {user.picture && (
                    <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
                  )}
                  <span className="text-sm font-medium">{user.name}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {!isAuthenticated ? (
          /* Login Screen */
          <motion.div
            className="max-w-md mx-auto mt-20 text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="glass rounded-3xl p-8 shadow-2xl">
              <div className="w-20 h-20 mx-auto mb-6 rounded-2xl gradient-primary flex items-center justify-center">
                <Mail className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-3xl font-bold mb-4">Welcome Back</h2>
              <p className="text-gray-600 dark:text-gray-300 mb-8">
                Connect your Gmail account to start using AI-powered email assistance
              </p>
              <button
                onClick={handleLogin}
                className="w-full py-4 px-6 rounded-xl gradient-primary text-white font-semibold 
                         hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
              >
                <Mail className="w-5 h-5" />
                Connect with Gmail
              </button>
              <p className="text-xs text-gray-500 mt-4">
                Secure OAuth 2.0 authentication • No passwords stored
              </p>
            </div>
          </motion.div>
        ) : (
          /* Dashboard */
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {stats.map((stat, index) => (
                <motion.div
                  key={stat.label}
                  className="glass rounded-2xl p-6"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30">
                      <stat.icon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                  </div>
                  <p className="text-3xl font-bold mb-1">{stat.value}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
                </motion.div>
              ))}
            </div>

            {/* Quick Actions */}
            <div className="glass rounded-2xl p-6 mb-8">
              <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <button className="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 
                                 dark:hover:bg-blue-900/30 transition-colors flex flex-col items-center gap-2">
                  <Plus className="w-6 h-6 text-blue-600" />
                  <span className="text-sm font-medium">Compose</span>
                </button>
                <button className="p-4 rounded-xl bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 
                                 dark:hover:bg-purple-900/30 transition-colors flex flex-col items-center gap-2">
                  <Sparkles className="w-6 h-6 text-purple-600" />
                  <span className="text-sm font-medium">AI Generate</span>
                </button>
                <button className="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 hover:bg-green-100 
                                 dark:hover:bg-green-900/30 transition-colors flex flex-col items-center gap-2">
                  <Calendar className="w-6 h-6 text-green-600" />
                  <span className="text-sm font-medium">Schedule</span>
                </button>
                <button className="p-4 rounded-xl bg-orange-50 dark:bg-orange-900/20 hover:bg-orange-100 
                                 dark:hover:bg-orange-900/30 transition-colors flex flex-col items-center gap-2">
                  <Settings className="w-6 h-6 text-orange-600" />
                  <span className="text-sm font-medium">Settings</span>
                </button>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="glass rounded-2xl p-6">
              <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50 
                                        dark:hover:bg-gray-800/50 transition-colors cursor-pointer">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 
                                  flex items-center justify-center text-white font-semibold">
                      {String.fromCharCode(64 + i)}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">Sample Email {i}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        This is a preview of the email content...
                      </p>
                    </div>
                    <span className="text-xs text-gray-400">{i}h ago</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </main>
    </div>
  )
}
