<script setup>
import { ref, computed } from 'vue'
import { useTheme, useDisplay } from 'vuetify'
import Login from './Login.vue'
import Sidebar from './components/SideBar.vue' 
import Home from './Home.vue'
import GenerateSchedules from './GenerateSchedules.vue'
import GeneratedSchedule from './GeneratedSchedule.vue'
import StudentPolls from './StudentPolls.vue'
import ComgradDashboard from './ComgradDashboard.vue'
import AdminDashboard from './AdminDashboard.vue'
import ManageUsers from './ManageUsers.vue'
import ManageAcademicData from './ManageAcademicData.vue'
import PollsReport from './PollsReport.vue'
import CurriculumPage from './CurriculumPage.vue'
import SearchCourses from './SearchCourses.vue'
import UserProfile from './UserProfile.vue'
import SetupWizard from './SetupWizard.vue'
import axios from 'axios'

const theme = useTheme()
const { mobile } = useDisplay()
const drawer = ref(false)

// Initialize theme from localStorage if it exists, otherwise use 'light'
const savedTheme = localStorage.getItem('theme') || 'light'
theme.global.name.value = savedTheme

const toggleTheme = () => {
  const newTheme = theme.global.current.value.dark ? 'light' : 'dark'
  theme.global.name.value = newTheme
  localStorage.setItem('theme', newTheme)
}

const isLoggedIn = ref(false)
const currentUser = ref(null) // { user_id, name, role, student_id }
const currentPage = ref('home') 

const pageTitle = computed(() => {
  const mapping = {
    home: 'Início',
    profile: 'Meu Perfil',
    curriculum: 'Grade Curricular',
    admin_dashboard: 'Painel Admin',
    admin_users: 'Gerenciar Usuários',
    admin_academic: 'Matrizes e Turmas',
    admin_polls_report: 'Relatório de Enquetes',
    search_courses: 'Pesquisar Disciplinas',
    generate_schedules: 'Gerar Grade',
    generated_schedule: 'Grade Gerada',
    enquetes: 'Enquetes',
    comgrad_polls: 'Pareceres de Grade'
  }
  return mapping[currentPage.value] || 'PMA - UFRGS'
})

const studentId = ref(1)
const selectedSemester = ref(null)

const mustChangePasswordDialog = ref(false)
const newPassword = ref('')
const confirmNewPassword = ref('')
const changingPassword = ref(false)
const setupRequired = ref(false)


const extendSession = () => {
  const sessionStr = localStorage.getItem('user_session')
  if (sessionStr) {
    try {
      const session = JSON.parse(sessionStr)
      session.expiresAt = Date.now() + 30 * 60 * 1000 // Extend by 30 min
      localStorage.setItem('user_session', JSON.stringify(session))
    } catch (e) {
      localStorage.removeItem('user_session')
    }
  }
}

const checkActiveSession = () => {
  const sessionStr = localStorage.getItem('user_session')
  if (sessionStr) {
    try {
      const session = JSON.parse(sessionStr)
      if (Date.now() < session.expiresAt) {
        currentUser.value = session.user
        studentId.value = session.user.student_id || 1
        isLoggedIn.value = true
        
        if (session.user.role === 'comgrad') {
          currentPage.value = 'comgrad_polls'
        } else if (session.user.role === 'admin' || session.user.role === 'comgrad_admin') {
          currentPage.value = 'admin_dashboard'
        } else {
          currentPage.value = 'home'
        }
        
        extendSession()
      } else {
        localStorage.removeItem('user_session')
      }
    } catch (e) {
      console.error('Erro ao restaurar sessão:', e)
      localStorage.removeItem('user_session')
    }
  }
}

const checkSetupStatus = async () => {
  try {
    const response = await axios.get('http://localhost:8000/auth/setup-status')
    setupRequired.value = response.data.setup_required
    if (!setupRequired.value) {
      checkActiveSession()
    }
  } catch (e) {
    console.error('Erro ao verificar status do setup:', e)
    checkActiveSession()
  }
}

const handleSetupComplete = () => {
  setupRequired.value = false
}

// Perform initial setup and session verification
checkSetupStatus()


const handleLogin = (userData) => {
  currentUser.value = userData
  studentId.value = userData.student_id || 1
  isLoggedIn.value = true
  
  // Save session in localStorage with a 30-minute expiration
  const sessionData = {
    user: userData,
    expiresAt: Date.now() + 30 * 60 * 1000
  }
  localStorage.setItem('user_session', JSON.stringify(sessionData))
  
  if (userData.must_change_password) {
    mustChangePasswordDialog.value = true
    newPassword.value = ''
    confirmNewPassword.value = ''
  }
  
  if (userData.role === 'comgrad') {
    currentPage.value = 'comgrad_polls'
  } else if (userData.role === 'admin' || userData.role === 'comgrad_admin') {
    currentPage.value = 'admin_dashboard'
  } else {
    currentPage.value = 'home'
  }
}

const changePage = (pageName) => {
  currentPage.value = pageName
  extendSession()
}

const handleGoGenerateSchedule = (semester) => {
  selectedSemester.value = semester
  currentPage.value = 'generated_schedule'
  extendSession()
}

const logout = () => {
  isLoggedIn.value = false
  currentUser.value = null
  currentPage.value = 'home' 
  mustChangePasswordDialog.value = false
  localStorage.removeItem('user_session')
}

const submitFirstAccessPassword = async () => {
  if (newPassword.value.length < 6 || newPassword.value !== confirmNewPassword.value) {
    return
  }
  changingPassword.value = true
  try {
    await axios.post('http://localhost:8000/auth/change-password', {
      user_id: currentUser.value.user_id,
      new_password: newPassword.value
    })
    mustChangePasswordDialog.value = false
    alert('Senha alterada com sucesso! Bem-vindo ao portal.')
  } catch (err) {
    console.error('Erro ao alterar senha:', err)
    alert(err?.response?.data?.detail || 'Erro ao alterar a senha. Tente novamente.')
  } finally {
    changingPassword.value = false
  }
}
</script>

<template>
  <v-app>
    <SetupWizard v-if="setupRequired" @setup-complete="handleSetupComplete" />

    <template v-else>
      <!-- Floating button to toggle theme, visible on login screen -->
      <v-btn
        v-if="!isLoggedIn"
        icon
        position="fixed"
        location="top right"
        class="ma-4"
        style="z-index: 1009;"
        @click="toggleTheme"
        :title="theme.global.current.value.dark ? 'Mudar para Modo Claro' : 'Mudar para Modo Escuro'"
      >
        <v-icon :color="theme.global.current.value.dark ? 'yellow-darken-1' : 'indigo-darken-3'">
          {{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}
        </v-icon>
      </v-btn>

      <Login v-if="!isLoggedIn" @login="handleLogin" />

      <template v-else>
        <!-- App Bar para Telas Mobile -->
        <v-app-bar v-if="mobile" flat border>
          <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
          <v-app-bar-title class="font-weight-bold text-primary">{{ pageTitle }}</v-app-bar-title>
          
          <v-spacer></v-spacer>

          <v-btn
            icon
            @click="toggleTheme"
            :title="theme.global.current.value.dark ? 'Modo Claro' : 'Modo Escuro'"
            class="mr-2"
          >
            <v-icon :color="theme.global.current.value.dark ? 'yellow-darken-1' : 'indigo-darken-3'">
              {{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}
            </v-icon>
          </v-btn>
        </v-app-bar>

        <Sidebar 
          v-model="drawer"
          :userRole="currentUser?.role || 'student'"
          :currentPage="currentPage"
          @logout="logout" 
          @change-page="changePage" 
        />

        <v-main :class="theme.global.current.value.dark ? 'bg-background' : 'bg-grey-lighten-4'">
          <v-container fluid>
            <Home 
              v-if="currentPage === 'home'"
              :user="currentUser"
            />
            <CurriculumPage
              v-if="currentPage === 'curriculum'"
              :studentId="studentId"
            />
            <SearchCourses
              v-if="currentPage === 'search_courses'"
            />
            <GenerateSchedules
              v-if="currentPage === 'generate_schedules'"
              :studentId="studentId"
              @go-generate-schedule="handleGoGenerateSchedule"
            />
            <GeneratedSchedule
              v-if="currentPage === 'generated_schedule'"
              :studentId="studentId"
              :semester="selectedSemester"
              @back="changePage('generate_schedules')"
            />
            <StudentPolls
              v-if="currentPage === 'enquetes'"
              :studentId="studentId"
            />
            <ComgradDashboard
              v-if="currentPage === 'comgrad_polls'"
              :userId="currentUser?.user_id"
              :userRole="currentUser?.role || 'comgrad'"
            />
            <AdminDashboard
              v-if="currentPage === 'admin_dashboard'"
            />
            <ManageUsers
              v-if="currentPage === 'admin_users'"
            />
            <ManageAcademicData
              v-if="currentPage === 'admin_academic'"
            />
            <PollsReport
              v-if="currentPage === 'admin_polls_report'"
            />
            <UserProfile
              v-if="currentPage === 'profile'"
              :currentUser="currentUser"
            />
          </v-container>
        </v-main>


        <!-- Dialog for Mandatory Password Change on First Access -->
        <v-dialog v-model="mustChangePasswordDialog" persistent max-width="450px">
          <v-card class="pa-4">
            <v-card-title class="text-h5 font-weight-bold text-error d-flex align-center">
              <v-icon color="error" class="mr-2">mdi-shield-alert</v-icon>
              Alteração de Senha Obrigatória
            </v-card-title>
            <v-card-text class="pt-4">
              <p class="text-body-2 mb-4">
                Este é o seu primeiro acesso. Por questões de segurança, você deve alterar a sua senha inicial antes de prosseguir.
              </p>
              <v-form @submit.prevent="submitFirstAccessPassword">
                <v-text-field
                  v-model="newPassword"
                  label="Nova Senha"
                  type="password"
                  variant="outlined"
                  required
                  class="mb-3"
                  placeholder="Mínimo 6 caracteres"
                ></v-text-field>
                <v-text-field
                  v-model="confirmNewPassword"
                  label="Confirmar Nova Senha"
                  type="password"
                  variant="outlined"
                  required
                  class="mb-3"
                ></v-text-field>
              </v-form>
            </v-card-text>
            <v-card-actions class="pa-4 justify-end">
              <v-btn color="error" variant="text" @click="logout">Sair</v-btn>
              <v-btn color="primary" variant="flat" :loading="changingPassword" @click="submitFirstAccessPassword" :disabled="newPassword.length < 6 || newPassword !== confirmNewPassword">
                Alterar Senha
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </template>
    </template>
  </v-app>
</template>

<style>
@media print {
  /* Hide sidebar and navigation drawer when printing */
  .v-navigation-drawer,
  .v-navigation-drawer__content,
  .v-navigation-drawer--rail,
  .no-print,
  .v-btn,
  button {
    display: none !important;
  }

  /* Reset main content wrapper layout for full-width print */
  .v-main {
    padding: 0 !important;
    margin: 0 !important;
    --v-layout-left: 0px !important;
    --v-layout-right: 0px !important;
    --v-layout-top: 0px !important;
    --v-layout-bottom: 0px !important;
    background: white !important;
  }

  .v-container {
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
  }
}
</style>