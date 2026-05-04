<template>
  <v-container>
    <v-card class="mx-auto" elevation="4">
      <v-card-title class="text-h5 font-weight-bold mt-4">
        Escolha suas disciplinas
      </v-card-title>
      
      <v-card-text>
        <v-form @submit.prevent="addCourse" class="d-flex flex-column gap-4">
          <v-row>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="currentForm.course"
                :items="coursesList"
                item-title="name"
                return-object
                label="Selecione a disciplina"
                variant="outlined"
                placeholder="Digite para buscar..."
                hide-details
              ></v-autocomplete>
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
                
                <th class="text-center" style="width: 100px;">Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in interestList" :key="index">
                <td class="font-weight-medium">{{ item.course?.name }}</td>
                
                <td class="text-center">
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
          
          <v-btn 
            color="success" 
            class="mt-4 align-self-end"
            @click="saveDesiredCourses"
          >
            Salvar
          </v-btn>

          <v-btn 
            color="primary" 
            variant="tonal"
            class="mt-4 ml-3 align-self-end"
            @click="emit('go-generate-schedule')"
          >
            Gerar grade de horários
          </v-btn>
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

    <v-card class="mt-6">
      <v-card-title class="text-h5 font-weight-bold mt-4">
        Informar Restrição de Horário (opcional)
      </v-card-title>

      <v-card-text>
        <v-form @submit.prevent="addRestriction" class="d-flex flex-column gap-4">
          <v-row>
            <v-col cols="12" md="6">
              <v-autocomplete
                v-model="restrictionForm.day"
                :items="daysOfWeekList"
                label="Selecione um dia da semana"
                variant="outlined"
                placeholder="Digite para buscar..."
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
            :disabled="!restrictionForm.day || !restrictionForm.startTime || !restrictionForm.endTime"
            >
            Adicionar à Lista
          </v-btn>
        </v-form>

        <v-divider class="my-6"></v-divider>

        <div v-if="restrictionsList.length > 0">
          <h3 class="text-h6 mb-3">Restrições adicionadas</h3>
          <v-table>
            <thead>
              <tr><th>Dia</th><th>Início</th><th>Fim</th><th class="text-center">Ações</th></tr>
            </thead>
            <tbody>
              <tr v-for="(r, idx) in restrictionsList" :key="r.id">
                <td>{{ r.dia }}</td>
                <td>{{ r.horario_inicio }}</td>
                <td>{{ r.horario_fim }}</td>
                <td class="text-center"><v-btn color="error" variant="text" size="small" @click="removeRestriction(idx)">Remover</v-btn></td>
              </tr>
            </tbody>
          </v-table>
        </div>

      </v-card-text>
    </v-card>

  </v-container>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['go-generate-schedule'])

const coursesList = ref([])

onMounted(() =>{
  loadCourses();
  loadDesiredCourses();
  loadRestrictions();
  loadDaysOfWeek();
})

const loadCourses = async () => {
  try {
    const response = await axios.get('http://localhost:8000/courses')
    console.log('Cadeiras disponíveis:', response.data)
    coursesList.value = response.data
  } catch (error) {
    console.error('Erro ao buscar cadeiras:', error)
  }
}

const loadDesiredCourses = async () => {
  try {
    const response = await axios.get('http://localhost:8000/students/1/desired-courses')
    console.log('Cadeiras de interesse carregadas:', response.data)
    interestList.value = Array.isArray(response.data) 
      ? response.data.map(curso => ({ course: curso }))
      : []
  } catch (error) {
    console.error('Erro ao carregar cadeiras de interesse:', error)
  }
}

const daysOfWeekList = ref([])

const loadDaysOfWeek = async () => {
  try {
    const response = await axios.get('http://localhost:8000/days-of-week/')
    console.log('Dias da semana carregados:', response.data)

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
})

const restrictionForm = reactive({
  day: null,
  startTime: null,
  endTime: null,
})

const interestList = ref([])
const restrictionsList = ref([])

const addCourse = () => {
  const jaExiste = interestList.value.some(item => item.course?.id === currentForm.course?.id)
  if (jaExiste) {
    alert('Você já adicionou essa disciplina na sua lista!')
    return
  }

  interestList.value.push({ course: currentForm.course })
  currentForm.course = null
}

const removeFromList = (index) => {
  interestList.value.splice(index, 1)
}

const sendFinalList = () => {
  console.log('Lista final enviada para a API:', JSON.stringify(interestList.value, null, 2))
  alert('Lista de interesse salva com sucesso!')
}

const addRestriction = async () => {
  if (!restrictionForm.day || !restrictionForm.startTime || !restrictionForm.endTime) {
    alert('Preencha dia, horário início e horário fim da restrição.')
    return
  }

  try {
    const response = await axios.post('http://localhost:8000/restrictions/', {
      day_of_week: restrictionForm.day,
      start_time: restrictionForm.startTime,
      end_time: restrictionForm.endTime
    })

    const createdRestriction = response.data || {}
    restrictionsList.value.push({
      id: createdRestriction.id || `r-${Date.now()}`,
      dia: createdRestriction.dia || createdRestriction.day_of_week || restrictionForm.day,
      horario_inicio: createdRestriction.horario_inicio || createdRestriction.start_time || restrictionForm.startTime,
      horario_fim: createdRestriction.horario_fim || createdRestriction.end_time || restrictionForm.endTime
    })

    restrictionForm.day = null
    restrictionForm.startTime = null
    restrictionForm.endTime = null
  } catch (error) {
    console.error('Erro ao adicionar restrição:', error)
    console.error('Detalhe da resposta:', error?.response?.data)
    alert('Erro ao adicionar restrição.')
  }
}

const removeRestriction = async (index) => {
  const restriction = restrictionsList.value[index]
  
  try {
    await axios.delete(`http://localhost:8000/restrictions/${restriction.id}`)
    console.log('Restrição removida da API:', restriction.id)
    restrictionsList.value.splice(index, 1)
  } catch (error) {
    console.error('Erro ao remover restrição:', error)
    alert('Erro ao remover restrição.')
  }
}

const saveDesiredCourses = async () => {
  try {
    // Extrai apenas os IDs das cadeiras
    const courseIds = interestList.value.map(item => item.course?.id).filter(id => id)
    
    const response = await axios.post('http://localhost:8000/students/1/desired-courses', {
      course_ids: courseIds
    })
    
    console.log('Cadeiras de interesse salvas:', response.data)
    alert('Cadeiras salvas com sucesso!')
  } catch (error) {
    console.error('Erro ao salvar cadeiras de interesse:', error)
    alert('Erro ao salvar cadeiras.')
  }
}

const loadRestrictions = async () => {
  try {
    const response = await axios.get('http://localhost:8000/restrictions/')
    console.log('Restrições de horário carregadas:', response.data)
    
    restrictionsList.value = Array.isArray(response.data) 
      ? response.data.map(restricao => ({
          id: restricao.id || `r-${Date.now()}`,
          dia: restricao.dia || restricao.day || restricao.day_of_week || '',
          horario_inicio: restricao.horario_inicio || restricao.start_time || '',
          horario_fim: restricao.horario_fim || restricao.end_time || ''
        }))
      : []
  } catch (error) {
    console.error('Erro ao carregar restrições de horário:', error)
  }
}

const saveRestrictions = async () => {
  try {
    const response = await axios.post('http://localhost:8000/restrictions/', {
      restrictions: restrictionsList.value.map(r => ({
        day_of_week: r.dia,
        start_time: r.horario_inicio,
        end_time: r.horario_fim
      }))
    })
    
    console.log('Restrições de horário salvas:', response.data)
    alert('Restrições salvas com sucesso!')
  } catch (error) {
    console.error('Erro ao salvar restrições de horário:', error)
    console.error('Detalhe da resposta:', error?.response?.data)
    alert('Erro ao salvar restrições.')
  }
}

</script>