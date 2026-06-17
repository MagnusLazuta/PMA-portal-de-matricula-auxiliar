<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import axios from 'axios'

// Current active tab: 'curriculum', 'courses', 'sections'
const tab = ref('curriculum')

// Data lists
const curricula = ref([])
const courses = ref([])
const sections = ref([])
const loadingCourses = ref(false)
const loadingSections = ref(false)

// Shared states
const searchCourse = ref('')
const searchSection = ref('')

// Curriculum Tab States
const selectedCurriculum = ref(null)
const currCsvFile = ref(null)
const currCsvLoading = ref(false)
const currCsvSuccess = ref('')
const currCsvError = ref('')
const currCsvErrorsList = ref([])

// Course Form States
const courseCode = ref('')
const courseName = ref('')
const courseCredits = ref(4)
const courseMinCredits = ref(0)
const coursePrereqs = ref([])
const courseFormLoading = ref(false)
const courseFormSuccess = ref('')
const courseFormError = ref('')

// Course CSV States
const courseCsvLoading = ref(false)
const courseCsvSuccess = ref('')
const courseCsvError = ref('')
const courseCsvErrorsList = ref([])

// Section Form States
const secCourseId = ref(null)
const secCode = ref('')
const secSemester = ref('2026/1')
const secCapacity = ref(40)
const secProfessor = ref('')
const secSchedules = ref([]) // { day_of_week, start_time, end_time, room }
const sectionFormLoading = ref(false)
const sectionFormSuccess = ref('')
const sectionFormError = ref('')

// Section CSV States
const sectionCsvLoading = ref(false)
const sectionCsvSuccess = ref('')
const sectionCsvError = ref('')
const sectionCsvErrorsList = ref([])

// Weekday Mapping for English <-> Portuguese
const weekdaysList = [
  { title: 'Segunda-feira', value: 'Monday' },
  { title: 'Terça-feira', value: 'Tuesday' },
  { title: 'Quarta-feira', value: 'Wednesday' },
  { title: 'Quinta-feira', value: 'Thursday' },
  { title: 'Sexta-feira', value: 'Friday' },
  { title: 'Sábado', value: 'Saturday' },
  { title: 'Domingo', value: 'Sunday' }
]

const translateDay = (day) => {
  const found = weekdaysList.find(d => d.value === day)
  return found ? found.title : day
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return timeStr.substring(0, 5)
}

// Load data from Backend
const loadCurricula = async () => {
  try {
    const res = await axios.get('http://localhost:8000/admin/curricula')
    curricula.value = res.data
    if (curricula.value.length > 0 && !selectedCurriculum.value) {
      selectedCurriculum.value = curricula.value[0].id
    }
  } catch (err) {
    console.error('Erro ao buscar currículos:', err)
  }
}

const loadCourses = async () => {
  loadingCourses.value = true
  try {
    const res = await axios.get('http://localhost:8000/courses/?limit=1000')
    courses.value = res.data
  } catch (err) {
    console.error('Erro ao buscar disciplinas:', err)
  } finally {
    loadingCourses.value = false
  }
}

const loadSections = async () => {
  loadingSections.value = true
  try {
    const res = await axios.get('http://localhost:8000/sections/?limit=1000')
    sections.value = res.data
  } catch (err) {
    console.error('Erro ao buscar turmas:', err)
  } finally {
    loadingSections.value = false
  }
}

// Helpers
const getCourseDisplay = (courseId) => {
  const course = courses.value.find(c => c.id === courseId)
  return course ? `${course.code} - ${course.name}` : `ID: ${courseId}`
}

// Curriculum Actions
const triggerCurriculumUpload = () => {
  const input = document.getElementById('curriculumCsvFileInput')
  if (input) input.click()
}

const handleCurriculumFileChange = async (e) => {
  const file = e.target.value ? e.target.files[0] : null
  if (!file) return

  currCsvLoading.value = true
  currCsvSuccess.value = ''
  currCsvError.value = ''
  currCsvErrorsList.value = []

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await axios.post(`http://localhost:8000/admin/curriculum/${selectedCurriculum.value}/update`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (res.data.status === 'success') {
      currCsvSuccess.value = res.data.message
      await loadCourses()
    } else {
      currCsvError.value = res.data.message
      currCsvErrorsList.value = res.data.errors || []
    }
  } catch (err) {
    console.error(err)
    currCsvError.value = err?.response?.data?.detail || 'Erro ao enviar o arquivo CSV da matriz.'
  } finally {
    currCsvLoading.value = false
    e.target.value = ''
  }
}

// Course Form Actions
const isCourseFormValid = computed(() => {
  return courseCode.value.trim() !== '' &&
         courseName.value.trim() !== '' &&
         courseCredits.value > 0
})

const handleRegisterCourse = async () => {
  courseFormSuccess.value = ''
  courseFormError.value = ''
  courseFormLoading.value = true

  try {
    await axios.post('http://localhost:8000/admin/courses', {
      code: courseCode.value.trim().toUpperCase(),
      name: courseName.value.trim(),
      credits: Number(courseCredits.value),
      min_credits_required: Number(courseMinCredits.value),
      prerequisites: coursePrereqs.value
    })

    courseFormSuccess.value = `Disciplina "${courseName.value}" cadastrada com sucesso!`
    courseCode.value = ''
    courseName.value = ''
    courseCredits.value = 4
    courseMinCredits.value = 0
    coursePrereqs.value = []
    await loadCourses()
  } catch (err) {
    console.error(err)
    courseFormError.value = err?.response?.data?.detail || 'Erro ao cadastrar disciplina.'
  } finally {
    courseFormLoading.value = false
  }
}

// Course CSV Actions
const triggerCourseCsvUpload = () => {
  const input = document.getElementById('courseCsvFileInput')
  if (input) input.click()
}

const handleCourseCsvFileChange = async (e) => {
  const file = e.target.value ? e.target.files[0] : null
  if (!file) return

  courseCsvLoading.value = true
  courseCsvSuccess.value = ''
  courseCsvError.value = ''
  courseCsvErrorsList.value = []

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await axios.post('http://localhost:8000/admin/courses/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (res.data.created > 0) {
      courseCsvSuccess.value = `Importação concluída! ${res.data.created} disciplina(s) criada(s) com sucesso.`
    }

    if (res.data.errors && res.data.errors.length > 0) {
      courseCsvErrorsList.value = res.data.errors
      courseCsvError.value = 'Houve alguns erros durante a importação.'
    }

    await loadCourses()
  } catch (err) {
    console.error(err)
    courseCsvError.value = err?.response?.data?.detail || 'Erro ao importar CSV de disciplinas.'
  } finally {
    courseCsvLoading.value = false
    e.target.value = ''
  }
}

// Section Form Actions
const addSchedule = () => {
  secSchedules.value.push({
    day_of_week: 'Monday',
    start_time: '08:30',
    end_time: '10:10',
    room: ''
  })
}

const removeSchedule = (index) => {
  secSchedules.value.splice(index, 1)
}

const isSectionFormValid = computed(() => {
  return secCourseId.value !== null &&
         secCode.value.trim() !== '' &&
         secSemester.value.trim() !== '' &&
         secCapacity.value > 0
})

const handleRegisterSection = async () => {
  sectionFormSuccess.value = ''
  sectionFormError.value = ''
  sectionFormLoading.value = true

  try {
    await axios.post('http://localhost:8000/admin/sections', {
      course_id: Number(secCourseId.value),
      section_code: secCode.value.trim().toUpperCase(),
      semester: secSemester.value.trim(),
      capacity: Number(secCapacity.value),
      professor_name: secProfessor.value.trim() || null,
      schedules: secSchedules.value
    })

    sectionFormSuccess.value = `Turma "${secCode.value}" criada com sucesso!`
    secCourseId.value = null
    secCode.value = ''
    secCapacity.value = 40
    secProfessor.value = ''
    secSchedules.value = []
    await loadSections()
  } catch (err) {
    console.error(err)
    sectionFormError.value = err?.response?.data?.detail || 'Erro ao cadastrar turma.'
  } finally {
    sectionFormLoading.value = false
  }
}

// Section CSV Actions
const triggerSectionCsvUpload = () => {
  const input = document.getElementById('sectionCsvFileInput')
  if (input) input.click()
}

const handleSectionCsvFileChange = async (e) => {
  const file = e.target.value ? e.target.files[0] : null
  if (!file) return

  sectionCsvLoading.value = true
  sectionCsvSuccess.value = ''
  sectionCsvError.value = ''
  sectionCsvErrorsList.value = []

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await axios.post('http://localhost:8000/admin/sections/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (res.data.created > 0) {
      sectionCsvSuccess.value = `Importação concluída! ${res.data.created} turma(s) criada(s) com sucesso.`
    }

    if (res.data.errors && res.data.errors.length > 0) {
      sectionCsvErrorsList.value = res.data.errors
      sectionCsvError.value = 'Houve alguns erros durante a importação.'
    }

    await loadSections()
  } catch (err) {
    console.error(err)
    sectionCsvError.value = err?.response?.data?.detail || 'Erro ao importar CSV de turmas.'
  } finally {
    sectionCsvLoading.value = false
    e.target.value = ''
  }
}

// Filtered Lists
const filteredCoursesList = computed(() => {
  if (!searchCourse.value.trim()) return courses.value
  const q = searchCourse.value.toLowerCase()
  return courses.value.filter(c => 
    c.code.toLowerCase().includes(q) ||
    c.name.toLowerCase().includes(q)
  )
})

const filteredSectionsList = computed(() => {
  if (!searchSection.value.trim()) return sections.value
  const q = searchSection.value.toLowerCase()
  return sections.value.filter(s => {
    const courseDisplay = getCourseDisplay(s.course_id).toLowerCase()
    return s.section_code.toLowerCase().includes(q) ||
           s.semester.toLowerCase().includes(q) ||
           (s.professor_name && s.professor_name.toLowerCase().includes(q)) ||
           courseDisplay.includes(q)
  })
})

onMounted(() => {
  loadCurricula()
  loadCourses()
  loadSections()
})
</script>

<template>
  <v-container>
    <div class="mb-6">
      <h1 class="text-h4 font-weight-bold text-primary">Gerenciamento Acadêmico</h1>
      <p class="text-subtitle-1 text-medium-emphasis">
        Cadastre disciplinas, crie turmas e horários, e gerencie as matrizes curriculares dos cursos.
      </p>
    </div>

    <!-- Navigation Tabs -->
    <v-tabs v-model="tab" bg-color="transparent" color="primary" class="mb-6 border-b">
      <v-tab value="curriculum" class="text-subtitle-2 font-weight-bold">
        <v-icon start>mdi-sitemap</v-icon>
        Matrizes Curriculares
      </v-tab>
      <v-tab value="courses" class="text-subtitle-2 font-weight-bold">
        <v-icon start>mdi-book-open-variant</v-icon>
        Disciplinas
      </v-tab>
      <v-tab value="sections" class="text-subtitle-2 font-weight-bold">
        <v-icon start>mdi-calendar-clock</v-icon>
        Turmas e Horários
      </v-tab>
    </v-tabs>

    <v-window v-model="tab">
      
      <!-- TAB 1: CURRICULA -->
      <v-window-item value="curriculum">
        <v-row>
          <v-col cols="12" md="6">
            <v-card class="pa-6 rounded-xl h-100 shadow-premium" elevation="2">
              <v-card-title class="text-h6 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-upload-network</v-icon>
                Atualizar Matriz Curricular
              </v-card-title>
              
              <v-card-text class="px-0">
                <p class="text-body-2 text-medium-emphasis mb-4">
                  Selecione o curso e faça o upload de um arquivo CSV contendo a grade curricular completa. A grade atual desse curso será <strong>totalmente substituída</strong> pelos novos dados inseridos.
                </p>

                <v-select
                  v-model="selectedCurriculum"
                  :items="curricula"
                  item-title="name"
                  item-value="id"
                  label="Curso / Matriz"
                  variant="outlined"
                  density="comfortable"
                  class="mb-4"
                ></v-select>

                <!-- Feedback messages -->
                <v-alert v-if="currCsvSuccess" type="success" variant="tonal" class="mb-4" closable @click:close="currCsvSuccess = ''">
                  {{ currCsvSuccess }}
                </v-alert>
                <v-alert v-if="currCsvError" type="error" variant="tonal" class="mb-4" closable @click:close="currCsvError = ''">
                  {{ currCsvError }}
                  <div v-if="currCsvErrorsList.length" class="mt-2 text-caption max-errors-height">
                    <div v-for="(err, idx) in currCsvErrorsList" :key="idx">• {{ err }}</div>
                  </div>
                </v-alert>

                <input
                  type="file"
                  id="curriculumCsvFileInput"
                  accept=".csv"
                  style="display: none"
                  @change="handleCurriculumFileChange"
                />

                <v-btn
                  color="primary"
                  size="large"
                  prepend-icon="mdi-file-upload"
                  :loading="currCsvLoading"
                  @click="triggerCurriculumUpload"
                  block
                  :disabled="!selectedCurriculum || currCsvLoading"
                >
                  Selecionar CSV da Matriz
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="6">
            <v-card class="pa-6 rounded-xl h-100 border-card" elevation="1">
              <v-card-title class="text-h6 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
                <v-icon color="secondary" class="mr-2">mdi-information-outline</v-icon>
                Estrutura do CSV da Matriz
              </v-card-title>
              
              <v-card-text class="px-0 text-body-2">
                <p class="mb-3">
                  O arquivo CSV de atualização de matriz deve possuir exatamente o seguinte cabeçalho e estrutura:
                </p>
                <v-sheet class="pa-3 bg-grey-lighten-4 rounded text-caption font-mono mb-4 border text-truncate">
                  course_code,semester,mandatory
                </v-sheet>
                
                <span class="text-caption font-weight-bold text-uppercase d-block mb-1">Significado das Colunas:</span>
                <ul class="pl-4">
                  <li class="mb-2"><strong>course_code:</strong> Código da disciplina (ex: <code>INF01124</code>). A disciplina já deve estar previamente cadastrada no sistema.</li>
                  <li class="mb-2"><strong>semester:</strong> Semestre/Etapa sugerida do curso em que a disciplina é ofertada (número inteiro de 1 a 12).</li>
                  <li class="mb-2"><strong>mandatory:</strong> Valor booleano indicando obrigatoriedade da disciplina na matriz. Aceita: <code>1</code>, <code>True</code>, <code>true</code>, ou <code>Obrigatória</code> (caso contrário será considerada Eletiva).</li>
                </ul>

                <v-alert type="warning" variant="tonal" class="mt-4 text-caption" density="comfortable">
                  <strong>Importante:</strong> Esta operação é atômica. Se houver algum erro de validação (como código de disciplina inexistente), nenhuma modificação será salva no banco de dados.
                </v-alert>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-window-item>

      <!-- TAB 2: COURSES -->
      <v-window-item value="courses">
        <v-row class="mb-6">
          
          <!-- Individual Form -->
          <v-col cols="12" md="7">
            <v-card class="pa-6 rounded-xl shadow-premium h-100" elevation="2">
              <v-card-title class="text-h6 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-book-plus</v-icon>
                Cadastrar Nova Disciplina
              </v-card-title>
              
              <v-card-text class="px-0">
                <v-alert v-if="courseFormSuccess" type="success" variant="tonal" class="mb-4" closable @click:close="courseFormSuccess = ''">
                  {{ courseFormSuccess }}
                </v-alert>
                <v-alert v-if="courseFormError" type="error" variant="tonal" class="mb-4" closable @click:close="courseFormError = ''">
                  {{ courseFormError }}
                </v-alert>

                <v-form @submit.prevent="handleRegisterCourse">
                  <v-row>
                    <v-col cols="12" sm="4" class="py-1">
                      <v-text-field
                        v-model="courseCode"
                        label="Código da Disciplina"
                        placeholder="Ex: INF01124"
                        variant="outlined"
                        density="comfortable"
                        required
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="8" class="py-1">
                      <v-text-field
                        v-model="courseName"
                        label="Nome da Disciplina"
                        placeholder="Ex: Classificação e Pesquisa de Dados"
                        variant="outlined"
                        density="comfortable"
                        required
                      ></v-text-field>
                    </v-col>
                  </v-row>

                  <v-row>
                    <v-col cols="12" sm="6" class="py-1">
                      <v-text-field
                        v-model="courseCredits"
                        label="Créditos"
                        type="number"
                        min="1"
                        max="30"
                        variant="outlined"
                        density="comfortable"
                        required
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="6" class="py-1">
                      <v-text-field
                        v-model="courseMinCredits"
                        label="Créditos Mínimos Exigidos"
                        type="number"
                        min="0"
                        variant="outlined"
                        density="comfortable"
                        hint="Mínimo de créditos do aluno para poder matricular-se"
                        persistent-hint
                      ></v-text-field>
                    </v-col>
                  </v-row>

                  <v-autocomplete
                    v-model="coursePrereqs"
                    :items="courses"
                    item-title="name"
                    item-value="code"
                    label="Pré-requisitos"
                    multiple
                    chips
                    closable-chips
                    variant="outlined"
                    density="comfortable"
                    class="mt-4"
                    placeholder="Selecione as disciplinas pré-requisito..."
                  >
                    <template v-slot:chip="{ props, item }">
                      <v-chip
                        v-bind="props"
                        color="secondary"
                        variant="outlined"
                        size="small"
                      >
                        {{ item.raw.code }} - {{ item.raw.name }}
                      </v-chip>
                    </template>
                  </v-autocomplete>

                  <v-btn
                    type="submit"
                    color="primary"
                    size="large"
                    class="mt-4"
                    block
                    :disabled="!isCourseFormValid || courseFormLoading"
                    :loading="courseFormLoading"
                  >
                    Cadastrar Disciplina
                  </v-btn>
                </v-form>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- CSV Batch -->
          <v-col cols="12" md="5">
            <v-card class="pa-6 rounded-xl border-card h-100 d-flex flex-column" elevation="1">
              <v-card-title class="text-h6 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
                <v-icon color="secondary" class="mr-2">mdi-file-delimited-outline</v-icon>
                Importação em Lote (.csv)
              </v-card-title>
              
              <v-card-text class="px-0 flex-grow-1 overflow-y-auto" style="max-height: 420px;">
                <p class="text-body-2 text-medium-emphasis mb-3">
                  Importe disciplinas em lote usando um arquivo CSV contendo exatamente o seguinte cabeçalho:
                </p>
                <v-sheet class="pa-3 bg-grey-lighten-4 rounded text-caption font-mono mb-4 border text-truncate">
                  code,name,credits,min_credits_required,prerequisites
                </v-sheet>

                <span class="text-caption font-weight-bold text-uppercase d-block mb-1">Significado das Colunas:</span>
                <ul class="pl-4 text-caption mb-4">
                  <li class="mb-1.5"><strong>code:</strong> Código identificador único da disciplina (ex: <code>INF01124</code>).</li>
                  <li class="mb-1.5"><strong>name:</strong> Nome por extenso da disciplina (ex: <code>Classificação e Pesquisa de Dados</code>).</li>
                  <li class="mb-1.5"><strong>credits:</strong> Número de créditos (ex: <code>4</code> ou <code>6</code>). Cada crédito equivale a 15 horas aula.</li>
                  <li class="mb-1.5"><strong>min_credits_required:</strong> Quantidade mínima de créditos que o estudante precisa ter cursado para se matricular (opcional, padrão <code>0</code>).</li>
                  <li class="mb-1.5"><strong>prerequisites:</strong> Códigos de pré-requisitos separados por ponto e vírgula <code>;</code> (ex: <code>MAT01353;INF01202</code>). Deixe em branco se não houver.</li>
                </ul>

                <!-- Feedback CSV -->
                <v-alert v-if="courseCsvSuccess" type="success" variant="tonal" class="mb-4" closable @click:close="courseCsvSuccess = ''">
                  {{ courseCsvSuccess }}
                </v-alert>
                <v-alert v-if="courseCsvError" type="error" variant="tonal" class="mb-4" closable @click:close="courseCsvError = ''">
                  {{ courseCsvError }}
                  <div v-if="courseCsvErrorsList.length" class="mt-2 text-caption max-errors-height">
                    <div v-for="(err, idx) in courseCsvErrorsList" :key="idx">• {{ err }}</div>
                  </div>
                </v-alert>

                <input
                  type="file"
                  id="courseCsvFileInput"
                  accept=".csv"
                  style="display: none"
                  @change="handleCourseCsvFileChange"
                />

                <v-btn
                  color="secondary"
                  variant="outlined"
                  size="large"
                  prepend-icon="mdi-upload"
                  :loading="courseCsvLoading"
                  @click="triggerCourseCsvUpload"
                  block
                >
                  Upload de CSV de Disciplinas
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Course List Table -->
        <v-card class="pa-6 rounded-xl shadow-premium" elevation="2">
          <div class="d-flex justify-space-between align-center mb-4 flex-wrap gap-2">
            <v-card-title class="text-h6 font-weight-bold px-0 pt-0 d-flex align-center">
              <v-icon color="primary" class="mr-2">mdi-format-list-bulleted</v-icon>
              Disciplinas Cadastradas
            </v-card-title>
            
            <v-text-field
              v-model="searchCourse"
              label="Buscar por código ou nome..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              style="max-width: 350px; min-width: 250px"
              clearable
            ></v-text-field>
          </div>

          <v-data-table
            v-if="!loadingCourses"
            :items="filteredCoursesList"
            :headers="[
              { title: 'Código', key: 'code', width: '15%' },
              { title: 'Nome', key: 'name', width: '45%' },
              { title: 'Créditos', key: 'credits', align: 'center', width: '10%' },
              { title: 'Créditos Mínimos', key: 'min_credits_required', align: 'center', width: '15%' },
              { title: 'Pré-requisitos', key: 'prerequisites', sortable: false, width: '15%' }
            ]"
            density="comfortable"
            class="border rounded-lg"
            items-per-page-text="Itens por página:"
            page-text="{0}-{1} de {2}"
          >
            <template v-slot:item="{ item }">
              <tr>
                <td class="font-weight-bold text-primary">{{ item.code }}</td>
                <td>{{ item.name }}</td>
                <td class="text-center">{{ item.credits }}</td>
                <td class="text-center">{{ item.min_credits_required || '—' }}</td>
                <td>
                  <div class="d-flex flex-wrap gap-1 py-1" v-if="item.prerequisites && item.prerequisites.length > 0">
                    <v-tooltip
                      v-for="pre in item.prerequisites"
                      :key="pre.id"
                      :text="pre.name"
                      location="top"
                    >
                      <template v-slot:activator="{ props }">
                        <v-chip
                          v-bind="props"
                          density="compact"
                          color="secondary"
                          variant="outlined"
                          size="small"
                        >
                          {{ pre.code }}
                        </v-chip>
                      </template>
                    </v-tooltip>
                  </div>
                  <span v-else class="text-caption text-medium-emphasis">Nenhum</span>
                </td>
              </tr>
            </template>
          </v-data-table>
          <v-progress-linear v-else indeterminate color="primary"></v-progress-linear>
        </v-card>
      </v-window-item>

      <!-- TAB 3: SECTIONS -->
      <v-window-item value="sections">
        <v-row class="mb-6">
          
          <!-- Individual Section Form -->
          <v-col cols="12" md="7">
            <v-card class="pa-6 rounded-xl shadow-premium h-100" elevation="2">
              <v-card-title class="text-h6 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-calendar-plus</v-icon>
                Cadastrar Nova Turma
              </v-card-title>
              
              <v-card-text class="px-0">
                <v-alert v-if="sectionFormSuccess" type="success" variant="tonal" class="mb-4" closable @click:close="sectionFormSuccess = ''">
                  {{ sectionFormSuccess }}
                </v-alert>
                <v-alert v-if="sectionFormError" type="error" variant="tonal" class="mb-4" closable @click:close="sectionFormError = ''">
                  {{ sectionFormError }}
                </v-alert>

                <v-form @submit.prevent="handleRegisterSection">
                  <v-autocomplete
                    v-model="secCourseId"
                    :items="courses"
                    item-title="name"
                    item-value="id"
                    label="Disciplina"
                    variant="outlined"
                    density="comfortable"
                    required
                    placeholder="Selecione a disciplina..."
                    class="mb-2"
                  >
                    <template v-slot:item="{ props, item }">
                      <v-list-item v-bind="props" :title="`${item.raw.code} - ${item.raw.name}`"></v-list-item>
                    </template>
                  </v-autocomplete>

                  <v-row>
                    <v-col cols="12" sm="4" class="py-1">
                      <v-text-field
                        v-model="secCode"
                        label="Turma (Código)"
                        placeholder="Ex: A, B, U"
                        variant="outlined"
                        density="comfortable"
                        required
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="4" class="py-1">
                      <v-text-field
                        v-model="secSemester"
                        label="Semestre Letivo"
                        placeholder="Ex: 2026/1"
                        variant="outlined"
                        density="comfortable"
                        required
                      ></v-text-field>
                    </v-col>
                    <v-col cols="12" sm="4" class="py-1">
                      <v-text-field
                        v-model="secCapacity"
                        label="Capacidade (Vagas)"
                        type="number"
                        min="1"
                        variant="outlined"
                        density="comfortable"
                        required
                      ></v-text-field>
                    </v-col>
                  </v-row>

                  <v-text-field
                    v-model="secProfessor"
                    label="Professor da Turma"
                    placeholder="Nome completo do docente (opcional)"
                    variant="outlined"
                    density="comfortable"
                    class="mb-3"
                  ></v-text-field>

                  <!-- Dynamic Schedules -->
                  <div class="border rounded-lg pa-4 mb-4">
                    <div class="d-flex justify-space-between align-center mb-4">
                      <span class="text-subtitle-2 font-weight-bold">Horários da Turma</span>
                      <v-btn
                        size="small"
                        color="secondary"
                        variant="tonal"
                        prepend-icon="mdi-plus"
                        @click="addSchedule"
                      >
                        Adicionar Horário
                      </v-btn>
                    </div>

                    <div v-if="secSchedules.length === 0" class="text-caption text-medium-emphasis text-center py-4 italic">
                      Nenhum horário adicionado ainda. Turmas sem horário cadastrado podem conflitar ou ficar ocultas na geração de grade.
                    </div>

                    <v-row
                      v-for="(sched, index) in secSchedules"
                      :key="index"
                      class="align-center mb-2"
                      dense
                    >
                      <v-col cols="12" sm="4">
                        <v-select
                          v-model="sched.day_of_week"
                          :items="weekdaysList"
                          label="Dia da Semana"
                          variant="outlined"
                          density="compact"
                          hide-details
                        ></v-select>
                      </v-col>
                      <v-col cols="6" sm="2">
                        <v-text-field
                          v-model="sched.start_time"
                          label="Início"
                          type="time"
                          variant="outlined"
                          density="compact"
                          hide-details
                        ></v-text-field>
                      </v-col>
                      <v-col cols="6" sm="2">
                        <v-text-field
                          v-model="sched.end_time"
                          label="Fim"
                          type="time"
                          variant="outlined"
                          density="compact"
                          hide-details
                        ></v-text-field>
                      </v-col>
                      <v-col cols="10" sm="3">
                        <v-text-field
                          v-model="sched.room"
                          label="Sala"
                          placeholder="Ex: 101"
                          variant="outlined"
                          density="compact"
                          hide-details
                        ></v-text-field>
                      </v-col>
                      <v-col cols="2" sm="1" class="text-center">
                        <v-btn
                          icon="mdi-delete"
                          color="error"
                          variant="text"
                          density="comfortable"
                          @click="removeSchedule(index)"
                        ></v-btn>
                      </v-col>
                    </v-row>
                  </div>

                  <v-btn
                    type="submit"
                    color="primary"
                    size="large"
                    block
                    :disabled="!isSectionFormValid || sectionFormLoading"
                    :loading="sectionFormLoading"
                  >
                    Criar Turma
                  </v-btn>
                </v-form>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- CSV Batch Section -->
          <v-col cols="12" md="5">
            <v-card class="pa-6 rounded-xl border-card h-100 d-flex flex-column" elevation="1">
              <v-card-title class="text-h6 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
                <v-icon color="secondary" class="mr-2">mdi-file-delimited-outline</v-icon>
                Importação em Lote (.csv)
              </v-card-title>
              
              <v-card-text class="px-0 flex-grow-1 overflow-y-auto" style="max-height: 420px;">
                <p class="text-body-2 text-medium-emphasis mb-3">
                  Importe turmas em lote com arquivo CSV contendo exatamente o seguinte cabeçalho:
                </p>
                <v-sheet class="pa-3 bg-grey-lighten-4 rounded text-caption font-mono mb-4 border text-truncate">
                  course_code,section_code,semester,capacity,professor_name,schedules
                </v-sheet>

                <span class="text-caption font-weight-bold text-uppercase d-block mb-1">Significado das Colunas:</span>
                <ul class="pl-4 text-caption mb-4">
                  <li class="mb-1.5"><strong>course_code:</strong> Código da disciplina vinculada (ex: <code>INF01124</code>). A disciplina deve estar cadastrada.</li>
                  <li class="mb-1.5"><strong>section_code:</strong> Código identificador da turma (ex: <code>A</code>, <code>B</code> ou <code>U</code>).</li>
                  <li class="mb-1.5"><strong>semester:</strong> Semestre de oferta da turma (ex: <code>2026/1</code>).</li>
                  <li class="mb-1.5"><strong>capacity:</strong> Número máximo de vagas / capacidade da turma (ex: <code>45</code>).</li>
                  <li class="mb-1.5"><strong>professor_name:</strong> Nome por extenso do professor docente (opcional).</li>
                  <li class="mb-1.5">
                    <strong>schedules:</strong> Horários da turma separados por ponto e vírgula <code>;</code> no formato:
                    <div class="my-1 bg-grey-lighten-3 pa-2 rounded font-mono text-truncate">
                      Dia HorarioInicio-HorarioFim Sala
                    </div>
                    <em>Exemplo:</em> <code>Monday 08:30-10:10 Sala 101; Wednesday 08:30-10:10 Sala 101</code>. Os dias aceitam inglês (Monday, Tuesday...) ou português (Segunda, Terça...).
                  </li>
                </ul>

                <!-- Feedback CSV -->
                <v-alert v-if="sectionCsvSuccess" type="success" variant="tonal" class="mb-4" closable @click:close="sectionCsvSuccess = ''">
                  {{ sectionCsvSuccess }}
                </v-alert>
                <v-alert v-if="sectionCsvError" type="error" variant="tonal" class="mb-4" closable @click:close="sectionCsvError = ''">
                  {{ sectionCsvError }}
                  <div v-if="sectionCsvErrorsList.length" class="mt-2 text-caption max-errors-height">
                    <div v-for="(err, idx) in sectionCsvErrorsList" :key="idx">• {{ err }}</div>
                  </div>
                </v-alert>

                <input
                  type="file"
                  id="sectionCsvFileInput"
                  accept=".csv"
                  style="display: none"
                  @change="handleSectionCsvFileChange"
                />

                <v-btn
                  color="secondary"
                  variant="outlined"
                  size="large"
                  prepend-icon="mdi-upload"
                  :loading="sectionCsvLoading"
                  @click="triggerSectionCsvUpload"
                  block
                >
                  Upload de CSV de Turmas
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Sections Table -->
        <v-card class="pa-6 rounded-xl shadow-premium" elevation="2">
          <div class="d-flex justify-space-between align-center mb-4 flex-wrap gap-2">
            <v-card-title class="text-h6 font-weight-bold px-0 pt-0 d-flex align-center">
              <v-icon color="primary" class="mr-2">mdi-format-list-bulleted</v-icon>
              Turmas Cadastradas
            </v-card-title>
            
            <v-text-field
              v-model="searchSection"
              label="Buscar por disciplina, professor, semestre ou turma..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              style="max-width: 450px; min-width: 250px"
              clearable
            ></v-text-field>
          </div>

          <v-data-table
            v-if="!loadingSections"
            :items="filteredSectionsList"
            :headers="[
              { title: 'Disciplina', key: 'course_id', width: '35%' },
              { title: 'Turma', key: 'section_code', align: 'center', width: '10%' },
              { title: 'Semestre', key: 'semester', align: 'center', width: '10%' },
              { title: 'Vagas', key: 'capacity', align: 'center', width: '10%' },
              { title: 'Professor', key: 'professor_name', width: '20%' },
              { title: 'Horários', key: 'schedules', sortable: false, width: '15%' }
            ]"
            density="comfortable"
            class="border rounded-lg"
            items-per-page-text="Itens por página:"
            page-text="{0}-{1} de {2}"
          >
            <template v-slot:item="{ item }">
              <tr>
                <td class="font-weight-medium">{{ getCourseDisplay(item.course_id) }}</td>
                <td class="text-center font-weight-bold text-indigo">{{ item.section_code }}</td>
                <td class="text-center">{{ item.semester }}</td>
                <td class="text-center">{{ item.capacity }}</td>
                <td>{{ item.professor_name || 'A definir' }}</td>
                <td>
                  <div v-if="item.schedules && item.schedules.length > 0" class="py-1">
                    <div
                      v-for="sched in item.schedules"
                      :key="sched.id"
                      class="text-caption mb-1"
                    >
                      <v-chip size="x-small" color="primary" variant="outlined" class="mr-1">
                        {{ translateDay(sched.day_of_week) }}
                      </v-chip>
                      <span>{{ formatTime(sched.start_time) }}-{{ formatTime(sched.end_time) }}</span>
                      <span v-if="sched.room" class="text-grey ml-1">({{ sched.room }})</span>
                    </div>
                  </div>
                  <span v-else class="text-caption text-medium-emphasis">Sem horários</span>
                </td>
              </tr>
            </template>
          </v-data-table>
          <v-progress-linear v-else indeterminate color="primary"></v-progress-linear>
        </v-card>
      </v-window-item>

    </v-window>
  </v-container>
</template>

<style scoped>
.gap-1 {
  gap: 4px;
}
.gap-2 {
  gap: 8px;
}
.max-errors-height {
  max-height: 150px;
  overflow-y: auto;
}
.border-card {
  border: 1px solid rgba(var(--v-border-color), 0.12) !important;
}
.transition-all {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.shadow-premium {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
}
.italic {
  font-style: italic;
}
</style>
