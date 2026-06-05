<template>
  <div class="user-chip-wrapper" ref="userChipRef">
    <div class="user-chip" @click="toggleMenu">
      <div class="user-avatar">{{ userInitial }}</div>
      <span>{{ userLabel }}</span>
    </div>

    <div v-if="menuOpen" class="user-menu">
      <template v-if="!isLoggedIn">
        <button @click="goLogin">Login</button>
        <button @click="goSignup">Sign up</button>
      </template>

      <template v-else>
        <button @click="goProfile">Configure Profile</button>
        <button @click="signOut">Sign out</button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const menuOpen = ref(false)
const authVersion = ref(0)
const userChipRef = ref(null)

function refreshAuth() {
  authVersion.value++
}

const user = computed(() => {
  authVersion.value

  try {
    const storedUser = localStorage.getItem('user')
    return storedUser ? JSON.parse(storedUser) : null
  } catch {
    return null
  }
})

const isLoggedIn = computed(() => {
  authVersion.value
  return !!localStorage.getItem('auth_token') && !!user.value
})

const userInitial = computed(() => {
  if (!user.value) return '?'

  const displayName = user.value.username || user.value.email || 'User'
  return displayName.charAt(0).toUpperCase()
})

const userLabel = computed(() => {
  if (!user.value) return 'Not signed in'

  return user.value.username || user.value.email || 'User'
})

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

function handleClickOutside(event) {
  if (!userChipRef.value) return

  if (!userChipRef.value.contains(event.target)) {
    closeMenu()
  }
}

function goLogin() {
  closeMenu()
  router.push('/login')
}

function goSignup() {
  closeMenu()
  router.push('/signup')
}

function goProfile() {
  closeMenu()
  router.push('/profile')
}

function signOut() {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user')

  sessionStorage.removeItem('guest_selected_licence_class')
  sessionStorage.removeItem('p1_selected_licence_class')

  refreshAuth()
  closeMenu()

  window.dispatchEvent(new Event('auth-updated'))

  router.push('/').then(() => {
    window.location.reload()
  })
}

onMounted(() => {
  window.addEventListener('auth-updated', refreshAuth)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('auth-updated', refreshAuth)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.user-chip-wrapper {
  position: relative;
}

.user-menu {
  position: absolute;
  top: 38px;
  right: 0;
  width: 170px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 8px 24px rgba(0,0,0,0.10);
  padding: 6px;
  z-index: 200;
}

.user-menu button {
  width: 100%;
  background: transparent;
  border: none;
  padding: 9px 10px;
  text-align: left;
  border-radius: 6px;
  font-family: var(--sans);
  font-size: 12px;
  color: var(--text2);
  cursor: pointer;
}

.user-menu button:hover {
  background: var(--accent-glow);
  color: var(--accent);
}
</style>