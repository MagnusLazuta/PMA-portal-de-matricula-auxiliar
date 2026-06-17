<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import UfrgsLogo from './components/UfrgsLogo.vue'

const emit = defineEmits(['login'])

const matricula = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

const forgotPasswordDialog = ref(false)
const recoveryStep = ref(1)
const recoveryMatricula = ref('')
const recoveryEmail = ref('')
const recoveryNewPassword = ref('')
const recoveryConfirmPassword = ref('')
const recoveryLoading = ref(false)
const recoveryError = ref('')

const isFormValid = computed(() => {
  return matricula.value.length === 8 && /^\d+$/.test(matricula.value) && password.value !== ''
})

const isRecoveryValid = computed(() => {
  return recoveryMatricula.value.length === 8 && /^\d+$/.test(recoveryMatricula.value)
})

const handleLogin = async () => {
  if (!isFormValid.value) {
    errorMsg.value = 'A matrícula deve conter exatamente 8 dígitos numéricos.'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const response = await axios.post('http://localhost:8000/auth/login', {
      card_number: matricula.value,
      password: password.value
    })


    emit('login', response.data)
  } catch (error) {
    console.error('Erro ao efetuar login:', error)
    if (error.response && error.response.data && error.response.data.detail) {
      errorMsg.value = error.response.data.detail
    } else {
      errorMsg.value = 'Erro ao conectar ao servidor de autenticação.'
    }
  } finally {
    loading.value = false
  }
}

const openForgotPassword = () => {
  forgotPasswordDialog.value = true
  recoveryStep.value = 1
  recoveryMatricula.value = ''
  recoveryEmail.value = ''
  recoveryNewPassword.value = ''
  recoveryConfirmPassword.value = ''
  recoveryError.value = ''
}

const closeRecoveryDialog = () => {
  forgotPasswordDialog.value = false
}

const submitForgotPassword = async () => {
  if (!isRecoveryValid.value) {
    recoveryError.value = 'A matrícula deve conter exatamente 8 dígitos numéricos.'
    return
  }
  recoveryLoading.value = true
  recoveryError.value = ''
  try {
    const res = await axios.post('http://localhost:8000/auth/forgot-password', {
      card_number: Number(recoveryMatricula.value)
    })
    recoveryEmail.value = res.data.email
    recoveryStep.value = 2
  } catch (err) {
    console.error(err)
    let msg = 'Erro ao enviar email de recuperação.'
    if (err?.response?.data) {
      if (typeof err.response.data.detail === 'string') {
        msg = err.response.data.detail
      } else if (Array.isArray(err.response.data.detail)) {
        msg = err.response.data.detail.map(d => d.msg).join(', ')
      }
    }
    recoveryError.value = msg
  } finally {
    recoveryLoading.value = false
  }
}

const submitResetPassword = async () => {
  recoveryLoading.value = true
  recoveryError.value = ''
  try {
    await axios.post('http://localhost:8000/auth/reset-password', {
      card_number: Number(recoveryMatricula.value),
      new_password: recoveryNewPassword.value
    })
    forgotPasswordDialog.value = false
    alert('Senha redefinida com sucesso! Agora você pode efetuar o login.')
  } catch (err) {
    console.error(err)
    let msg = 'Erro ao redefinir a senha.'
    if (err?.response?.data) {
      if (typeof err.response.data.detail === 'string') {
        msg = err.response.data.detail
      } else if (Array.isArray(err.response.data.detail)) {
        msg = err.response.data.detail.map(d => d.msg).join(', ')
      }
    }
    recoveryError.value = msg
  } finally {
    recoveryLoading.value = false
  }
}
</script>

<template>
  <v-container class="d-flex justify-center mt-10">
    
    <v-card class="pa-6" width="100%" max-width="400" elevation="4" rounded="lg">
      <UfrgsLogo 
        height="100" 
        class="mb-4"
      />

      <v-card-title class="text-center text-h5 font-weight-bold mb-2">
        Login
      </v-card-title>
      
      <v-card-subtitle class="text-center mb-4">
        Portal de Matrícula Auxiliar
      </v-card-subtitle>

      <v-card-text>
        <v-alert v-if="errorMsg" type="error" variant="tonal" class="mb-4" closable @click:close="errorMsg = ''">
          {{ errorMsg }}
        </v-alert>

        <v-form @submit.prevent="handleLogin">
          <v-text-field
            v-model="matricula"
            label="Matrícula (8 dígitos)"
            type="text"
            variant="outlined"
            prepend-inner-icon="mdi-account-card-outline"
            maxLength="8"
            required
            class="mb-2"
            :disabled="loading"
            placeholder="Ex: 11111111"
          ></v-text-field>
          <v-text-field
            v-model="password"
            label="Senha"
            type="password"
            variant="outlined"
            prepend-inner-icon="mdi-lock"
            required
            class="mb-1"
            :disabled="loading"
          ></v-text-field>

          <div class="d-flex justify-end mb-4">
            <a href="#" class="text-caption text-primary text-decoration-none" @click.prevent="openForgotPassword">
              Esqueci minha senha
            </a>
          </div>

          <v-btn 
            type="submit" 
            color="primary" 
            block 
            size="large"
            prepend-icon="mdi-login"
            :loading="loading"
            :disabled="!isFormValid || loading"
          >
            Entrar
          </v-btn>

        </v-form>
      </v-card-text>
    </v-card>

    <!-- Password Recovery Dialog -->
    <v-dialog v-model="forgotPasswordDialog" max-width="450px">
      <v-card class="pa-4">
        <v-card-title class="text-h5 font-weight-bold text-primary">
          Recuperar Senha
        </v-card-title>
        <v-card-text class="pt-4">
          <template v-if="recoveryStep === 1">
            <p class="text-body-2 mb-4">
              Informe a sua matrícula de 8 dígitos para receber as instruções de recuperação em seu e-mail cadastrado.
            </p>
            <v-text-field
              v-model="recoveryMatricula"
              label="Matrícula"
              type="text"
              variant="outlined"
              maxLength="8"
              required
              class="mb-3"
              placeholder="Ex: 11111111"
            ></v-text-field>
            <v-alert v-if="recoveryError" type="error" variant="tonal" class="mb-3">
              {{ recoveryError }}
            </v-alert>
          </template>
          
          <template v-else-if="recoveryStep === 2">
            <v-alert type="success" variant="tonal" class="mb-4" border="start">
              E-mail de recuperação enviado com sucesso para: <strong>{{ recoveryEmail }}</strong>
            </v-alert>
            
            <v-divider class="my-4"></v-divider>
            
            <p class="text-body-2 font-weight-bold mb-3">
              [Simulação] Redefinir Senha Diretamente:
            </p>
            <v-text-field
              v-model="recoveryNewPassword"
              label="Nova Senha"
              type="password"
              variant="outlined"
              required
              class="mb-3"
              placeholder="Mínimo 6 caracteres"
            ></v-text-field>
            <v-text-field
              v-model="recoveryConfirmPassword"
              label="Confirmar Nova Senha"
              type="password"
              variant="outlined"
              required
              class="mb-3"
            ></v-text-field>
            <v-alert v-if="recoveryError" type="error" variant="tonal" class="mb-3">
              {{ recoveryError }}
            </v-alert>
          </template>
        </v-card-text>
        
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="closeRecoveryDialog" :disabled="recoveryLoading">Cancelar</v-btn>
          
          <v-btn
            v-if="recoveryStep === 1"
            color="primary"
            variant="flat"
            :loading="recoveryLoading"
            @click="submitForgotPassword"
            :disabled="recoveryMatricula.length !== 8 || recoveryLoading"
          >
            Enviar E-mail
          </v-btn>
          
          <v-btn
            v-else-if="recoveryStep === 2"
            color="success"
            variant="flat"
            :loading="recoveryLoading"
            @click="submitResetPassword"
            :disabled="recoveryNewPassword.length < 6 || recoveryNewPassword !== recoveryConfirmPassword || recoveryLoading"
          >
            Salvar Nova Senha
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
</style>