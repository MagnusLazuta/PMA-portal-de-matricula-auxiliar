<script setup>
import { onMounted, ref, computed } from 'vue'
import axios from 'axios'

const polls = ref([])
const courses = ref([])
const loading = ref(false)
const error = ref('')

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const [pollsRes, coursesRes] = await Promise.all([
      axios.get('http://localhost:8000/polls/all'),
      axios.get('http://localhost:8000/courses')
    ])
    polls.value = pollsRes.data || []
    courses.value = coursesRes.data || []
  } catch (err) {
    console.error('Erro ao carregar dados do relatório:', err)
    error.value = 'Erro ao carregar os dados das enquetes.'
  } finally {
    loading.value = false
  }
}

const getCourseDisplay = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? `${course.code} - ${course.name}` : `ID: ${courseId}`
}

// 1. Aggregated Metrics
const totalPolls = computed(() => polls.value.length)

const totalVotes = computed(() => {
  return polls.value.reduce((sum, p) => sum + (p.vote_count || 0), 0)
})

const averageVotes = computed(() => {
  if (totalPolls.value === 0) return 0
  return Number((totalVotes.value / totalPolls.value).toFixed(1))
})

const approvalRate = computed(() => {
  const decided = polls.value.filter(p => p.status === 'Approved' || p.status === 'Closed')
  if (decided.length === 0) return '0.0%'
  const approved = decided.filter(p => p.status === 'Approved').length
  return ((approved / decided.length) * 100).toFixed(1) + '%'
})

// 2. Status Distribution counts
const statusCounts = computed(() => {
  const counts = { open: 0, approved: 0, closed: 0 }
  polls.value.forEach(p => {
    if (p.status === 'Open') counts.open++
    else if (p.status === 'Approved') counts.approved++
    else if (p.status === 'Closed') counts.closed++
  })
  return counts
})

// 3. Top Most Demanded Courses (Grouped by Course)
const topDemandedCourses = computed(() => {
  const groups = {}
  polls.value.forEach(p => {
    if (!groups[p.course_id]) {
      groups[p.course_id] = {
        course_id: p.course_id,
        poll_count: 0,
        total_votes: 0,
        polls: []
      }
    }
    groups[p.course_id].poll_count++
    groups[p.course_id].total_votes += (p.vote_count || 0)
    groups[p.course_id].polls.push(p)
  })

  const list = Object.values(groups)
  // Sort descending by votes
  list.sort((a, b) => b.total_votes - a.total_votes)
  
  // Return top 5
  return list.slice(0, 5)
})

// Max votes among top courses for relative progress calculation
const maxVotesAmongTop = computed(() => {
  if (topDemandedCourses.value.length === 0) return 1
  return Math.max(...topDemandedCourses.value.map(c => c.total_votes), 1)
})

const printReport = () => {
  window.print()
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <v-container class="print-area">
    <!-- Header -->
    <div class="d-flex justify-space-between align-center mb-6 no-print">
      <div>
        <h1 class="text-h4 font-weight-bold text-primary">Relatório Consolidado de Enquetes</h1>
        <p class="text-subtitle-1 text-medium-emphasis">Visão analítica e consolidada de demandas de abertura de turmas</p>
      </div>
      <div class="d-flex gap-2">
        <v-btn color="secondary" variant="outlined" prepend-icon="mdi-printer" @click="printReport" :disabled="loading">
          Imprimir Relatório
        </v-btn>
        <v-btn color="primary" prepend-icon="mdi-refresh" @click="loadData" :loading="loading">
          Atualizar
        </v-btn>
      </div>
    </div>

    <!-- Print Title (Only visible when printing) -->
    <div class="print-only-title text-center mb-6">
      <h1 class="text-h3 font-weight-bold text-primary">Relatório Consolidado de Enquetes (UFRGS)</h1>
      <p class="text-subtitle-1">Análise de Transações e Demandas de Abertura de Turmas pelos Alunos</p>
      <p class="text-caption text-medium-emphasis">Gerado em: {{ new Date().toLocaleString('pt-BR') }}</p>
      <v-divider class="my-4"></v-divider>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-6">
      {{ error }}
    </v-alert>

    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-6"></v-progress-linear>

    <template v-else>
      <!-- Cards de Métricas -->
      <v-row class="mb-6">
        <v-col cols="12" sm="6" md="3">
          <v-card class="pa-4 bg-blue-lighten-5 text-blue-darken-4 rounded-xl shadow-premium h-100" elevation="2">
            <div class="text-subtitle-2 text-uppercase font-weight-medium">Total de Enquetes</div>
            <div class="text-h3 font-weight-bold mt-2">{{ totalPolls }}</div>
            <div class="text-caption mt-1 text-blue-darken-2">Demandas abertas no total</div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card class="pa-4 bg-purple-lighten-5 text-purple-darken-4 rounded-xl shadow-premium h-100" elevation="2">
            <div class="text-subtitle-2 text-uppercase font-weight-medium">Votos Registrados</div>
            <div class="text-h3 font-weight-bold mt-2">{{ totalVotes }}</div>
            <div class="text-caption mt-1 text-purple-darken-2">Total de votos coletados</div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card class="pa-4 bg-orange-lighten-5 text-orange-darken-4 rounded-xl shadow-premium h-100" elevation="2">
            <div class="text-subtitle-2 text-uppercase font-weight-medium">Média de Engajamento</div>
            <div class="text-h3 font-weight-bold mt-2">{{ averageVotes }}</div>
            <div class="text-caption mt-1 text-orange-darken-2">Média de votos por enquete</div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card class="pa-4 bg-green-lighten-5 text-green-darken-4 rounded-xl shadow-premium h-100" elevation="2">
            <div class="text-subtitle-2 text-uppercase font-weight-medium">Taxa de Aprovação</div>
            <div class="text-h3 font-weight-bold mt-2">{{ approvalRate }}</div>
            <div class="text-caption mt-1 text-green-darken-2">Decisões favoráveis da COMGRAD</div>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mb-6">
        <!-- Distribuição de Status -->
        <v-col cols="12" md="4">
          <v-card class="pa-6 rounded-xl h-100 border-card" elevation="1">
            <v-card-title class="text-subtitle-1 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
              <v-icon color="primary" class="mr-2">mdi-chart-pie</v-icon>
              Distribuição de Status
            </v-card-title>
            
            <v-card-text class="px-0">
              <div class="mb-4">
                <div class="d-flex justify-space-between text-body-2 mb-1">
                  <span>Enquetes Abertas (Votação)</span>
                  <span class="font-weight-bold">{{ statusCounts.open }}</span>
                </div>
                <v-progress-linear
                  :model-value="totalPolls ? (statusCounts.open / totalPolls) * 100 : 0"
                  color="info"
                  height="8"
                  rounded
                ></v-progress-linear>
              </div>

              <div class="mb-4">
                <div class="d-flex justify-space-between text-body-2 mb-1">
                  <span>Aprovadas pela COMGRAD</span>
                  <span class="font-weight-bold">{{ statusCounts.approved }}</span>
                </div>
                <v-progress-linear
                  :model-value="totalPolls ? (statusCounts.approved / totalPolls) * 100 : 0"
                  color="success"
                  height="8"
                  rounded
                ></v-progress-linear>
              </div>

              <div>
                <div class="d-flex justify-space-between text-body-2 mb-1">
                  <span>Recusadas / Fechadas</span>
                  <span class="font-weight-bold">{{ statusCounts.closed }}</span>
                </div>
                <v-progress-linear
                  :model-value="totalPolls ? (statusCounts.closed / totalPolls) * 100 : 0"
                  color="error"
                  height="8"
                  rounded
                ></v-progress-linear>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Top Disciplinas Mais Demandadas -->
        <v-col cols="12" md="8">
          <v-card class="pa-6 rounded-xl h-100 shadow-premium" elevation="2">
            <v-card-title class="text-subtitle-1 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
              <v-icon color="primary" class="mr-2">mdi-fire</v-icon>
              Destaque: Top 5 Disciplinas Mais Demandadas
            </v-card-title>
            
            <v-card-text class="px-0">
              <v-table v-if="topDemandedCourses.length > 0" density="comfortable">
                <thead>
                  <tr>
                    <th class="text-left font-weight-bold">Disciplina</th>
                    <th class="text-center font-weight-bold" style="width: 120px;">Qtd. Enquetes</th>
                    <th class="text-center font-weight-bold" style="width: 120px;">Votos Totais</th>
                    <th class="text-left font-weight-bold" style="width: 200px;">Nível de Engajamento</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in topDemandedCourses" :key="item.course_id">
                    <td class="font-weight-bold text-truncate" style="max-width: 250px;">
                      {{ idx + 1 }}. {{ getCourseDisplay(item.course_id) }}
                    </td>
                    <td class="text-center">{{ item.poll_count }}</td>
                    <td class="text-center font-weight-bold">
                      <v-chip color="primary" size="small" variant="tonal">{{ item.total_votes }}</v-chip>
                    </td>
                    <td>
                      <v-progress-linear
                        :model-value="(item.total_votes / maxVotesAmongTop) * 100"
                        color="teal"
                        height="6"
                        rounded
                      ></v-progress-linear>
                    </td>
                  </tr>
                </tbody>
              </v-table>
              <div v-else class="text-center py-6 text-caption text-medium-emphasis italic">
                Nenhum dado de demanda registrado no momento.
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<style scoped>
.gap-2 {
  gap: 8px;
}
.shadow-premium {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
}
.border-card {
  border: 1px solid rgba(var(--v-border-color), 0.12) !important;
}
.print-only-title {
  display: none;
}

@media print {
  .no-print {
    display: none !important;
  }
  .print-only-title {
    display: block !important;
  }
  .print-area {
    width: 100%;
    max-width: 100%;
    padding: 0;
    margin: 0;
  }
}
</style>
