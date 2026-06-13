import { createApp } from 'vue'
import { createPinia } from 'pinia'
import AdminApp from './AdminApp.vue'
import adminRouter from './router'
import i18n from '@/i18n'
import '@/assets/styles/main.css'
import '@/styles/animations.css'

const app = createApp(AdminApp)

app.use(createPinia())
app.use(adminRouter)
app.use(i18n)

app.mount('#admin-app')
