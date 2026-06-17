<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import ufrgsData from './ufrgs_data.json'

const loading = ref(false)
const courses = ref([])
const searchQuery = ref('')
const selectedEtapa = ref('Todas')
const selectedCarater = ref('Todos')
const selectedCredits = ref('Todos')

const semesters = ref([])
const selectedSemester = ref('')
const sections = ref([])

const dialogOpen = ref(false)
const selectedCourse = ref(null)

const curricula = ref([
  { id: 1, name: 'Ciência da Computação' },
  { id: 2, name: 'Engenharia de Computação' }
])
const selectedCurriculum = ref({ id: 1, name: 'Ciência da Computação' })

// Map local metadata from ufrgs_data.json
const localCoursesMap = computed(() => {
  const map = {}
  if (!ufrgsData || !ufrgsData.curriculum) return map

  ufrgsData.curriculum.forEach(item => {
    const code = item.codigo === "" ? "TCC-CIC" : item.codigo
    map[code] = {
      etapa: item.etapa,
      carater: item.carater || 'Obrigatória'
    }
  })
  return map
})

const fetchCurricula = async () => {
  try {
    const response = await axios.get('http://localhost:8000/courses/curricula')
    if (response.data && response.data.length > 0) {
      curricula.value = response.data
      const exists = curricula.value.some(c => c.id === selectedCurriculum.value.id)
      if (!exists) {
        selectedCurriculum.value = curricula.value[0]
      }
    }
  } catch (error) {
    console.error('Erro ao buscar currículos:', error)
  }
}

const fetchCourses = async () => {
  loading.value = true
  try {
    let url = 'http://localhost:8000/courses/'
    if (selectedCurriculum.value) {
      url += `?curriculum_id=${selectedCurriculum.value.id}`
    }
    const response = await axios.get(url)
    const backendCourses = response.data || []
    
    courses.value = backendCourses.map(course => {
      const code = course.code === "" ? "TCC" : course.code
      
      let etapa = 'Eletiva / Extra'
      let carater = 'Eletiva'
      
      if (course.semester !== null && course.semester !== undefined) {
        etapa = `Etapa ${course.semester}`
      } else {
        const localMeta = localCoursesMap.value[code]
        if (localMeta) etapa = localMeta.etapa
      }
      
      if (course.mandatory !== null && course.mandatory !== undefined) {
        carater = course.mandatory ? 'Obrigatória' : 'Eletiva'
      } else {
        const localMeta = localCoursesMap.value[code]
        if (localMeta) carater = localMeta.carater
      }

      return {
        ...course,
        code,
        etapa,
        carater
      }
    })
  } catch (error) {
    console.error('Erro ao buscar disciplinas:', error)
  } finally {
    loading.value = false
  }
}

const fetchSemesters = async () => {
  try {
    const response = await axios.get('http://localhost:8000/sections/semesters')
    semesters.value = response.data || []
    if (semesters.value.length > 0) {
      selectedSemester.value = semesters.value[0]
    }
  } catch (error) {
    console.error('Erro ao buscar semestres:', error)
  }
}

const fetchSectionsForSemester = async () => {
  if (!selectedSemester.value) return
  try {
    const response = await axios.get(`http://localhost:8000/sections/?semester=${selectedSemester.value}`)
    sections.value = response.data || []
  } catch (error) {
    console.error('Erro ao buscar turmas:', error)
  }
}

// Watch selectedSemester to reload sections
watch(selectedSemester, () => {
  fetchSectionsForSemester()
})

// Watch selectedCurriculum to reload courses
watch(selectedCurriculum, () => {
  fetchCourses()
})

onMounted(async () => {
  await fetchCurricula()
  await fetchCourses()
  await fetchSemesters()
  await fetchSectionsForSemester()
})

// Filter Options
const etapas = computed(() => {
  const list = new Set()
  courses.value.forEach(c => {
    if (c.etapa) list.add(c.etapa)
  })
  // Sort stages numerically
  const sorted = Array.from(list).sort((a, b) => {
    const numA = parseInt(a.replace(/\D/g, '')) || 99
    const numB = parseInt(b.replace(/\D/g, '')) || 99
    return numA - numB
  })
  return ['Todas', ...sorted]
})

const carateres = ['Todos', 'Obrigatória', 'Eletiva']
const creditOptions = ['Todos', '2 créditos', '4 créditos', '6 créditos', '8 créditos']

// Filter Logic
const filteredCourses = computed(() => {
  return courses.value.filter(course => {
    // Text search (code or name)
    const matchesText = 
      course.code.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      course.name.toLowerCase().includes(searchQuery.value.toLowerCase())

    // Etapa filter
    const matchesEtapa = selectedEtapa.value === 'Todas' || course.etapa === selectedEtapa.value

    // Carater filter
    const matchesCarater = selectedCarater.value === 'Todos' || course.carater === selectedCarater.value

    // Credits filter
    let matchesCredits = true
    if (selectedCredits.value !== 'Todos') {
      const creditsNum = parseInt(selectedCredits.value.split(' ')[0])
      matchesCredits = course.credits === creditsNum
    }

    return matchesText && matchesEtapa && matchesCarater && matchesCredits
  })
})

const getCourseSections = (courseDbId) => {
  return sections.value.filter(sec => sec.course_id === courseDbId)
}

const translateDay = (day) => {
  const days = {
    'Monday': 'Segunda-feira',
    'Tuesday': 'Terça-feira',
    'Wednesday': 'Quarta-feira',
    'Thursday': 'Quinta-feira',
    'Friday': 'Sexta-feira',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo'
  }
  return days[day] || day
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return timeStr.substring(0, 5)
}

const openCourseDetails = (course) => {
  selectedCourse.value = course
  dialogOpen.value = true
}
</script>

<template>
  <div>
    <div class="d-flex align-center justify-between mb-4">
      <h1 class="text-h4 font-weight-bold text-primary">
        Pesquisar Disciplinas (Cadeiras)
      </h1>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        variant="outlined"
        prepend-icon="mdi-refresh"
        :loading="loading"
        @click="fetchCourses"
        class="rounded-lg font-weight-medium"
      >
        Atualizar
      </v-btn>
    </div>

    <v-divider class="mb-6"></v-divider>

    <!-- Barra de Filtros e Pesquisa -->
    <v-card class="pa-4 mb-6 rounded-xl elevation-2">
      <v-row align="center">
        <!-- Input de Pesquisa -->
        <v-col cols="12" md="3">
          <v-text-field
            v-model="searchQuery"
            prepend-inner-icon="mdi-magnify"
            label="Pesquisar por código ou nome..."
            variant="outlined"
            hide-details
            clearable
            class="rounded-lg"
          ></v-text-field>
        </v-col>

        <!-- Filtro por Grade Curricular -->
        <v-col cols="12" md="3">
          <v-select
            v-model="selectedCurriculum"
            :items="curricula"
            item-title="name"
            return-object
            label="Grade Curricular"
            variant="outlined"
            hide-details
            class="rounded-lg"
          ></v-select>
        </v-col>

        <!-- Filtro por Semestre de Oferta -->
        <v-col cols="12" sm="3" md="1.5">
          <v-select
            v-model="selectedSemester"
            :items="semesters"
            label="Semestre"
            variant="outlined"
            hide-details
            class="rounded-lg"
          ></v-select>
        </v-col>

        <!-- Filtro por Etapa -->
        <v-col cols="12" sm="3" md="1.5">
          <v-select
            v-model="selectedEtapa"
            :items="etapas"
            label="Etapa"
            variant="outlined"
            hide-details
            class="rounded-lg"
          ></v-select>
        </v-col>

        <!-- Filtro por Caráter -->
        <v-col cols="12" sm="3" md="1.5">
          <v-select
            v-model="selectedCarater"
            :items="carateres"
            label="Caráter"
            variant="outlined"
            hide-details
            class="rounded-lg"
          ></v-select>
        </v-col>

        <!-- Filtro por Créditos -->
        <v-col cols="12" sm="3" md="1.5">
          <v-select
            v-model="selectedCredits"
            :items="creditOptions"
            label="Créditos"
            variant="outlined"
            hide-details
            class="rounded-lg"
          ></v-select>
        </v-col>
      </v-row>
    </v-card>

    <!-- Grid de Resultados -->
    <v-row v-if="filteredCourses.length > 0">
      <v-col
        v-for="course in filteredCourses"
        :key="course.id"
        cols="12"
        sm="6"
        md="4"
        class="d-flex"
      >
        <v-card 
          class="flex-grow-1 rounded-xl d-flex flex-column shadow-premium border-card transition-all cursor-pointer" 
          elevation="2 hover"
          @click="openCourseDetails(course)"
        >
          <!-- Cabeçalho do Card com Tags -->
          <v-card-item class="pb-1">
            <div class="d-flex justify-space-between align-center mb-2">
              <v-chip
                color="primary"
                variant="flat"
                size="small"
                class="font-weight-bold"
              >
                {{ course.code }}
              </v-chip>
              <div class="d-flex align-center">
                <v-chip
                  :color="course.carater === 'Obrigatória' ? 'indigo-darken-1' : 'amber-darken-2'"
                  variant="tonal"
                  size="small"
                  class="font-weight-bold mr-1"
                >
                  {{ course.carater }}
                </v-chip>
                <v-chip
                  color="teal"
                  variant="outlined"
                  size="small"
                  class="font-weight-bold"
                >
                  {{ course.etapa }}
                </v-chip>
              </div>
            </div>
            
            <v-card-title class="text-h6 font-weight-bold text-wrap line-clamp-2 pt-1">
              {{ course.name }}
            </v-card-title>
          </v-card-item>

          <!-- Corpo do Card -->
          <v-card-text class="flex-grow-1 pt-2 pb-0">
            <!-- Créditos -->
            <div class="d-flex align-center mb-3">
              <v-icon color="grey-darken-1" size="18" class="mr-2">mdi-numeric-binary-box</v-icon>
              <span class="text-body-2 font-weight-medium">
                Créditos: <strong class="text-primary">{{ course.credits }}</strong> ({{ course.credits * 15 }}h)
              </span>
            </div>

            <!-- Créditos Mínimos -->
            <div v-if="course.min_credits_required > 0" class="d-flex align-center mb-3">
              <v-icon color="warning" size="18" class="mr-2">mdi-alert-circle-outline</v-icon>
              <span class="text-body-2 text-warning font-weight-bold">
                Exige {{ course.min_credits_required }} créditos obrigatórios
              </span>
            </div>

            <!-- Pré-requisitos -->
            <div v-if="course.prerequisites && course.prerequisites.length > 0" class="mb-4">
              <div class="text-caption font-weight-bold text-grey-darken-1 mb-1">
                Pré-requisitos:
              </div>
              <div class="d-flex flex-wrap gap-1">
                <v-tooltip
                  v-for="pre in course.prerequisites"
                  :key="pre.id"
                  :text="pre.name"
                  location="bottom"
                >
                  <template v-slot:activator="{ props }">
                    <v-chip
                      v-bind="props"
                      density="compact"
                      color="secondary"
                      variant="outlined"
                      size="small"
                      class="mr-1 mb-1"
                    >
                      {{ pre.code }}
                    </v-chip>
                  </template>
                </v-tooltip>
              </div>
            </div>
            <div v-else class="text-caption text-grey font-weight-medium italic mb-4">
              Sem pré-requisitos de disciplinas.
            </div>
          </v-card-text>

          <v-divider></v-divider>

          <!-- Footer visual para clique -->
          <div class="d-flex justify-center py-2.5 text-caption text-primary font-weight-medium cursor-pointer">
            <v-icon icon="mdi-information-outline" size="18" class="mr-1"></v-icon>
            Visualizar Turmas e Horários
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Estado de busca vazia -->
    <v-row v-else class="justify-center py-12">
      <v-col cols="12" class="text-center">
        <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-book-open-blank-variant</v-icon>
        <h3 class="text-h6 text-grey-darken-1 font-weight-bold">Nenhuma disciplina encontrada</h3>
        <p class="text-body-2 text-grey">Tente ajustar seus termos de pesquisa ou filtros.</p>
      </v-col>
    </v-row>

    <!-- Janela Modal (Dialog) sobreposta -->
    <v-dialog v-model="dialogOpen" max-width="600px" scrollable>
      <v-card class="rounded-xl overflow-hidden" elevation="10" v-if="selectedCourse">
        <!-- Dialog Header -->
        <v-card-title class="bg-primary text-white pa-4 d-flex align-center">
          <div class="text-truncate flex-grow-1 pr-2">
            <v-chip color="white" class="text-primary font-weight-bold mr-2" variant="flat" size="small">
              {{ selectedCourse.code }}
            </v-chip>
            <span class="text-h6 font-weight-bold align-middle">
              {{ selectedCourse.name }}
            </span>
          </div>
          <v-btn icon="mdi-close" variant="text" color="white" @click="dialogOpen = false" density="comfortable"></v-btn>
        </v-card-title>

        <v-card-text class="pa-6 bg-grey-lighten-5">
          <!-- Course Info Summary -->
          <div class="d-flex flex-wrap gap-2 mb-6">
            <v-chip color="indigo-darken-1" variant="tonal" size="small" class="font-weight-bold">
              {{ selectedCourse.carater }}
            </v-chip>
            <v-chip color="teal" variant="outlined" size="small" class="font-weight-bold">
              {{ selectedCourse.etapa }}
            </v-chip>
            <v-chip color="primary" variant="outlined" size="small" class="font-weight-bold">
              {{ selectedCourse.credits }} créditos ({{ selectedCourse.credits * 15 }}h)
            </v-chip>
            <v-chip v-if="selectedCourse.min_credits_required > 0" color="warning" variant="tonal" size="small" class="font-weight-bold">
              Mínimo {{ selectedCourse.min_credits_required }} creds
            </v-chip>
          </div>

          <!-- Section Offerings header -->
          <div class="text-subtitle-1 font-weight-bold text-grey-darken-3 mb-3 d-flex align-center">
            <v-icon size="20" class="mr-2" color="primary">mdi-calendar-clock</v-icon>
            Turmas no Semestre {{ selectedSemester }}
          </div>

          <!-- Section Offerings List -->
          <div v-if="getCourseSections(selectedCourse.id).length > 0">
            <v-card
              v-for="sec in getCourseSections(selectedCourse.id)"
              :key="sec.id"
              class="mb-3 pa-4 rounded-xl border elevation-0 bg-white"
            >
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-subtitle-2 font-weight-bold text-indigo">
                  Turma {{ sec.section_code }}
                </span>
              </div>

              <!-- Professor -->
              <div class="d-flex align-center mb-2">
                <v-icon size="16" color="grey-darken-1" class="mr-2">mdi-account-tie</v-icon>
                <span class="text-body-2 font-weight-medium">
                  {{ sec.professor_name || 'Sem professor definido' }}
                </span>
              </div>

              <!-- Horários -->
              <div v-if="sec.schedules && sec.schedules.length > 0" class="mt-3 pl-1">
                <div
                  v-for="sched in sec.schedules"
                  :key="sched.id"
                  class="d-flex align-center text-caption text-grey-darken-2 mb-1"
                >
                  <v-icon size="14" class="mr-2" color="grey">mdi-clock-outline</v-icon>
                  <span class="font-weight-medium mr-1">{{ translateDay(sched.day_of_week) }}:</span>
                  {{ formatTime(sched.start_time) }} - {{ formatTime(sched.end_time) }}
                  <span v-if="sched.room" class="ml-2 text-grey">({{ sched.room }})</span>
                </div>
              </div>
            </v-card>
          </div>
          <v-sheet v-else class="pa-8 rounded-xl text-center border bg-white">
            <v-icon size="40" color="grey-lighten-1" class="mb-2">mdi-calendar-remove</v-icon>
            <div class="text-caption text-grey italic font-weight-medium">
              Nenhuma turma ofertada para esta disciplina neste semestre.
            </div>
          </v-sheet>
        </v-card-text>

        <v-divider></v-divider>
        <v-card-actions class="pa-4 bg-white justify-end">
          <v-btn color="grey-darken-1" variant="outlined" class="rounded-lg px-4" @click="dialogOpen = false">
            Fechar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.gap-1 {
  gap: 4px;
}
.gap-2 {
  gap: 8px;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}
.transition-all {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.border-card {
  border: 1px solid rgba(var(--v-border-color), 0.08) !important;
}
.shadow-premium:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.08) !important;
}
.cursor-pointer {
  cursor: pointer;
}
</style>
