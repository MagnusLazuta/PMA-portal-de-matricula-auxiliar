<script setup>
import { ref } from 'vue'
import { useTheme, useDisplay } from 'vuetify'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  userRole: {
    type: String,
    required: true
  },
  currentPage: {
    type: String,
    default: 'home'
  }
})

const emit = defineEmits(['logout', 'change-page', 'update:modelValue'])

const isCompact = ref(false)

const theme = useTheme()
const { mobile } = useDisplay()

const toggleTheme = () => {
  const newTheme = theme.global.current.value.dark ? 'light' : 'dark'
  theme.global.name.value = newTheme
  localStorage.setItem('theme', newTheme)
}

const selectPage = (pageName) => {
  emit('change-page', pageName)
  if (mobile.value) {
    emit('update:modelValue', false)
  }
}
</script>

<template>
  <v-navigation-drawer
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    :permanent="!mobile"
    :temporary="mobile"
    :rail="!mobile && isCompact"
  >
    <v-list density="compact" nav>
      <!-- Hide collapse button on mobile -->
      <v-list-item
        v-if="!mobile"
        :prepend-icon="isCompact ? 'mdi-chevron-right' : 'mdi-chevron-left'"
        title="Ocultar Menu"
        class="mb-2"
        @click="isCompact = !isCompact"
      ></v-list-item>

      <v-divider v-if="!mobile" class="mb-2"></v-divider>

      <!-- Common Links -->
      <v-list-item
        prepend-icon="mdi-home"
        title="Início"
        value="home"
        :active="currentPage === 'home'"
        @click="selectPage('home')"
      ></v-list-item>
      <v-list-item
        prepend-icon="mdi-account"
        title="Meu Perfil"
        value="profile"
        :active="currentPage === 'profile'"
        @click="selectPage('profile')"
      ></v-list-item>


      <!-- Admin Links -->
      <template v-if="userRole === 'admin' || userRole === 'comgrad_admin'">
        <v-list-item
          prepend-icon="mdi-shield-crown"
          title="Painel Admin"
          value="admin_dashboard"
          :active="currentPage === 'admin_dashboard'"
          @click="selectPage('admin_dashboard')"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-account-multiple"
          title="Gerenciar Usuários"
          value="admin_users"
          :active="currentPage === 'admin_users'"
          @click="selectPage('admin_users')"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-book-multiple"
          title="Matrizes e Turmas"
          value="admin_academic"
          :active="currentPage === 'admin_academic'"
          @click="selectPage('admin_academic')"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-chart-bar"
          title="Relatório de Enquetes"
          value="admin_polls_report"
          :active="currentPage === 'admin_polls_report'"
          @click="selectPage('admin_polls_report')"
        ></v-list-item>
      </template>

      <v-list-item
        prepend-icon="mdi-magnify"
        title="Pesquisar Disciplinas"
        value="search_courses"
        :active="currentPage === 'search_courses'"
        @click="selectPage('search_courses')"
      ></v-list-item>

      <!-- Student Links -->
      <template v-if="userRole === 'student'">
        <v-list-item
          prepend-icon="mdi-calendar-clock"
          title="Gerar Grade"
          value="generate_schedules"
          :active="currentPage === 'generate_schedules'"
          @click="selectPage('generate_schedules')"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-poll"
          title="Enquetes"
          value="enquetes"
          :active="currentPage === 'enquetes'"
          @click="selectPage('enquetes')"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-sitemap"
          title="Grade Curricular"
          value="curriculum"
          :active="currentPage === 'curriculum'"
          @click="selectPage('curriculum')"
        ></v-list-item>
      </template>

      <!-- COMGRAD Links -->
      <template v-if="userRole === 'comgrad' || userRole === 'comgrad_admin'">
        <v-list-item
          prepend-icon="mdi-forum"
          title="Pareceres de Grade"
          value="comgrad_polls"
          :active="currentPage === 'comgrad_polls'"
          @click="selectPage('comgrad_polls')"
        ></v-list-item>
      </template>

    </v-list>

    <template v-slot:append>
      <v-divider></v-divider>
      <v-list density="compact" nav>
        <!-- Theme Switcher - only on desktop since it is in mobile app-bar -->
        <v-list-item
          v-if="!mobile"
          :prepend-icon="theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night'"
          :title="theme.global.current.value.dark ? 'Modo Claro' : 'Modo Escuro'"
          @click="toggleTheme"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-logout"
          title="Sair (Logout)"
          base-color="error"
          @click="emit('logout')"
        ></v-list-item>
      </v-list>
    </template>
  </v-navigation-drawer>
</template>

<style scoped>
</style>