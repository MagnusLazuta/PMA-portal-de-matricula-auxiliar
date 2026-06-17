<script setup>
import { onMounted, ref } from 'vue'
import axios from 'axios'

const stats = ref({
  courses: 0,
  sections: 0,
  students: 0,
  restrictions: 0,
  polls: 0,
  approvedPolls: 0,
  deniedPolls: 0,
})

const loading = ref(false)

const loadStats = async () => {
  loading.value = true
  try {
    const [coursesRes, sectionsRes, studentsRes, restrictionsRes, pollSummaryRes] = await Promise.all([
      axios.get('http://localhost:8000/courses'),
      axios.get('http://localhost:8000/sections/'),
      axios.get('http://localhost:8000/students/'),
      axios.get('http://localhost:8000/restrictions/'),
      axios.get('http://localhost:8000/polls/summary')
    ])
    stats.value = {
      courses: Array.isArray(coursesRes.data) ? coursesRes.data.length : 0,
      sections: Array.isArray(sectionsRes.data) ? sectionsRes.data.length : 0,
      students: Array.isArray(studentsRes.data) ? studentsRes.data.length : 0,
      restrictions: Array.isArray(restrictionsRes.data) ? restrictionsRes.data.length : 0,
      polls: pollSummaryRes.data.total_polls || 0,
      approvedPolls: pollSummaryRes.data.approved_polls || 0,
      deniedPolls: pollSummaryRes.data.denied_polls || 0,
    }
  } catch (err) {
    console.error('Erro ao buscar estatísticas:', err)
  } finally {
    loading.value = false
  }
}



onMounted(() => {
  loadStats()
})
</script>

<template>
  <v-container>
    <div class="mb-6">
      <h1 class="text-h4 font-weight-bold text-primary">Painel do Administrador</h1>
      <p class="text-subtitle-1 text-medium-emphasis">Gerenciamento de dados e redefinição do sistema</p>
    </div>

    <!-- Statistics Indicators -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 bg-blue-lighten-5 text-blue-darken-4 rounded-lg" elevation="2">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-subtitle-2 text-uppercase font-weight-medium">Disciplinas</div>
              <div class="text-h3 font-weight-bold mt-2">{{ stats.courses }}</div>
            </div>
            <v-icon size="64" color="blue">mdi-book-open-page-variant</v-icon>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 bg-green-lighten-5 text-green-darken-4 rounded-lg" elevation="2">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-subtitle-2 text-uppercase font-weight-medium">Turmas Ofertadas</div>
              <div class="text-h3 font-weight-bold mt-2">{{ stats.sections }}</div>
            </div>
            <v-icon size="64" color="green">mdi-google-classroom</v-icon>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 bg-purple-lighten-5 text-purple-darken-4 rounded-lg" elevation="2">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-subtitle-2 text-uppercase font-weight-medium">Alunos</div>
              <div class="text-h3 font-weight-bold mt-2">{{ stats.students }}</div>
            </div>
            <v-icon size="64" color="purple">mdi-school</v-icon>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 bg-orange-lighten-5 text-orange-darken-4 rounded-lg" elevation="2">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-subtitle-2 text-uppercase font-weight-medium">Restrições Criadas</div>
              <div class="text-h3 font-weight-bold mt-2">{{ stats.restrictions }}</div>
            </div>
            <v-icon size="64" color="orange">mdi-clock-alert</v-icon>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 bg-teal-lighten-5 text-teal-darken-4 rounded-lg" elevation="2">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-subtitle-2 text-uppercase font-weight-medium">Total de Enquetes</div>
              <div class="text-h3 font-weight-bold mt-2">{{ stats.polls }}</div>
            </div>
            <v-icon size="64" color="teal">mdi-poll</v-icon>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 bg-green-lighten-5 text-green-darken-4 rounded-lg" elevation="2">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-subtitle-2 text-uppercase font-weight-medium">Enquetes Aprovadas</div>
              <div class="text-h3 font-weight-bold mt-2">{{ stats.approvedPolls }}</div>
            </div>
            <v-icon size="64" color="green">mdi-check-circle</v-icon>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 bg-red-lighten-5 text-red-darken-4 rounded-lg" elevation="2">
          <div class="d-flex align-center justify-space-between">
            <div>
              <div class="text-subtitle-2 text-uppercase font-weight-medium">Enquetes Recusadas</div>
              <div class="text-h3 font-weight-bold mt-2">{{ stats.deniedPolls }}</div>
            </div>
            <v-icon size="64" color="red">mdi-close-circle</v-icon>
          </div>
        </v-card>
      </v-col>
    </v-row>


  </v-container>
</template>

<style scoped>
.gap-3 {
  gap: 12px;
}
</style>
