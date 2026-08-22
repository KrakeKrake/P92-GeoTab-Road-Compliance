<template>
  <main class="auth-page">
    <section class="auth-card">
      <button class="auth-close" @click="router.push('/')" title="Back to dashboard">&times;</button>
      <div class="logo auth-logo">HeavyRoute</div>

      <div class="status-pill auth-pill">
        <div class="status-dot"></div>
        NHVR Compliance System
      </div>

      <h1 class="auth-title">Sign in</h1>
      <p class="auth-subtitle">
        Sign in to save vehicle preferences and access compliance features.
      </p>

      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="input-wrap">
          <div class="input-label">Email</div>
          <input
            v-model="email"
            class="input-field"
            type="email"
            placeholder="Enter email"
            required
          />
        </div>

        <div class="input-wrap">
          <div class="input-label">Password</div>
          <input
            v-model="password"
            class="input-field"
            type="password"
            placeholder="Enter password"
            required
          />
        </div>

        <button class="cta" type="submit">
          Login
        </button>

        <button class="cta secondary" type="button" @click="goSignup">
          Create Account
        </button>
      </form>

      <p v-if="message" class="auth-message">
        {{ message }}
      </p>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const email = ref('')
const password = ref('')
const message = ref('')

async function handleLogin() {
  message.value = ''

  try {
    const res = await fetch('/api/compliance/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        login: email.value,
        password: password.value,
      }),
    })

    const data = await res.json()

    if (!res.ok) {
      message.value = data.detail || 'Login failed.'
      return
    }

    localStorage.setItem('auth_token', 'local_dev_token')
    localStorage.setItem('user', JSON.stringify(data.user))
    window.dispatchEvent(new Event('auth-updated'))

    router.push('/')
  } catch (error) {
    message.value = `Login failed: ${error}`
  }
}

function goSignup() {
  router.push('/signup')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: var(--surface2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--sans);
}

.auth-card {
  width: 390px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  padding: 28px;
  position: relative;
}

.auth-close {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 28px;
  height: 28px;
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 18px;
  line-height: 1;
  color: var(--text3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background 0.15s, color 0.15s;
}

.auth-close:hover {
  background: var(--surface2);
  color: var(--text);
}

.auth-logo {
  margin-bottom: 12px;
}

.auth-pill {
  width: fit-content;
  margin-bottom: 24px;
}

.auth-title {
  font-family: var(--display);
  font-size: 26px;
  color: var(--text);
  margin-bottom: 6px;
}

.auth-subtitle {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text3);
  line-height: 1.5;
  margin-bottom: 22px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.auth-message {
  margin-top: 14px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--accent);
  text-align: center;
}
</style>