<template>
  <div class="login-page">
    <div class="login-card panel">
      <h2>{{ isRegister ? $t('login.register') : $t('login.title') }}</h2>
      <form @submit.prevent="submit">
        <input v-model="username" :placeholder="$t('login.username')" required />
        <input v-model="password" type="password" :placeholder="$t('login.password')" required />
        <button type="submit" :disabled="loading">{{ loading ? '...' : isRegister ? $t('login.register') : $t('login.title') }}</button>
        <div v-if="error" class="error">{{ error }}</div>
      </form>
      <a href="#" @click.prevent="isRegister = !isRegister" class="toggle">
        {{ isRegister ? $t('login.haveAccount') : $t('login.needAccount') }}
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth.js'

const { t } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')
const isRegister = ref(false)
const loading = ref(false)
const error = ref('')

async function submit() {
  loading.value = true; error.value = ''
  try {
    if (isRegister.value) {
      await authStore.register(username.value, password.value)
      isRegister.value = false; error.value = t('login.registered')
    } else {
      await authStore.login(username.value, password.value); router.push('/dashboard')
    }
  } catch (e) { error.value = e.response?.data?.detail || t('login.failed') }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-page { display: flex; align-items: center; justify-content: center; min-height: 60vh; }
.login-card { width: 340px; text-align: center; }
h2 { margin-bottom: 20px; }
form { display: flex; flex-direction: column; gap: 12px; }
input { width: 100%; } button { width: 100%; }
.error { color: var(--danger); font-size: 13px; margin-top: 4px; }
.toggle { display: block; margin-top: 16px; font-size: 13px; }
</style>
