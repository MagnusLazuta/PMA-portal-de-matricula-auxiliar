<script setup>
import { ref } from 'vue'
import Login from './Login.vue'
import Sidebar from './components/SideBar.vue' 
import Home from './Home.vue'
import GenerateSchedules from './GenerateSchedules.vue'
import GeneratedSchedule from './GeneratedSchedule.vue'

const isLoggedIn = ref(false)
const currentPage = ref('home') 

const changePage = (pageName) => {
  currentPage.value = pageName
}

const logout = () => {
  isLoggedIn.value = false
  currentPage.value = 'home' 
}
</script>

<template>
  <v-app>
    <Login v-if="!isLoggedIn" @login="isLoggedIn = true" />

    <template v-else>
      <Sidebar 
        @logout="logout" 
        @change-page="changePage" 
      />

      <v-main class="bg-grey-lighten-4">
        <v-container fluid>
          <Home v-if="currentPage === 'home'"/>
          <GenerateSchedules
            v-if="currentPage === 'generate_schedules'"
            @go-generate-schedule="changePage('generated_schedule')"
          />
          <GeneratedSchedule
            v-if="currentPage === 'generated_schedule'"
            @back="changePage('generate_schedules')"
          />
        </v-container>
      </v-main>

    </template>
  </v-app>
</template>

<style scoped>
</style>