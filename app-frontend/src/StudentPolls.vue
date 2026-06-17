<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  studentId: {
    type: Number,
    required: true
  }
})

const polls = ref([])
const courses = ref([])
const eligibleCourses = ref([])
const loading = ref(false)
const creating = ref(false)
const error = ref('')
const creationError = ref('')
const selectedCourseId = ref(null)
const timeSlots = [
  { label: '08:30 - 10:10', start: '08:30', end: '10:10' },
  { label: '10:30 - 12:10', start: '10:30', end: '12:10' },
  { label: '13:30 - 15:10', start: '13:30', end: '15:10' },
  { label: '15:30 - 17:10', start: '15:30', end: '17:10' },
  { label: '18:30 - 20:10', start: '18:30', end: '20:10' },
  { label: '20:30 - 22:10', start: '20:30', end: '22:10' }
]
const selectedTimeSlots = ref([])
const responseDialog = ref(false)
const slotsDialog = ref(false)
const selectedPoll = ref(null)

const dayOptions = [
  { label: 'Segunda-feira', value: 'Monday' },
  { label: 'Terça-feira', value: 'Tuesday' },
  { label: 'Quarta-feira', value: 'Wednesday' },
  { label: 'Quinta-feira', value: 'Thursday' },
  { label: 'Sexta-feira', value: 'Friday' }
]

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
    const response = await axios.get(`http://localhost:8000/polls?student_id=${props.studentId}`)
    polls.value = response.data
  } catch (err) {
    console.error('Erro ao buscar enquetes:', err)
    error.value = 'Não foi possível carregar as enquetes.'
  } finally {
    loading.value = false
  }
}

const loadEligibleCourses = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/students/${props.studentId}/eligible-courses`)
    eligibleCourses.value = response.data.map(course => ({
      ...course,
      credits: Number(course.credits),
      displayName: `${course.code} - ${course.name}`
    }))
  } catch (err) {
    console.error('Erro ao carregar disciplinas elegíveis:', err)
  }
}

const selectedCourse = computed(() => {
  return eligibleCourses.value.find(c => Number(c.id) === Number(selectedCourseId.value))
})

const expectedSlotCount = computed(() => {
  const credits = selectedCourse.value ? Number(selectedCourse.value.credits) : NaN
  return !isNaN(credits) ? Math.max(1, Math.floor(credits / 2)) : 1
})

const ensureSelectedTimeSlots = () => {
  const count = expectedSlotCount.value
  if (!selectedCourse.value) {
    selectedTimeSlots.value = []
    return
  }
  while (selectedTimeSlots.value.length < count) {
    selectedTimeSlots.value.push({ day: 'Monday', slot: null })
  }
  if (selectedTimeSlots.value.length > count) {
    selectedTimeSlots.value.splice(count)
  }
}

watch([selectedCourseId, eligibleCourses], () => {
  ensureSelectedTimeSlots()
}, { immediate: true })

const eligibleCourseIds = computed(() => new Set(eligibleCourses.value.map(c => c.id)))

const visiblePolls = computed(() => {
  if (!eligibleCourseIds.value.size) {
    return []
  }
  return polls.value.filter(poll => eligibleCourseIds.value.has(poll.course_id))
})

const createPoll = async () => {
  creationError.value = ''
  if (!selectedCourseId.value) {
    creationError.value = 'Selecione uma disciplina elegível.'
    return
  }
  // validate selectedTimeSlots according to course credits
  const course = selectedCourse.value
  const expected = expectedSlotCount.value
  if (!selectedTimeSlots.value || selectedTimeSlots.value.length !== expected) {
    creationError.value = `Selecione ${expected} intervalo(s) de horário proposto(s).`
    return
  }
  for (const s of selectedTimeSlots.value) {
    if (!s || !s.slot) {
      creationError.value = 'Preencha todos os intervalos de horário.'
      return
    }
  }

  const seenSlots = new Set()
  for (const s of selectedTimeSlots.value) {
    const key = `${s.day}-${s.slot.start}-${s.slot.end}`
    if (seenSlots.has(key)) {
      creationError.value = 'Não é permitido selecionar o mesmo dia e horário para múltiplos intervalos.'
      return
    }
    seenSlots.add(key)
  }

  creating.value = true
  try {
    // voting_deadline is always 14 days from now
    const votingDeadlineIso = new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString()
    const suggested_slots_payload = selectedTimeSlots.value.map(s => ({
      suggested_day_of_week: s.day,
      suggested_start_time: s.slot.start,
      suggested_end_time: s.slot.end
    }))
    await axios.post('http://localhost:8000/polls', {
      creator_student_id: props.studentId,
      course_id: selectedCourseId.value,
      suggested_slots: suggested_slots_payload,
      voting_deadline: votingDeadlineIso
    })
    selectedCourseId.value = null
    selectedTimeSlots.value = []
    await loadPolls()
    await loadEligibleCourses()
  } catch (err) {
    console.error('Erro ao criar enquete:', err)
    creationError.value = err?.response?.data?.detail || 'Não foi possível criar a enquete.'
  } finally {
    creating.value = false
  }
}

const getCourseName = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? `${course.code} - ${course.name}` : `Curso ID: ${courseId}`
}

const vote = async (poll) => {
  try {
    await axios.post(`http://localhost:8000/polls/${poll.id}/votes`, { student_id: props.studentId })
    await loadPolls()
  } catch (err) {
    console.error('Erro ao registrar voto:', err)
    const detail = err?.response?.data || err?.message || String(err)
    if (err?.response?.status === 409) {
      alert('Você já votou nesta enquete.')
    } else if (err?.response?.status === 400) {
      alert(detail.detail || 'Votação não permitida.')
    } else {
      alert('Erro ao enviar voto.')
    }
  }
}

const removeVote = async (poll) => {
  try {
    await axios.delete(`http://localhost:8000/polls/${poll.id}/votes/${props.studentId}`)
    await loadPolls()
  } catch (err) {
    console.error('Erro ao remover voto:', err)
    if (err?.response?.status === 404) {
      alert('Você não possui voto registrado nesta enquete.')
    } else {
      alert('Erro ao remover voto.')
    }
  }
}

const openResponseDialog = (poll) => {
  selectedPoll.value = poll
  responseDialog.value = true
}

const openSlotsDialog = (poll) => {
  selectedPoll.value = poll
  slotsDialog.value = true
}

const translateDay = (day) => {
  const mapping = {
    Monday: 'Segunda-feira',
    Tuesday: 'Terça-feira',
    Wednesday: 'Quarta-feira',
    Thursday: 'Quinta-feira',
    Friday: 'Sexta-feira'
  }
  return mapping[day] || day
}

onMounted(() => {
  loadCourses()
  loadPolls()
  loadEligibleCourses()
})
</script>

<template>
  <v-container>
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold text-primary">Enquetes</h1>
        <p class="text-subtitle-1 text-medium-emphasis">Participe das enquetes abertas e apoie a criação de turmas</p>
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

        <v-card class="mb-6" outlined>
          <v-card-title class="font-weight-bold">Criar nova enquete</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-select
                  v-model="selectedCourseId"
                  :items="eligibleCourses"
                  item-title="displayName"
                  item-value="id"
                  label="Disciplina elegível"
                  dense
                  hide-details="auto"
                />
              </v-col>
            </v-row>
            <template v-if="selectedTimeSlots.length">
              <template v-for="(s, idx) in selectedTimeSlots" :key="idx">
                <v-row align="center" class="mt-4">
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="selectedTimeSlots[idx].day"
                      :items="dayOptions"
                      item-title="label"
                      item-value="value"
                      :label="`Dia proposto ${idx + 1}`"
                      dense
                      hide-details="auto"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="selectedTimeSlots[idx].slot"
                      :items="timeSlots"
                      item-title="label"
                      :return-object="true"
                      :label="`Intervalo de horário ${idx + 1}`"
                      dense
                      hide-details="auto"
                    />
                  </v-col>
                </v-row>
              </template>
            </template>
            <v-row align="center" class="mt-4">
              <v-col cols="12" md="4">
                <v-btn color="primary" @click="createPoll" :loading="creating" :disabled="creating || !eligibleCourses.length">
                  Criar enquete
                </v-btn>
              </v-col>
              <v-col cols="12" md="8">
                <v-alert v-if="creationError" type="error" variant="tonal" class="mb-0">
                  {{ creationError }}
                </v-alert>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <v-table v-if="visiblePolls.length > 0" density="comfortable" class="border rounded">
          <thead>
            <tr>
              <th class="text-left font-weight-bold">Disciplina</th>
              <th class="text-center font-weight-bold">Horário Sugerido</th>
              <th class="text-center font-weight-bold">Votos</th>
              <th class="text-center font-weight-bold">Prazo</th>
              <th class="text-center font-weight-bold">Status</th>
              <th class="text-center font-weight-bold" style="width: 160px;">Ação</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="poll in visiblePolls" :key="poll.id">
              <td class="font-weight-medium">{{ getCourseName(poll.course_id) }}</td>
              <td class="text-center">
                <div class="d-flex justify-center">
                  <v-btn color="secondary" variant="outlined" size="small" @click="openSlotsDialog(poll)">
                    Ver horários
                  </v-btn>
                </div>
              </td>
              <td class="text-center font-weight-bold">
                <v-chip color="primary" size="small" variant="tonal">{{ poll.vote_count }}</v-chip>
              </td>
              <td class="text-center">{{ new Date(poll.voting_deadline).toLocaleDateString() }}</td>
              <td class="text-center">
                <v-chip :color="poll.status === 'Open' ? 'info' : (poll.status === 'Approved' ? 'success' : 'error')" size="small" variant="flat">
                  {{ poll.status === 'Open' ? 'Aberta' : (poll.status === 'Approved' ? 'Aprovada' : 'Fechada') }}
                </v-chip>
              </td>
              <td class="text-center">
                <template v-if="poll.status === 'Open'">
                  <v-btn
                    v-if="!poll.voted_student_ids || !poll.voted_student_ids.includes(props.studentId)"
                    color="primary"
                    variant="outlined"
                    size="small"
                    @click="vote(poll)"
                  >
                    Votar
                  </v-btn>
                  <v-btn
                    v-else
                    color="error"
                    variant="text"
                    size="small"
                    @click="removeVote(poll)"
                  >
                    Retirar
                  </v-btn>
                </template>
                <template v-else>
                  <v-btn
                    v-if="poll.committee_response"
                    color="primary"
                    variant="outlined"
                    size="small"
                    @click="openResponseDialog(poll)"
                  >
                    Ver parecer
                  </v-btn>
                </template>
              </td>
            </tr>
          </tbody>
        </v-table>

        <v-alert v-if="!visiblePolls.length && !loading" type="info" variant="tonal">
          Não há enquetes disponíveis para você no momento.
        </v-alert>

        <v-dialog v-model="responseDialog" max-width="500px">
          <v-card v-if="selectedPoll">
            <v-card-title class="text-h5 font-weight-bold pa-4 bg-primary text-white">
              Parecer da COMGRAD
            </v-card-title>
            <v-card-text class="pa-4">
              <div class="mb-3">
                <div class="text-subtitle-2 font-weight-bold">Disciplina:</div>
                <div>{{ getCourseName(selectedPoll.course_id) }}</div>
              </div>
              <div class="mb-3">
                <div class="text-subtitle-2 font-weight-bold">Status:</div>
                <div>{{ selectedPoll.status === 'Approved' ? 'Aprovada' : 'Fechada' }}</div>
              </div>
              <div class="mb-3" v-if="selectedPoll.committee_response">
                <div class="text-subtitle-2 font-weight-bold">Parecer oficial:</div>
                <div>{{ selectedPoll.committee_response }}</div>
              </div>
              <v-divider class="my-4" />
            </v-card-text>
            <v-card-actions class="pa-4 justify-end">
              <v-btn variant="text" @click="responseDialog = false">Fechar</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <v-dialog v-model="slotsDialog" max-width="500px">
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
              <v-divider class="my-4" />
            </v-card-text>
            <v-card-actions class="pa-4 justify-end">
              <v-btn variant="text" @click="slotsDialog = false">Fechar</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<style scoped>
</style>
