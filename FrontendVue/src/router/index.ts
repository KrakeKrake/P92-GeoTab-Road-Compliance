import { createRouter, createWebHistory } from 'vue-router'

import MainView from '../components/UI_Components/MainView.vue'
import LoginView from '../views/LoginView.vue'
import SignupView from '../views/SignupView.vue'
import ProfileView from '../views/ProfileView.vue'
import AddVehicleView from '../views/AddVehicleView.vue'
import EditVehicleView from '../views/EditVehicleView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: MainView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignupView,
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
    },
    {
      path: '/admin/add-vehicle',
      name: 'admin-add-vehicle',
      component: AddVehicleView,
    },
    {
      path: '/admin/edit-vehicle',
      name: 'admin-edit-vehicle',
      component: EditVehicleView,
    },
  ],
})

export default router