<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useTheme } from 'vuetify'

const theme = useTheme()
const isDark = computed(() => theme.global.current.value.dark)

const props = defineProps({
  currentUser: {
    type: Object,
    required: true
  }
})

const loading = ref(true)
const profile = ref(null)
const emailEditing = ref(false)
const editedEmail = ref('')
const saving = ref(false)

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const emailRules = [
  v => !!v || 'E-mail é obrigatório',
  v => /.+@.+\..+/.test(v) || 'E-mail deve ser válido'
]

const roleLabel = computed(() => {
  if (!profile.value) return ''
  const mapping = {
    admin: 'Administrador',
    comgrad: 'Membro da COMGRAD',
    student: 'Estudante',
    comgrad_admin: 'Membro da COMGRAD e Administrador'
  }
  return mapping[profile.value.role] || profile.value.role
})

const roleColor = computed(() => {
  if (!profile.value) return 'grey'
  const mapping = {
    admin: 'purple-darken-1',
    comgrad: 'teal-darken-1',
    student: 'blue-darken-1',
    comgrad_admin: 'amber-darken-3'
  }
  return mapping[profile.value.role] || 'grey'
})

const fetchProfile = async () => {
  loading.value = true
  try {
    const response = await axios.get(`http://localhost:8000/auth/profile/${props.currentUser.user_id}`)
    profile.value = response.data
    editedEmail.value = response.data.email
  } catch (error) {
    console.error('Erro ao carregar perfil:', error)
    showSnackbar('Erro ao carregar informações do perfil.', 'error')
  } finally {
    loading.value = false
  }
}

const startEditEmail = () => {
  editedEmail.value = profile.value.email
  emailEditing.value = true
}

const cancelEditEmail = () => {
  emailEditing.value = false
}

const saveEmail = async () => {
  if (!editedEmail.value || !/.+@.+\..+/.test(editedEmail.value)) {
    return
  }
  saving.value = true
  try {
    await axios.put(`http://localhost:8000/auth/profile/${props.currentUser.user_id}/email`, {
      email: editedEmail.value
    })
    profile.value.email = editedEmail.value
    emailEditing.value = false
    showSnackbar('E-mail atualizado com sucesso!', 'success')
  } catch (error) {
    const msg = error.response?.data?.detail || 'Erro ao atualizar e-mail.'
    showSnackbar(msg, 'error')
  } finally {
    saving.value = false
  }
}

const showSnackbar = (text, color) => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <v-container class="py-8" max-width="800">
    <h1 class="text-h4 font-weight-bold text-primary mb-6" id="profile-page-title">
      Meu Perfil
    </h1>

    <v-divider class="mb-6"></v-divider>

    <div v-if="loading" class="d-flex justify-center my-12">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <v-card v-else class="mx-auto overflow-hidden" elevation="3" rounded="lg" style="background: rgba(var(--v-theme-surface), 0.95); backdrop-filter: blur(10px);">
      <!-- Header banner with gradient -->
      <div class="bg-gradient-header py-8 px-6 text-white d-flex align-center flex-wrap gap-4">
        <v-avatar size="80" color="white" class="elevation-2 mr-4">
          <v-icon size="48" color="primary">mdi-account</v-icon>
        </v-avatar>
        <div>
          <h2 class="text-h5 font-weight-bold mb-1">{{ profile?.name }}</h2>
          <v-chip :color="roleColor" :class="isDark ? 'text-white' : 'text-grey-darken-4'" class="font-weight-bold" size="small">
            {{ roleLabel }}
          </v-chip>
        </div>
      </div>

      <v-card-text class="pa-6">
        <v-row>
          <v-col cols="12" md="6">
            <h3 class="text-subtitle-1 font-weight-bold mb-4 text-primary">Informações Gerais</h3>
            
            <v-list class="bg-transparent" density="compact">
              <v-list-item class="px-0">
                <template v-slot:prepend>
                  <v-icon color="grey-darken-1" class="mr-3">mdi-card-account-details-outline</v-icon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">Matrícula</v-list-item-title>
                <v-list-item-subtitle class="text-body-1 font-weight-medium text-high-emphasis">
                  {{ profile?.card_number }}
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item class="px-0 mt-3">
                <template v-slot:prepend>
                  <v-icon color="grey-darken-1" class="mr-3">mdi-email-outline</v-icon>
                </template>
                <v-list-item-title class="text-caption text-medium-emphasis">E-mail</v-list-item-title>
                <v-list-item-subtitle v-if="!emailEditing" class="text-body-1 font-weight-medium text-high-emphasis d-flex align-center flex-wrap gap-2">
                  {{ profile?.email }}
                  <v-btn
                    id="edit-email-btn"
                    icon="mdi-pencil"
                    variant="text"
                    size="x-small"
                    color="primary"
                    @click="startEditEmail"
                    title="Editar E-mail"
                  ></v-btn>
                </v-list-item-subtitle>
                
                <div v-else class="mt-2">
                  <v-text-field
                    id="email-input-field"
                    v-model="editedEmail"
                    :rules="emailRules"
                    label="Novo E-mail"
                    variant="outlined"
                    density="compact"
                    hide-details="auto"
                    class="mb-2"
                  ></v-text-field>
                  <div class="d-flex gap-2">
                    <v-btn
                      id="save-email-btn"
                      size="small"
                      color="success"
                      :loading="saving"
                      @click="saveEmail"
                    >
                      Salvar
                    </v-btn>
                    <v-btn
                      id="cancel-email-btn"
                      size="small"
                      variant="tonal"
                      color="grey"
                      @click="cancelEditEmail"
                    >
                      Cancelar
                    </v-btn>
                  </div>
                </div>
              </v-list-item>
            </v-list>
          </v-col>

          <!-- Academic / COMGRAD specific info -->
          <v-col cols="12" md="6" v-if="profile?.role === 'student' || profile?.comgrad_role">
            <h3 class="text-subtitle-1 font-weight-bold mb-4 text-primary">Informações do Vínculo</h3>
            
            <v-list class="bg-transparent" density="compact">
              <template v-if="profile?.role === 'student'">
                <v-list-item class="px-0">
                  <template v-slot:prepend>
                    <v-icon color="grey-darken-1" class="mr-3">mdi-school-outline</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Curso</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium text-high-emphasis">
                    {{ profile?.course }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item class="px-0 mt-3">
                  <template v-slot:prepend>
                    <v-icon color="grey-darken-1" class="mr-3">mdi-progress-clock</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Semestre Atual</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium text-high-emphasis">
                    {{ profile?.current_semester }}º Semestre
                  </v-list-item-subtitle>
                </v-list-item>

                <v-list-item class="px-0 mt-3">
                  <template v-slot:prepend>
                    <v-icon color="grey-darken-1" class="mr-3">mdi-card-bulleted-outline</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Grade Curricular</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium text-high-emphasis">
                    {{ profile?.curriculum_name || 'Não vinculada' }}
                  </v-list-item-subtitle>
                </v-list-item>
              </template>

              <template v-if="profile?.comgrad_role">
                <v-list-item class="px-0">
                  <template v-slot:prepend>
                    <v-icon color="grey-darken-1" class="mr-3">mdi-briefcase-outline</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Cargo na COMGRAD</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium text-high-emphasis">
                    {{ profile?.comgrad_role }}
                  </v-list-item-subtitle>
                </v-list-item>
              </template>
            </v-list>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="4000">
      {{ snackbarText }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar = false">Fechar</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<style scoped>
.bg-gradient-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
}
.gap-2 {
  gap: 8px;
}
.gap-4 {
  gap: 16px;
}
</style>
