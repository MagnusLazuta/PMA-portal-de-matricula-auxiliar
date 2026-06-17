<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: {
    type: Object,
    default: () => ({ name: 'Usuário', role: 'student' })
  }
})

const roleLabel = computed(() => {
  const mapping = {
    admin: 'Administrador',
    comgrad: 'Membro da COMGRAD',
    student: 'Estudante',
    comgrad_admin: 'Membro da COMGRAD e Administrador'
  }
  return mapping[props.user?.role] || 'Usuário'
})
</script>

<template>
  <div>
    <h1 class="text-h4 font-weight-bold text-primary mb-4">
      Painel Principal
    </h1>

    <v-divider class="mb-6"></v-divider>

    <v-card class="pa-6" elevation="2" rounded="lg">
      <v-row align="center">
        <v-col cols="12" md="8">
          <h2 class="text-h5 mb-2">Bem-vindo, {{ user?.name }}!</h2>
          <div class="text-subtitle-1 text-primary font-weight-medium mb-4">
            Papel: {{ roleLabel }}
          </div>

          <p class="text-body-1 text-medium-emphasis mb-4">
            Este é o portal auxiliar de matrícula da UFRGS para os cursos do INF (Ciência da Computação e Engenharia de Computação).
          </p>

          <!-- Role-based descriptions -->
          <div v-if="user?.role === 'student'">
            <v-alert type="info" variant="tonal" border="start">
              Como <strong>Estudante</strong>, você pode acessar a seção <strong>Gerar Grade</strong> na barra lateral para indicar suas restrições e interesses de horários e professores para gerar sua grade letiva otimizada de forma automatizada.
            </v-alert>
          </div>

          <div v-if="user?.role === 'comgrad' || user?.role === 'admin' || user?.role === 'comgrad_admin'" class="mb-4">
            <v-alert type="success" variant="tonal" border="start">
              Como <strong>Membro da COMGRAD</strong>, você pode acessar a seção <strong>Pareceres de Grade</strong> na barra lateral para analisar enquetes de interesse de turmas criadas por alunos e registrar decisões oficiais.
            </v-alert>
          </div>

          <div v-if="user?.role === 'admin' || user?.role === 'comgrad_admin'">
            <v-alert type="warning" variant="tonal" border="start">
              Como <strong>Administrador</strong>, você tem acesso completo ao <strong>Painel Admin</strong> para monitorar as estatísticas gerais do sistema, redefinir ou carregar dados globais de disciplinas e turmas no banco.
            </v-alert>
          </div>
        </v-col>
        
        <v-col cols="12" md="4" class="text-center d-none d-md-block">
          <v-icon size="128" color="primary">mdi-school-outline</v-icon>
        </v-col>
      </v-row>
    </v-card>
  </div>
</template>

<style scoped>
</style>