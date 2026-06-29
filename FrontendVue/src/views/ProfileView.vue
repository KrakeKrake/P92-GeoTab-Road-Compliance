<template>
  <main class="auth-page">
    <section class="auth-card">
      <div class="logo auth-logo">HeavyRoute</div>

      <div class="status-pill auth-pill">
        <div class="status-dot"></div>
        User Profile
      </div>

      <h1 class="auth-title">Configure Profile</h1>

      <div v-if="user" class="profile-box">
        <p><strong>Username:</strong> {{ user.username }}</p>
        <p><strong>Email:</strong> {{ user.email }}</p>
      </div>

      <form class="auth-form" @submit.prevent="saveProfile">
        <div class="input-wrap">
          <div class="input-label">Licence Class</div>
          <select
            class="input-field"
            v-model="licenceClass"
            @change="onLicenceChange"
          >
            <option value="">— Select licence class —</option>
            <option value="MC">MC — Multi Combination</option>
            <option value="HC">HC — Heavy Combination</option>
            <option value="HR">HR — Heavy Rigid</option>
            <option value="MR">MR — Medium Rigid</option>
            <option value="LR">LR — Light Rigid</option>
          </select>
        </div>

        <div class="input-wrap">
          <div class="input-label">Favourite Vehicle</div>
          <select class="input-field" v-model="favouriteProfileId">
            <option value="">— No favourite vehicle —</option>
            <option
              v-for="profile in profiles"
              :key="profile.profile_id"
              :value="profile.profile_id"
            >
              {{ profile.display_name }}
            </option>
          </select>
          <div class="input-unit">
            Favourite vehicle options are filtered by the selected licence class.
          </div>
        </div>

        <button class="cta" type="submit">
          Save Profile
        </button>

        <button class="cta secondary" type="button" @click="goHome">
          Back to Main Page
        </button>
      </form>

      <p v-if="message" class="auth-message">
        {{ message }}
      </p>
    </section>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const API_BASE = '/api/compliance'

const router = useRouter()

const user = ref(null)
const licenceClass = ref('')
const favouriteProfileId = ref('')
const profiles = ref([])
const message = ref('')

onMounted(async () => {
  const storedUser = localStorage.getItem('user')

  if (!storedUser) {
    router.push('/login')
    return
  }

  try {
    user.value = JSON.parse(storedUser)
  } catch {
    localStorage.removeItem('user')
    router.push('/login')
    return
  }

  licenceClass.value = user.value.licence_class_id || ''
  favouriteProfileId.value = user.value.favourite_profile_id || ''

  if (licenceClass.value) {
    await loadProfilesByLicence()
  }
})

async function readJsonSafely(res) {
  const raw = await res.text()

  if (!raw) return {}

  try {
    return JSON.parse(raw)
  } catch {
    return {
      detail: raw,
    }
  }
}

async function onLicenceChange() {
  favouriteProfileId.value = ''
  await loadProfilesByLicence()
}

async function loadProfilesByLicence() {
  profiles.value = []
  message.value = ''

  if (!licenceClass.value) return

  try {
    const res = await fetch(`${API_BASE}/profiles-by-licence/${licenceClass.value}`)
    const data = await readJsonSafely(res)

    if (!res.ok) {
      message.value = data.detail || 'Failed to load vehicle profiles.'
      return
    }

    profiles.value = Array.isArray(data) ? data : []
  } catch (error) {
    message.value = `Failed to load vehicle profiles: ${error}`
  }
}

async function saveProfile() {
  message.value = ''

  if (!user.value) {
    message.value = 'No logged-in user found.'
    return
  }

  if (!licenceClass.value) {
    message.value = 'Please select a licence class.'
    return
  }

  try {
    const res = await fetch(`${API_BASE}/auth/users/${user.value.user_id}/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        licence_class_id: licenceClass.value,
        favourite_profile_id: favouriteProfileId.value || null,
      }),
    })

    const data = await readJsonSafely(res)

    if (!res.ok) {
      message.value = data.detail || 'Failed to update profile.'
      return
    }

    localStorage.setItem('user', JSON.stringify(data.user))
    window.dispatchEvent(new Event('auth-updated'))

    user.value = data.user
    licenceClass.value = data.user.licence_class_id || ''
    favouriteProfileId.value = data.user.favourite_profile_id || ''

    message.value = 'Profile updated successfully.'
  } catch (error) {
    message.value = `Failed to update profile: ${error}`
  }
}

function goHome() {
  router.push('/')
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
  width: 430px;
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
  margin-bottom: 18px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.profile-box {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 16px;
  font-family: var(--mono);
  font-size: 12px;
  color: var(--text2);
  line-height: 1.8;
}

.auth-message {
  margin-top: 14px;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--accent);
  text-align: center;
}
</style>