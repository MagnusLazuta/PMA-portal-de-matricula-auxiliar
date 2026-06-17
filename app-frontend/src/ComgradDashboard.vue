<script setup>
import { onMounted, ref, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  userId: {
    type: Number,
    required: true
  },
  userRole: {
    type: String,
    default: 'comgrad'
  }
})

const polls = ref([])
const courses = ref([])
const loading = ref(false)
const error = ref('')

const reviewDialog = ref(false)
const viewSlotsDialog = ref(false)
const reportDialog = ref(false)
const selectedPoll = ref(null)
const reviewResponse = ref('')
const reviewStatus = ref('Approved')
const reviewLoading = ref(false)

const openReportDialog = (poll) => {
  selectedPoll.value = poll
  reportDialog.value = true
}

const printReport = () => {
  window.print()
}

const searchQuery = ref('')
const selectedStatus = ref('All')
const sortBy = ref('votes-desc')

const filteredPolls = computed(() => {
  let list = [...polls.value]

  // 1. Filter by text search
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase().trim()
    list = list.filter(poll => {
      const nameStr = getCourseName(poll.course_id).toLowerCase()
      return nameStr.includes(query)
    })
  }

  // 2. Filter by status
  if (selectedStatus.value !== 'All') {
    list = list.filter(poll => poll.status === selectedStatus.value)
  }

  // 3. Sort
  if (sortBy.value === 'votes-desc') {
    list.sort((a, b) => b.vote_count - a.vote_count)
  } else if (sortBy.value === 'votes-asc') {
    list.sort((a, b) => a.vote_count - b.vote_count)
  } else if (sortBy.value === 'deadline') {
    list.sort((a, b) => new Date(a.voting_deadline) - new Date(b.voting_deadline))
  }

  return list
})

const loadCourses = async () => {
  try {
    const response = await axios.get('http://localhost:8000/courses')
    courses.value = response.data
  } catch (err) {
    console.error('Erro ao carregar cursos:', err)
  }
}

const loadPolls = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get('http://localhost:8000/polls/all')
    polls.value = response.data
  } catch (err) {
    console.error('Erro ao buscar enquetes:', err)
    error.value = 'Não foi possível carregar as solicitações da COMGRAD.'
  } finally {
    loading.value = false
  }
}

const getCourseName = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? `${course.code} - ${course.name}` : `Curso ID: ${courseId}`
}

const openViewSlotsDialog = (poll) => {
  selectedPoll.value = poll
  viewSlotsDialog.value = true
}

const openReviewDialog = (poll) => {
  selectedPoll.value = poll
  reviewResponse.value = poll.committee_response || ''
  reviewStatus.value = poll.status === 'Open' ? 'Approved' : poll.status
  reviewDialog.value = true
}

const submitReview = async () => {
  if (!reviewResponse.value.trim()) {
    alert('Por favor, digite uma justificativa ou resposta.')
    return
  }

  reviewLoading.value = true
  try {
    await axios.post(`http://localhost:8000/polls/${selectedPoll.value.id}/review`, {
      committee_response: reviewResponse.value,
      status: reviewStatus.value,
      committee_member_id: props.userId
    })
    reviewDialog.value = false
    await loadPolls()
  } catch (err) {
    console.error('Erro ao registrar parecer:', err)
    alert('Erro ao enviar parecer para a solicitação.')
  } finally {
    reviewLoading.value = false
  }
}

const translateDay = (day) => {
  const mapping = {
    Monday: 'Segunda-feira',
    Tuesday: 'Terça-feira',
    Wednesday: 'Quarta-feira',
    Thursday: 'Quinta-feira',
    Friday: 'Sexta-feira',
    Saturday: 'Sábado',
    Sunday: 'Domingo'
  }
  return mapping[day] || day
}

const getStatusColor = (status) => {
  if (status === 'Open') return 'info'
  if (status === 'Approved') return 'success'
  return 'error'
}

const getStatusLabel = (status) => {
  if (status === 'Open') return 'Aberta'
  if (status === 'Approved') return 'Aprovada'
  return 'Recusada/Fechada'
}

onMounted(() => {
  loadCourses()
  loadPolls()
})
</script>

<template>
  <v-container>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold text-primary">Pareceres da COMGRAD</h1>
        <p class="text-subtitle-1 text-medium-emphasis">Avalie as demandas de turmas abertas por estudantes</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-refresh" @click="loadPolls" :loading="loading">
        Atualizar
      </v-btn>
    </div>

    <v-card elevation="2" rounded="lg">
      <v-card-text>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4">
          {{ error }}
        </v-alert>

        <v-progress-linear v-if="loading" indeterminate class="mb-4" />

        <!-- Filters and Sorting -->
        <v-row class="mb-4">
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="searchQuery"
              label="Buscar por disciplina ou código"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            ></v-text-field>
          </v-col>
          <v-col cols="12" sm="4">
            <v-select
              v-model="selectedStatus"
              :items="[
                { title: 'Todos os status', value: 'All' },
                { title: 'Abertas', value: 'Open' },
                { title: 'Aprovadas', value: 'Approved' },
                { title: 'Recusadas/Fechadas', value: 'Closed' }
              ]"
              label="Status"
              variant="outlined"
              density="compact"
              hide-details
            ></v-select>
          </v-col>
          <v-col cols="12" sm="4">
            <v-select
              v-model="sortBy"
              :items="[
                { title: 'Mais votadas', value: 'votes-desc' },
                { title: 'Menos votadas', value: 'votes-asc' },
                { title: 'Prazo mais próximo', value: 'deadline' }
              ]"
              label="Ordenar por"
              variant="outlined"
              density="compact"
              hide-details
            ></v-select>
          </v-col>
        </v-row>

        <v-table v-if="filteredPolls.length > 0" density="comfortable" class="border rounded">
          <thead>
            <tr>
              <th class="text-left font-weight-bold">Disciplina</th>
              <th class="text-center font-weight-bold">Horário Sugerido</th>
              <th class="text-center font-weight-bold">Votos</th>
              <th class="text-center font-weight-bold">Prazo</th>
              <th class="text-center font-weight-bold">Status</th>
              <th class="text-left font-weight-bold">Parecer Oficial</th>
              <th class="text-center font-weight-bold" style="width: 120px;">Ação</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="poll in filteredPolls" :key="poll.id">
              <td class="font-weight-medium">{{ getCourseName(poll.course_id) }}</td>
              <td class="text-center">
                <div class="d-flex justify-center">
                  <v-btn color="secondary" variant="outlined" size="small" @click="openViewSlotsDialog(poll)">
                    Ver horários
                  </v-btn>
                </div>
              </td>
              <td class="text-center font-weight-bold">
                <v-chip color="primary" size="small" variant="tonal">{{ poll.vote_count }}</v-chip>
              </td>
              <td class="text-center">{{ new Date(poll.voting_deadline).toLocaleDateString() }}</td>
              <td class="text-center">
                <v-chip :color="getStatusColor(poll.status)" size="small" variant="flat">
                   {{ getStatusLabel(poll.status) }}
                </v-chip>
              </td>
              <td class="text-truncate" style="max-width: 200px;" :title="poll.committee_response || 'Nenhum parecer emitido.'">
                {{ poll.committee_response || '—' }}
              </td>
              <td class="text-center">
                <div class="d-flex gap-1 justify-center align-center">
                  <v-btn color="primary" variant="outlined" size="small" @click="openReviewDialog(poll)">
                    {{ poll.status === 'Open' ? 'Emitir Parecer' : 'Editar' }}
                  </v-btn>
                  <v-btn color="info" variant="flat" size="small" prepend-icon="mdi-file-chart" @click="openReportDialog(poll)">
                    Relatório
                  </v-btn>
                </div>
              </td>
            </tr>
          </tbody>
        </v-table>

        <v-alert v-else-if="!loading" type="info" variant="tonal">
          Nenhuma solicitação de enquete encontrada.
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- Dialog to Issue/Edit Review -->
<v-dialog v-model="reviewDialog" max-width="600px">
          <v-card v-if="selectedPoll">
            <v-card-title class="text-h5 font-weight-bold pa-4 bg-primary text-white">
              Registrar Parecer da COMGRAD
            </v-card-title>
            <v-card-text class="pa-6">
              <div class="mb-4">
                <div class="text-subtitle-2 font-weight-bold">Disciplina:</div>
                <div>{{ getCourseName(selectedPoll.course_id) }}</div>
              </div>
              <div class="mb-6">
                <div class="text-subtitle-2 font-weight-bold">Engajamento de Alunos:</div>
                <div><v-chip color="primary" size="small">{{ selectedPoll.vote_count }} votos</v-chip></div>
              </div>

              <v-divider class="mb-6"></v-divider>

              <v-form @submit.prevent="submitReview">
                <v-select
                  v-model="reviewStatus"
                  :items="[
                    { title: 'Aprovada (Approved)', value: 'Approved' },
                    { title: 'Recusada/Fechada (Closed)', value: 'Closed' }
                  ]"
                  label="Decisão"
                  variant="outlined"
                  class="mb-4"
                ></v-select>

                <v-textarea
                  v-model="reviewResponse"
                  label="Justificativa / Parecer Oficial da COMGRAD"
                  variant="outlined"
                  rows="4"
                  required
                  placeholder="Descreva a decisão oficial da comissão com relação a esta oferta de turma..."
                ></v-textarea>
              </v-form>
            </v-card-text>
            <v-card-actions class="pa-4 justify-end">
              <v-btn variant="text" @click="reviewDialog = false">Cancelar</v-btn>
              <v-btn color="primary" variant="flat" :loading="reviewLoading" @click="submitReview" :disabled="!reviewResponse.trim()">
                Salvar Parecer
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <v-dialog v-model="viewSlotsDialog" max-width="500px">
          <v-card v-if="selectedPoll">
            <v-card-title class="text-h5 font-weight-bold pa-4 bg-primary text-white">
              Horários sugeridos
            </v-card-title>
            <v-card-text class="pa-4">
              <div class="mb-3">
                <div class="text-subtitle-2 font-weight-bold">Disciplina:</div>
                <div>{{ getCourseName(selectedPoll.course_id) }}</div>
              </div>
              <div class="mb-3">
                <div class="text-subtitle-2 font-weight-bold">Intervalos sugeridos:</div>
                <div>
                  <v-card
                    v-for="(slot, idx) in selectedPoll.suggested_slots || []"
                    :key="idx"
                    class="pa-3 mb-3"
                    elevation="1"
                    rounded
                  >
                    <div class="text-subtitle-2 font-weight-bold mb-1">Horário {{ idx + 1 }}</div>
                    <div>{{ translateDay(slot.suggested_day_of_week) }}</div>
                    <div>{{ slot.suggested_start_time.substring(0, 5) }} - {{ slot.suggested_end_time.substring(0, 5) }}</div>
                  </v-card>
                </div>
              </div>
            </v-card-text>
            <v-card-actions class="pa-4 justify-end">
              <v-btn variant="text" @click="viewSlotsDialog = false">Fechar</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <!-- Dialog for Individual Poll Report -->
        <v-dialog v-model="reportDialog" max-width="650px">
          <v-card v-if="selectedPoll" class="print-area">
            <v-card-title class="text-h5 font-weight-bold pa-4 bg-primary text-white d-flex align-center justify-space-between no-print">
              <span>Relatório de Demanda</span>
              <v-btn icon="mdi-close" variant="text" color="white" @click="reportDialog = false" density="comfortable"></v-btn>
            </v-card-title>

            <v-card-text class="pa-6">
              <div class="text-center mb-6">
                <h2 class="text-h5 font-weight-bold text-primary">Relatório de Enquete de Oferta</h2>
                <p class="text-caption text-medium-emphasis">Gerado em {{ new Date().toLocaleString('pt-BR') }}</p>
              </div>

              <v-row class="mb-4">
                <v-col cols="6" class="py-1">
                  <span class="text-caption text-medium-emphasis d-block">Disciplina</span>
                  <span class="text-body-1 font-weight-bold">{{ getCourseName(selectedPoll.course_id) }}</span>
                </v-col>
                <v-col cols="6" class="py-1">
                  <span class="text-caption text-medium-emphasis d-block">Identificador (ID)</span>
                  <span class="text-body-1 font-weight-bold">#{{ selectedPoll.id }}</span>
                </v-col>
              </v-row>

              <v-row class="mb-4">
                <v-col cols="6" class="py-1">
                  <span class="text-caption text-medium-emphasis d-block">Status Atual</span>
                  <v-chip :color="getStatusColor(selectedPoll.status)" size="small" variant="flat" class="mt-1">
                    {{ getStatusLabel(selectedPoll.status) }}
                  </v-chip>
                </v-col>
                <v-col cols="6" class="py-1">
                  <span class="text-caption text-medium-emphasis d-block">Engajamento / Votos</span>
                  <v-chip color="primary" size="small" variant="tonal" class="mt-1 font-weight-bold">
                    {{ selectedPoll.vote_count }} votos
                  </v-chip>
                </v-col>
              </v-row>

              <v-divider class="my-4"></v-divider>

              <div class="mb-6">
                <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
                  <v-icon color="secondary" size="20" class="mr-2">mdi-clock-outline</v-icon>
                  Horários Sugeridos pelos Alunos
                </h3>
                <v-card
                  v-for="(slot, idx) in selectedPoll.suggested_slots || []"
                  :key="idx"
                  class="pa-3 mb-2 bg-grey-lighten-4"
                  elevation="0"
                  border
                >
                  <div class="d-flex justify-space-between align-center">
                    <span class="font-weight-medium">{{ translateDay(slot.suggested_day_of_week) }}</span>
                    <span class="text-primary font-weight-bold">
                      {{ slot.suggested_start_time.substring(0, 5) }} - {{ slot.suggested_end_time.substring(0, 5) }}
                    </span>
                  </div>
                </v-card>
              </div>

              <v-divider class="my-4"></v-divider>

              <div class="mb-4">
                <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
                  <v-icon color="success" size="20" class="mr-2">mdi-shield-check</v-icon>
                  Parecer Oficial da COMGRAD
                </h3>
                <div class="bg-grey-lighten-5 pa-4 rounded border text-body-2">
                  <div class="mb-2">
                    <strong>Decisão:</strong> {{ getStatusLabel(selectedPoll.status) }}
                  </div>
                  <div class="mb-2">
                    <strong>Justificativa / Resposta da Comissão:</strong>
                    <p class="mt-1 text-medium-emphasis italic font-weight-medium text-wrap">
                      {{ selectedPoll.committee_response || 'Nenhuma justificativa registrada até o momento.' }}
                    </p>
                  </div>
                  <div v-if="selectedPoll.response_date" class="text-caption text-grey mt-4">
                    Avaliado em: {{ new Date(selectedPoll.response_date).toLocaleString('pt-BR') }}
                    <span v-if="selectedPoll.committee_member_id"> por Membro ID #{{ selectedPoll.committee_member_id }}</span>
                  </div>
                </div>
              </div>
            </v-card-text>

            <v-divider class="no-print"></v-divider>
            <v-card-actions class="pa-4 justify-end no-print">
              <v-btn color="primary" variant="flat" @click="reportDialog = false">
                Fechar
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
  </v-container>
</template>

<style scoped>
.gap-1 {
  gap: 4px;
}
@media print {
  body * {
    visibility: hidden;
  }
  .print-area, .print-area * {
    visibility: visible;
  }
  .print-area {
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
  }
  .no-print {
    display: none !important;
  }
}
</style>
