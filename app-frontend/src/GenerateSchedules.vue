<template>
  <v-container>
    <v-card class="mx-auto rounded-xl" elevation="4">
      <v-card-title class="text-h5 font-weight-bold mt-4">
        Escolha suas disciplinas
      </v-card-title>
      
      <v-card-text>
        <!-- Semester selector on top -->
        <v-row class="mb-4">
          <v-col cols="12" md="6">
            <v-select
              v-model="selectedSemester"
              :items="semestersList"
              label="Selecione o Semestre Letivo"
              variant="outlined"
              placeholder="Selecione o semestre..."
              hide-details
            ></v-select>
          </v-col>
        </v-row>

        <v-divider class="mb-6"></v-divider>

        <v-form v-if="selectedSemester" @submit.prevent="addCourse" class="d-flex flex-column gap-4">
          <v-row>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="currentForm.course"
                :items="filteredCourses"
                item-title="name"
                return-object
                label="Selecione a disciplina"
                variant="outlined"
                placeholder="Digite para buscar..."
                hide-details
              ></v-autocomplete>
            </v-col>
          </v-row>

          <v-row v-if="currentForm.course">
            <v-col cols="12" md="4">
              <v-select
                v-model="currentForm.importanceLevel"
                :items="[
                  { title: 'Baixa', value: 'low' },
                  { title: 'Média', value: 'medium' },
                  { title: 'Alta', value: 'high' }
                ]"
                label="Prioridade da Disciplina"
                variant="outlined"
                hide-details
              ></v-select>
            </v-col>
            <v-col cols="12" md="5">
              <v-combobox
                v-model="currentForm.preferredProfessor"
                :items="availableFormProfessors"
                label="Professor Preferido (opcional)"
                variant="outlined"
                placeholder="Selecione ou digite..."
                hide-details
              ></v-combobox>
            </v-col>
            <v-col cols="12" md="3" v-if="currentForm.preferredProfessor">
              <v-select
                v-model="currentForm.preferenceOrder"
                :items="[1, 2, 3]"
                label="Ordem de Preferência"
                variant="outlined"
                hide-details
              ></v-select>
            </v-col>
          </v-row>

          <v-btn 
            type="submit" 
            color="primary" 
            class="mt-4 align-self-end"
            :disabled="!currentForm.course"
          >
            Adicionar à Lista
          </v-btn>
        </v-form>

        <v-divider class="my-6"></v-divider>

        <div v-if="interestList.length > 0">
          <h3 class="text-h6 mb-3">Disciplinas selecionadas</h3>
          
          <v-table density="comfortable" class="border rounded">
            <thead>
              <tr>
                <th class="text-left">Disciplina</th>
                <th class="text-left">Prioridade</th>
                <th class="text-left">Prof. Preferido</th>
                <th class="text-center" style="width: 180px;">Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in interestList" :key="index">
                <td class="font-weight-medium">{{ item.course?.name }} ({{ item.course?.code }})</td>
                <td>{{ getCoursePriorityLabel(item.course?.id) }}</td>
                <td>{{ getCourseProfessorLabel(item.course?.id) }}</td>
                <td class="text-center d-flex justify-center align-center gap-2">
                  <v-btn 
                    color="primary" 
                    variant="text" 
                    size="small"
                    @click="openEditDialog(item)"
                  >
                    Editar
                  </v-btn>
                  <v-btn 
                    color="error" 
                    variant="text" 
                    size="small"
                    @click="removeFromList(index)"
                  >
                    Remover
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
          
          <v-row class="mt-6 align-center">
            <v-col cols="12" class="d-flex justify-end">
              <v-btn 
                color="primary" 
                variant="elevated"
                size="large"
                @click="emit('go-generate-schedule', selectedSemester)"
              >
                Gerar grade de horários
              </v-btn>
            </v-col>
          </v-row>
        </div>
        
        <v-alert
          v-else
          type="info"
          variant="tonal"
          class="mt-4"
        >
          Sua lista está vazia. Adicione disciplinas no formulário acima.
        </v-alert>
      </v-card-text>
    </v-card>

    <v-card class="mt-6 rounded-xl">
      <v-card-title class="text-h5 font-weight-bold mt-4">
        Informar Restrições de Horário (opcional)
      </v-card-title>

      <v-card-text>
        <v-form @submit.prevent="addRestriction" class="d-flex flex-column gap-4">
          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="restrictionForm.type"
                :items="[
                  { title: 'Bloqueio de Horário (Restrição Rígida)', value: 'hard_block' },
                  { title: 'Janela Preferida (Horário Preferido)', value: 'preferred_window' }
                ]"
                label="Tipo de Restrição Rígida/Horário"
                variant="outlined"
                hide-details
              ></v-select>
            </v-col>
          </v-row>

          <v-row v-if="restrictionForm.type === 'hard_block' || restrictionForm.type === 'preferred_window'">
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="restrictionForm.day"
                :items="translatedDaysList"
                item-title="title"
                item-value="value"
                label="Selecione os dias da semana"
                variant="outlined"
                multiple
                chips
                closable-chips
                placeholder="Selecione um ou mais dias..."
                hide-details
              ></v-autocomplete>
            </v-col>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="restrictionForm.startTime"
                label="Horário início"
                variant="outlined"
                prepend-inner-icon="mdi-clock-time-four-outline"
                hide-details
              >    
                <v-menu
                  v-model="showStartTimeMenu"
                  :close-on-content-click="false"
                  activator="parent"
                  min-width="0"
                >
                  <v-time-picker 
                    v-model="restrictionForm.startTime"
                    format="24hr"
                  ></v-time-picker>
                </v-menu>
              </v-text-field>
            </v-col>

            <v-col cols="12" md="3">
              <v-text-field
                v-model="restrictionForm.endTime"
                label="Horário fim"
                variant="outlined"
                prepend-inner-icon="mdi-clock-time-four-outline"
                hide-details
              >    
                <v-menu
                  v-model="showEndTimeMenu"
                  :close-on-content-click="false"
                  activator="parent"
                  min-width="0"
                >
                  <v-time-picker 
                    v-model="restrictionForm.endTime"
                    format="24hr"
                  ></v-time-picker>
                </v-menu>
              </v-text-field>
            </v-col>
          </v-row>

          <v-btn 
            type="submit" 
            color="primary" 
            class="mt-4 align-self-end"
            :disabled="!isRestrictionFormValid"
          >
            Adicionar à Lista
          </v-btn>
        </v-form>

        <v-divider class="my-6"></v-divider>

        <div v-if="timeRestrictionsOnly.length > 0">
          <h3 class="text-h6 mb-3">Restrições de Horário adicionadas</h3>
          <v-table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Detalhes</th>
                <th class="text-center" style="width: 100px;">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in timeRestrictionsOnly" :key="r.id">
                <td class="font-weight-medium">{{ getRestrictionTypeName(r.restriction_type) }}</td>
                <td>{{ getRestrictionDetails(r) }}</td>
                <td class="text-center">
                  <v-btn color="error" variant="text" size="small" @click="removeRestrictionById(r.id)">
                    Remover
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </div>

      </v-card-text>
    </v-card>

    <!-- Preference editing dialog -->
    <v-dialog v-model="editDialog.show" max-width="600px" persistent>
      <v-card class="rounded-xl pa-4">
        <v-card-title class="text-h6 font-weight-bold d-flex justify-space-between align-center border-bottom pb-2">
          <span>Editar Preferências - {{ editDialog.course?.name }}</span>
          <v-btn icon="mdi-close" variant="text" @click="closeEditDialog"></v-btn>
        </v-card-title>
        
        <v-card-text class="pt-4">
          <!-- Edit Priority -->
          <h4 class="text-subtitle-1 font-weight-bold mb-2">Prioridade da Disciplina</h4>
          <v-select
            v-model="editDialog.importanceLevel"
            :items="[
              { title: 'Baixa', value: 'low' },
              { title: 'Média', value: 'medium' },
              { title: 'Alta', value: 'high' }
            ]"
            label="Nível de Prioridade"
            variant="outlined"
            class="mb-4"
            hide-details
          ></v-select>

          <v-btn color="primary" variant="flat" class="rounded-lg mb-6" @click="saveImportancePreference">
            Atualizar Prioridade
          </v-btn>

          <v-divider class="mb-4"></v-divider>

          <!-- Manage Professors -->
          <h4 class="text-subtitle-1 font-weight-bold mb-2">Professores Preferidos</h4>
          
          <!-- List of existing professor preferences -->
          <v-table class="border rounded-lg mb-4" density="comfortable" v-if="editDialogProfessors.length > 0">
            <thead>
              <tr>
                <th>Professor</th>
                <th>Preferência</th>
                <th class="text-center" style="width: 80px;">Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="pref in editDialogProfessors" :key="pref.id">
                <td>{{ pref.preferred_professor }}</td>
                <td style="width: 140px;">
                  <v-select
                    v-model="pref.preference_order"
                    :items="[1, 2, 3]"
                    density="compact"
                    variant="outlined"
                    hide-details
                    @update:model-value="updateProfessorPreferenceOrder(pref)"
                  ></v-select>
                </td>
                <td class="text-center">
                  <v-btn icon="mdi-delete" color="error" variant="text" size="small" @click="deleteProfessorPreference(pref.id)"></v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
          <v-alert type="info" variant="tonal" class="rounded-lg mb-4" v-else>
            Nenhum professor preferido configurado para esta disciplina.
          </v-alert>

          <!-- Form to add new professor preference -->
          <v-card variant="outlined" class="pa-3 rounded-lg border-thin">
            <h5 class="text-subtitle-2 font-weight-bold mb-2">Adicionar Preferência de Professor</h5>
            <v-row no-gutters class="gap-2">
              <v-col cols="12" sm="7" class="pr-sm-2 mb-2 mb-sm-0">
                <v-combobox
                  v-model="editDialog.newProf"
                  :items="editDialogAvailableProfs"
                  label="Selecione o Professor"
                  variant="outlined"
                  density="compact"
                  hide-details
                ></v-combobox>
              </v-col>
              <v-col cols="12" sm="3" class="pr-sm-2 mb-2 mb-sm-0">
                <v-select
                  v-model="editDialog.newOrder"
                  :items="[1, 2, 3]"
                  label="Pref. #"
                  variant="outlined"
                  density="compact"
                  hide-details
                ></v-select>
              </v-col>
              <v-col cols="12" sm="2" class="d-flex align-center justify-center">
                <v-btn color="success" icon="mdi-plus" size="small" :disabled="!editDialog.newProf" @click="addProfessorPreferenceInDialog"></v-btn>
              </v-col>
            </v-row>
          </v-card>
        </v-card-text>
        
        <v-card-actions class="pa-4 pt-2 border-top-thin">
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="tonal" class="rounded-lg" @click="closeEditDialog">
            Fechar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { onMounted, reactive, ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  studentId: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['go-generate-schedule'])

const coursesList = ref([])
const sectionsList = ref([])

const semestersList = ref([])
const selectedSemester = ref('')

onMounted(() =>{
  loadCourses();
  loadDesiredCourses();
  loadRestrictions();
  loadDaysOfWeek();
  loadSemesters();
})

const loadCourses = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/students/${props.studentId}/eligible-courses`)
    coursesList.value = response.data
  } catch (error) {
    console.error('Erro ao buscar cadeiras:', error)
  }
}

const loadSemesters = async () => {
  try {
    const response = await axios.get('http://localhost:8000/sections/semesters')
    semestersList.value = response.data
    if (semestersList.value.length > 0) {
      selectedSemester.value = semestersList.value[0]
    } else {
      selectedSemester.value = '2026/1'
    }
  } catch (error) {
    console.error('Erro ao carregar semestres:', error)
    selectedSemester.value = '2026/1'
  }
}

const loadDesiredCourses = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/students/${props.studentId}/desired-courses`)
    interestList.value = Array.isArray(response.data) 
      ? response.data.map(curso => ({ course: curso }))
      : []
  } catch (error) {
    console.error('Erro ao carregar cadeiras de interesse:', error)
  }
}

const loadSections = async () => {
  try {
    const response = await axios.get('http://localhost:8000/sections/')
    sectionsList.value = response.data
  } catch (error) {
    console.error('Erro ao carregar turmas:', error)
  }
}

const daysOfWeekList = ref([])

const loadDaysOfWeek = async () => {
  try {
    const response = await axios.get('http://localhost:8000/days-of-week/')

    const dias = Array.isArray(response.data) ? response.data : []
    daysOfWeekList.value = dias.map(dia => {
      if (typeof dia === 'string') {
        return dia
      }

      return dia.name || dia.label || dia.dia || dia.day_of_week || dia.day || ''
    }).filter(Boolean)
  } catch (error) {
    console.error('Erro ao carregar dias da semana:', error)
    daysOfWeekList.value = []
  }
}

const showStartTimeMenu = ref(false)
const showEndTimeMenu = ref(false)

const currentForm = reactive({
  course: null,
  importanceLevel: 'medium',
  preferredProfessor: '',
  preferenceOrder: 1
})

const restrictionForm = reactive({
  type: 'hard_block',
  day: [],
  startTime: null,
  endTime: null,
  courseId: null,
  preferredProfessor: '',
  preferenceOrder: 1,
  importanceLevel: 'medium'
})

const interestList = ref([])
const restrictionsList = ref([])

const timeRestrictionsOnly = computed(() => {
  return restrictionsList.value.filter(
    r => r.restriction_type === 'hard_block' || r.restriction_type === 'preferred_window'
  )
})

const translatedDaysList = computed(() => {
  const translations = {
    Monday: 'Segunda-feira',
    Tuesday: 'Terça-feira',
    Wednesday: 'Quarta-feira',
    Thursday: 'Quinta-feira',
    Friday: 'Sexta-feira',
    Saturday: 'Sábado',
    Sunday: 'Domingo'
  }
  return daysOfWeekList.value.map(day => ({
    title: translations[day] || day,
    value: day
  }))
})

const availableFormProfessors = computed(() => {
  if (!currentForm.course) return []
  const courseSections = sectionsList.value.filter(s => s.course_id === currentForm.course.id)
  const profs = courseSections
    .map(s => s.professor_name)
    .filter(Boolean)
    .map(name => name.trim())
  return [...new Set(profs)].sort()
})

const filteredCourses = computed(() => {
  if (sectionsList.value.length === 0) return []
  const offeredCourseIds = new Set(sectionsList.value.map(s => s.course_id))
  return coursesList.value.filter(c => offeredCourseIds.has(c.id))
})

const loadSectionsForSemester = async () => {
  if (!selectedSemester.value) return
  try {
    const response = await axios.get(`http://localhost:8000/sections/?semester=${selectedSemester.value}`)
    sectionsList.value = response.data
  } catch (error) {
    console.error('Erro ao carregar turmas para o semestre:', error)
  }
}

watch(selectedSemester, () => {
  loadSectionsForSemester()
  currentForm.course = null
})

watch(() => currentForm.course, () => {
  currentForm.importanceLevel = 'medium'
  currentForm.preferredProfessor = ''
  currentForm.preferenceOrder = 1
})

const isRestrictionFormValid = computed(() => {
  if (restrictionForm.type === 'hard_block' || restrictionForm.type === 'preferred_window') {
    const hasDay = Array.isArray(restrictionForm.day) ? restrictionForm.day.length > 0 : restrictionForm.day
    return hasDay && restrictionForm.startTime && restrictionForm.endTime
  }
  return false
})

const addCourse = async () => {
  if (!currentForm.course) return

  const courseToAdd = currentForm.course
  const importanceLevel = currentForm.importanceLevel
  const preferredProfessor = currentForm.preferredProfessor
  const preferenceOrder = currentForm.preferenceOrder

  const jaExiste = interestList.value.some(item => item.course?.id === courseToAdd.id)
  
  if (jaExiste) {
    alert('Esta disciplina já foi adicionada na sua lista de interesse. Use o botão "Editar" na tabela abaixo para fazer alterações ou gerenciar os professores preferidos.')
    currentForm.course = null
    return
  }

  interestList.value.push({ course: courseToAdd })
  currentForm.course = null
  
  await saveDesiredCourses()

  try {
    await axios.post('http://localhost:8000/restrictions/', {
      student_id: props.studentId,
      restriction_type: 'course_importance',
      course_id: courseToAdd.id,
      importance_level: importanceLevel
    })
  } catch (error) {
    console.error('Erro ao cadastrar prioridade:', error)
  }

  if (preferredProfessor) {
    try {
      await axios.post('http://localhost:8000/restrictions/', {
        student_id: props.studentId,
        restriction_type: 'professor_preference',
        course_id: courseToAdd.id,
        preferred_professor: preferredProfessor,
        preference_order: preferenceOrder
      })
    } catch (error) {
      console.error('Erro ao cadastrar preferência de professor:', error)
    }
  }

  await loadRestrictions()
}

const removeFromList = async (index) => {
  const item = interestList.value[index]
  const courseId = item.course?.id

  interestList.value.splice(index, 1)
  await saveDesiredCourses()

  if (courseId) {
    const preferencesToDelete = restrictionsList.value.filter(
      r => r.course_id === courseId && 
      (r.restriction_type === 'course_importance' || r.restriction_type === 'professor_preference')
    )

    for (const pref of preferencesToDelete) {
      try {
        await axios.delete(`http://localhost:8000/restrictions/${pref.id}`)
      } catch (e) {
        console.error('Erro ao deletar preferência:', e)
      }
    }
    await loadRestrictions()
  }
}

const sendFinalList = () => {
  alert('Lista de interesse salva com sucesso!')
}

const formatTimeToHHMMSS = (timeStr) => {
  if (!timeStr) return null
  if (timeStr.split(':').length === 2) {
    return timeStr + ':00'
  }
  return timeStr
}

const addRestriction = async () => {
  if (!isRestrictionFormValid.value) {
    alert('Por favor, preencha os campos obrigatórios.')
    return
  }

  try {
    const days = Array.isArray(restrictionForm.day) ? restrictionForm.day : [restrictionForm.day]

    const promises = days.map(day => {
      const payload = {
        student_id: props.studentId,
        restriction_type: restrictionForm.type
      }

      if (restrictionForm.type === 'hard_block' || restrictionForm.type === 'preferred_window') {
        payload.day_of_week = day
        payload.start_time = formatTimeToHHMMSS(restrictionForm.startTime)
        payload.end_time = formatTimeToHHMMSS(restrictionForm.endTime)
      }

      return axios.post('http://localhost:8000/restrictions/', payload)
    })

    const responses = await Promise.all(promises)

    await loadRestrictions()

    // Reset Form
    restrictionForm.day = []
    restrictionForm.startTime = null
    restrictionForm.endTime = null
  } catch (error) {
    console.error('Erro ao adicionar restrição:', error)
    console.error('Detalhe da resposta:', error?.response?.data)
    const errorMsg = error?.response?.data?.detail 
      ? (Array.isArray(error.response.data.detail) ? error.response.data.detail.map(d => d.msg).join(', ') : error.response.data.detail)
      : error.message
    alert('Erro ao adicionar restrição: ' + errorMsg)
  }
}

const removeRestrictionById = async (id) => {
  try {
    await axios.delete(`http://localhost:8000/restrictions/${id}`)
    await loadRestrictions()
  } catch (error) {
    console.error('Erro ao remover restrição:', error)
    alert('Erro ao remover restrição.')
  }
}

const saveDesiredCourses = async () => {
  try {
    const courseIds = interestList.value.map(item => item.course?.id).filter(id => id)
    
    const response = await axios.post(`http://localhost:8000/students/${props.studentId}/desired-courses`, {
      course_ids: courseIds
    })
    
  } catch (error) {
    console.error('Erro ao salvar cadeiras de interesse:', error)
    alert('Erro ao salvar cadeiras.')
  }
}

const loadRestrictions = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/restrictions/?student_id=${props.studentId}`)
    
    restrictionsList.value = Array.isArray(response.data) 
      ? response.data.map(restricao => ({
          id: restricao.id,
          restriction_type: restricao.restriction_type || 'hard_block',
          dia: restricao.day_of_week || '',
          horario_inicio: restricao.start_time || '',
          horario_fim: restricao.end_time || '',
          course_id: restricao.course_id,
          preferred_professor: restricao.preferred_professor,
          preference_order: restricao.preference_order,
          importance_level: restricao.importance_level,
        }))
      : []
  } catch (error) {
    console.error('Erro ao carregar restrições/preferências:', error)
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

const getRestrictionTypeName = (type) => {
  const mapping = {
    hard_block: 'Bloqueio de Horário',
    preferred_window: 'Janela Preferida',
    professor_preference: 'Preferência de Professor',
    course_importance: 'Prioridade da Disciplina',
  }
  return mapping[type] || type
}

const getRestrictionDetails = (r) => {
  if (r.restriction_type === 'hard_block' || r.restriction_type === 'preferred_window') {
    return `${translateDay(r.dia)}: ${r.horario_inicio} - ${r.horario_fim}`
  }
  
  const course = coursesList.value.find(c => c.id === r.course_id)
  const courseName = course ? `${course.code} - ${course.name}` : `ID: ${r.course_id}`
  
  if (r.restriction_type === 'professor_preference') {
    return `${courseName} | Prof: ${r.preferred_professor} (Pref #${r.preference_order})`
  }
  if (r.restriction_type === 'course_importance') {
    const priorityLabels = { low: 'Baixa', medium: 'Média', high: 'Alta' }
    return `${courseName} | Prioridade: ${priorityLabels[r.importance_level] || r.importance_level}`
  }
  return ''
}

const getCoursePriorityLabel = (courseId) => {
  const r = restrictionsList.value.find(x => x.course_id === courseId && x.restriction_type === 'course_importance')
  if (!r) return 'Média'
  const priorityLabels = { low: 'Baixa', medium: 'Média', high: 'Alta' }
  return priorityLabels[r.importance_level] || r.importance_level
}

const getCourseProfessorLabel = (courseId) => {
  const prefs = restrictionsList.value.filter(x => x.course_id === courseId && x.restriction_type === 'professor_preference')
  if (prefs.length === 0) return 'Nenhum'
  const sortedPrefs = [...prefs].sort((a, b) => a.preference_order - b.preference_order)
  return sortedPrefs.map(r => `${r.preferred_professor} (#${r.preference_order})`).join(', ')
}

// Course preference editing logic
const editDialog = reactive({
  show: false,
  course: null,
  importanceLevel: 'medium',
  newProf: '',
  newOrder: 1
})

const editDialogProfessors = computed(() => {
  if (!editDialog.course) return []
  return restrictionsList.value.filter(
    r => r.course_id === editDialog.course.id && r.restriction_type === 'professor_preference'
  )
})

const editDialogAvailableProfs = computed(() => {
  if (!editDialog.course) return []
  const courseSections = sectionsList.value.filter(s => s.course_id === editDialog.course.id)
  const profs = courseSections
    .map(s => s.professor_name)
    .filter(Boolean)
    .map(name => name.trim())
  return [...new Set(profs)].sort()
})

const openEditDialog = (item) => {
  const course = item.course
  editDialog.course = course
  
  const r = restrictionsList.value.find(
    x => x.course_id === course.id && x.restriction_type === 'course_importance'
  )
  editDialog.importanceLevel = r ? r.importance_level : 'medium'
  
  editDialog.newProf = ''
  editDialog.newOrder = 1
  editDialog.show = true
}

const closeEditDialog = () => {
  editDialog.show = false
  editDialog.course = null
}

const saveImportancePreference = async () => {
  if (!editDialog.course) return
  const courseId = editDialog.course.id
  const existing = restrictionsList.value.find(
    r => r.course_id === courseId && r.restriction_type === 'course_importance'
  )
  
  try {
    if (existing) {
      await axios.delete(`http://localhost:8000/restrictions/${existing.id}`)
    }
    await axios.post('http://localhost:8000/restrictions/', {
      student_id: props.studentId,
      restriction_type: 'course_importance',
      course_id: courseId,
      importance_level: editDialog.importanceLevel
    })
    alert('Prioridade da disciplina atualizada com sucesso!')
    await loadRestrictions()
  } catch (error) {
    console.error('Erro ao atualizar prioridade:', error)
    alert('Erro ao atualizar prioridade.')
  }
}

const deleteProfessorPreference = async (id) => {
  try {
    await axios.delete(`http://localhost:8000/restrictions/${id}`)
    await loadRestrictions()
  } catch (error) {
    console.error('Erro ao remover preferência de professor:', error)
    alert('Erro ao remover preferência.')
  }
}

const addProfessorPreferenceInDialog = async () => {
  if (!editDialog.course || !editDialog.newProf) return
  const courseId = editDialog.course.id
  const profName = editDialog.newProf.trim()
  
  const alreadyExists = editDialogProfessors.value.some(
    p => p.preferred_professor.trim().toLowerCase() === profName.toLowerCase()
  )
  
  if (alreadyExists) {
    alert('Este professor já foi adicionado para esta disciplina!')
    return
  }
  
  try {
    await axios.post('http://localhost:8000/restrictions/', {
      student_id: props.studentId,
      restriction_type: 'professor_preference',
      course_id: courseId,
      preferred_professor: profName,
      preference_order: editDialog.newOrder
    })
    editDialog.newProf = ''
    editDialog.newOrder = 1
    await loadRestrictions()
  } catch (error) {
    console.error('Erro ao cadastrar preferência de professor:', error)
    alert('Erro ao cadastrar preferência de professor.')
  }
}

const updateProfessorPreferenceOrder = async (pref) => {
  if (!editDialog.course) return
  try {
    await axios.delete(`http://localhost:8000/restrictions/${pref.id}`)
    
    await axios.post('http://localhost:8000/restrictions/', {
      student_id: props.studentId,
      restriction_type: 'professor_preference',
      course_id: editDialog.course.id,
      preferred_professor: pref.preferred_professor,
      preference_order: pref.preference_order
    })
    
    await loadRestrictions()
  } catch (error) {
    console.error('Erro ao atualizar preferência de professor:', error)
    alert('Erro ao atualizar preferência de professor.')
  }
}
</script>