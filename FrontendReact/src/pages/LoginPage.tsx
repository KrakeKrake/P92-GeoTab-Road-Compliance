import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/LoginPage.css'

function LoginPage() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setMessage('')

    try {
      const res = await fetch('/api/compliance/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          login: email,
          password: password,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        setMessage(data.detail || 'Login failed.')
        return
      }

      localStorage.setItem('auth_token', 'local_dev_token')
      localStorage.setItem('user', JSON.stringify(data.user))

      window.dispatchEvent(new Event('auth-updated'))

      navigate('/')
    } catch (error) {
      setMessage(`Login failed: ${error}`)
    }
  }

  function goSignup() {
    navigate('/signup')
  }

  return (
    <main className="auth-page">
      <section className="auth-card">

        <button
          className="auth-close"
          onClick={() => navigate('/')}
          title="Back to dashboard"
        >
          &times;
        </button>

        <div className="logo auth-logo">
          HeavyRoute
        </div>

        <div className="status-pill auth-pill">
          <div className="status-dot"></div>
          NHVR Compliance System
        </div>

        <h1 className="auth-title">
          Sign in
        </h1>

        <p className="auth-subtitle">
          Sign in to save vehicle preferences and access compliance features.
        </p>

        <form className="auth-form" onSubmit={handleLogin}>

          <div className="input-wrap">
            <div className="input-label">
              Email
            </div>

            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="input-field"
              type="email"
              placeholder="Enter email"
              required
            />
          </div>

          <div className="input-wrap">
            <div className="input-label">
              Password
            </div>

            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="input-field"
              type="password"
              placeholder="Enter password"
              required
            />
          </div>

          <button className="cta" type="submit">
            Login
          </button>

          <button
            className="cta secondary"
            type="button"
            onClick={goSignup}
          >
            Create Account
          </button>

        </form>

        {message && (
          <p className="auth-message">
            {message}
          </p>
        )}

      </section>
    </main>
  )
}

export default LoginPage