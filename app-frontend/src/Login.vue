<script setup>
import { ref } from 'vue'

const emit = defineEmits(['login'])

const email = ref('')
const password = ref('')

const handleLogin = () => {
  if (email.value !== '' && password.value !== '') {
    emit('login')
  } else {
    alert('Por favor, preencha todos os campos.')
  }
}
</script>

<template>
  <v-container class="d-flex justify-center mt-10">
    
    <v-card class="pa-6" width="100%" max-width="400" elevation="4" rounded="lg">
      <v-img 
        src="/ufrgs.png" 
        alt="Logo UFRGS" 
        height="100" 
        class="mb-4"
      ></v-img>

      <v-card-title class="text-center text-h5 font-weight-bold mb-4">
        Login
      </v-card-title>

      <v-card-text>
        <v-form @submit.prevent="handleLogin">
          <v-text-field
            v-model="email"
            label="E-mail"
            type="email"
            variant="outlined"
            prepend-inner-icon="mdi-email"
            required
            class="mb-2"
          ></v-text-field>
          <v-text-field
            v-model="password"
            label="Senha"
            type="password"
            variant="outlined"
            prepend-inner-icon="mdi-lock"
            required
            class="mb-4"
          ></v-text-field>

          <v-btn 
            type="submit" 
            color="primary" 
            block 
            size="large"
            prepend-icon="mdi-login"
          >
            Entrar
          </v-btn>

        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<style scoped>
</style>