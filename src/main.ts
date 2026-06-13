import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import i18n, { defaultLocale } from './i18n'
import { getLocaleConfig } from './locales/registry'
import './assets/styles/main.css'
import './styles/animations.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

document.documentElement.lang = getLocaleConfig(defaultLocale).htmlLang

app.mount('#app')
