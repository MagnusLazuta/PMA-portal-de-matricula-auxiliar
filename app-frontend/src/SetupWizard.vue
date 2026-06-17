<script setup>
import { ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['setup-complete'])

const name = ref('')
const email = ref('')
const cardNumber = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const showPassword = ref(false)

const nameRules = [
  v => !!v || 'Nome Completo é obrigatório',
  v => v.trim().length >= 3 || 'Nome deve conter pelo menos 3 caracteres'
]

const emailRules = [
  v => !!v || 'E-mail é obrigatório',
  v => /.+@.+\..+/.test(v) || 'E-mail deve ser válido'
]

const cardRules = [
  v => !!v || 'Matrícula é obrigatória',
  v => /^\d{8}$/.test(v) || 'A matrícula deve conter exatamente 8 dígitos numéricos'
]

const passwordRules = [
  v => !!v || 'Senha é obrigatória',
  v => v.length >= 6 || 'A senha deve conter pelo menos 6 caracteres'
]

const confirmPasswordRules = [
  v => !!v || 'Confirmação de senha é obrigatória',
  v => v === password.value || 'As senhas não coincidem'
]

const formIsValid = ref(false)

const submitSetup = async () => {
  if (!name.value || !email.value || !cardNumber.value || !password.value || password.value !== confirmPassword.value) {
    return
  }
  
  loading.value = true
  try {
    const payload = {
      name: name.value.trim(),
      email: email.value.trim(),
      card_number: cardNumber.value.trim(),
      password: password.value
    }
    
    await axios.post('http://localhost:8000/auth/setup-admin', payload)
    showSnackbar('Administrador Geral cadastrado com sucesso!', 'success')
    
    // Short delay so the user can see the message before reloading
    setTimeout(() => {
      emit('setup-complete')
    }, 1500)
    
  } catch (error) {
    const msg = error.response?.data?.detail || 'Erro ao realizar a configuração inicial.'
    showSnackbar(msg, 'error')
  } finally {
    loading.value = false
  }
}

const showSnackbar = (text, color) => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}
</script>

<template>
  <v-container class="fill-height d-flex align-center justify-center bg-setup-gradient py-12" fluid>
    <v-card class="pa-8 elevation-12 w-100 max-w-500 overflow-hidden" rounded="xl" style="background: rgba(var(--v-theme-surface), 0.95); backdrop-filter: blur(15px);">
      
      <!-- Top header with UFRGS Logo -->
      <div class="text-center mb-6">
        <v-img
          src="/ufrgs.svg"
          alt="UFRGS Logo"
          max-height="90"
          contain
          class="mx-auto mb-4"
        ></v-img>
        <h1 class="text-h4 font-weight-black text-primary mb-1">
          Configuração Inicial
        </h1>
        <p class="text-body-2 text-medium-emphasis">
          Bem-vindo ao PMA - UFRGS! Crie a conta do primeiro Administrador Geral para prosseguir com o sistema.
        </p>
      </div>

      <v-form v-model="formIsValid" @submit.prevent="submitSetup">
        <v-row dense>
          <v-col cols="12">
            <v-text-field
              id="setup-name-field"
              v-model="name"
              :rules="nameRules"
              label="Nome Completo"
              prepend-inner-icon="mdi-account-outline"
              variant="outlined"
              density="comfortable"
              required
              class="mb-1"
            ></v-text-field>
          </v-col>

          <v-col cols="12">
            <v-text-field
              id="setup-email-field"
              v-model="email"
              :rules="emailRules"
              label="E-mail Institucional"
              prepend-inner-icon="mdi-email-outline"
              variant="outlined"
              density="comfortable"
              type="email"
              required
              class="mb-1"
            ></v-text-field>
          </v-col>

          <v-col cols="12">
            <v-text-field
              id="setup-card-field"
              v-model="cardNumber"
              :rules="cardRules"
              label="Matrícula (8 dígitos)"
              prepend-inner-icon="mdi-card-account-details-outline"
              variant="outlined"
              density="comfortable"
              maxLength="8"
              required
              class="mb-1"
            ></v-text-field>
          </v-col>

          <v-col cols="12">
            <v-text-field
              id="setup-password-field"
              v-model="password"
              :rules="passwordRules"
              label="Senha"
              prepend-inner-icon="mdi-lock-outline"
              :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
              :type="showPassword ? 'text' : 'password'"
              @click:append-inner="showPassword = !showPassword"
              variant="outlined"
              density="comfortable"
              required
              class="mb-1"
            ></v-text-field>
          </v-col>

          <v-col cols="12">
            <v-text-field
              id="setup-confirm-password-field"
              v-model="confirmPassword"
              :rules="confirmPasswordRules"
              label="Confirmar Senha"
              prepend-inner-icon="mdi-lock-check-outline"
              type="password"
              variant="outlined"
              density="comfortable"
              required
              class="mb-4"
            ></v-text-field>
          </v-col>

          <v-col cols="12">
            <v-btn
              id="submit-setup-btn"
              type="submit"
              color="primary"
              size="large"
              block
              rounded="lg"
              class="font-weight-bold elevation-2 py-6 d-flex align-center justify-center"
              :loading="loading"
              :disabled="!formIsValid"
            >
              Concluir Configuração
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
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
.bg-setup-gradient {
  background: linear-gradient(135deg, #0d47a1 0%, #1976d2 50%, #42a5f5 100%);
  min-height: 100vh;
}
.max-w-500 {
  max-width: 480px;
}
</style>
