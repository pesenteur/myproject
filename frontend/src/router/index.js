import { createRouter, createWebHistory } from 'vue-router'
import ServerPage from '../pages/ServerPage.vue'

const routes = [
    {
        path: '/',
        redirect: '/server',
    },
    {
        path: '/server',
        name: 'server',
        component: ServerPage,
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router