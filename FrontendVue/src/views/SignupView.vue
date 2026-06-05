<template>
  <main class="auth-page">
    <section class="auth-card">
      <div class="logo auth-logo">HeavyRoute</div>

      <div class="status-pill auth-pill">
        <div class="status-dot"></div>
        NHVR Compliance System
      </div>

      <h1 class="auth-title">Create account</h1>
      <p class="auth-subtitle">
        Create an account to save vehicles and compliance preferences.
      </p>

      <form class="auth-form" @submit.prevent="handleSignup">
        <div class="input-wrap">
          <div class="input-label">Username</div>
          <input
            v-model="username"
            class="input-field"
            type="text"
            placeholder="Enter username"
            required
          />
        </div>

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

        <div class="input-wrap">
          <div class="input-label">Licence Class</div>
          <select class="input-field" v-model="licenceClass">
            <option value="">— Select licence class —</option>
            <option value="MC">MC — Multi Combination</option>
            <option value="HC">HC — Heavy Combination</option>
            <option value="HR">HR — Heavy Rigid</option>
            <option value="MR">MR — Medium Rigid</option>
            <option value="LR">LR — Light Rigid</option>
          </select>
        </div>

        <button class="cta" type="submit">
          Sign up
        </button>

        <button class="cta secondary" type="button" @click="goLogin">
          Back to Login
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

const username = ref('')
const email = ref('')
const password = ref('')
const licenceClass = ref('')
const message = ref('')

async function handleSignup() {
  message.value = ''

  try {
    const res = await fetch('http://127.0.0.1:8000/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value,
        username: username.value,
        password: password.value,
        licence_class_id: licenceClass.value || null,
      }),
    })

    const data = await res.json()

    if (!res.ok) {
      message.value = data.detail || 'Signup failed.'
      return
    }

    localStorage.setItem('auth_token', 'local_dev_token')
    localStorage.setItem('user', JSON.stringify(data.user))
    window.dispatchEvent(new Event('auth-updated'))

    router.push('/')
  } catch (error) {
    message.value = `Signup failed: ${error}`
  }
}

function goLogin() {
  router.push('/login')
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
  width: 410px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  padding: 28px;
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