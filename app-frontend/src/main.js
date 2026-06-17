import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'

// Configura o endpoint da API dinamicamente para permitir acesso via VPN ou redes locais
axios.interceptors.request.use((config) => {
  if (config.url) {
    const envApiUrl = import.meta.env.VITE_API_URL
    if (envApiUrl) {
      config.url = config.url
        .replace('http://localhost:8000', envApiUrl)
        .replace('http://127.0.0.1:8000', envApiUrl)
    } else {
      const hostname = window.location.hostname
      const protocol = window.location.protocol
      config.url = config.url
        .replace(/https?:\/\/localhost:8000/g, `${protocol}//${hostname}:8000`)
        .replace(/https?:\/\/127\.0\.0\.1:8000/g, `${protocol}//${hostname}:8000`)
    }
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

// --- Vuetify Configuration Start ---
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
  },
})

const app = createApp(App)
app.use(vuetify)
app.mount('#app')