<script setup>
import { onMounted, ref } from 'vue'
import axios from 'axios'

const emit = defineEmits(['back'])

const scheduleOptions = ref([])
const loading = ref(false)
const error = ref('')

const dayOrder = {
  'Segunda-feira': 1,
  'Terça-feira': 2,
  'Quarta-feira': 3,
  'Quinta-feira': 4,
  'Sexta-feira': 5,
  'Sábado': 6,
  'Domingo': 7,
}

const convertTimeToMinutes = (hora) => {
  if (!hora || typeof hora !== 'string') {
    return 0
  }

  const [horas, minutos] = hora.split(':').map(Number)
  return (horas * 60) + (minutos || 0)
}

const normalizeDay = (raw) => {
  if (raw === null || raw === undefined) return '—'
  if (typeof raw === 'number') {
    const num = raw
    const mapNum = {
      1: 'Segunda-feira', 2: 'Terça-feira', 3: 'Quarta-feira', 4: 'Quinta-feira', 5: 'Sexta-feira', 6: 'Sábado', 7: 'Domingo', 0: 'Domingo'
    }
    return mapNum[num] || String(raw)
  }
  const s = String(raw).trim().toLowerCase()
  if (!s) return '—'
  if (/^mon|segunda/.test(s)) return 'Segunda-feira'
  if (/^tue|terc/.test(s)) return 'Terça-feira'
  if (/^wed|qua/.test(s)) return 'Quarta-feira'
  if (/^thu|qui/.test(s)) return 'Quinta-feira'
  if (/^fri|sex|sexta/.test(s)) return 'Sexta-feira'
  if (/^sat|sab/.test(s)) return 'Sábado'
  if (/^sun|dom/.test(s)) return 'Domingo'
  return String(raw)
}

const formatMinutes = (minutos) => {
  const h = Math.floor(minutos / 60)
  const m = minutos % 60
  return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0')
}

const buildTimeSlots = (schedule, step = 30) => {
  if (!Array.isArray(schedule) || schedule.length === 0) return []
  let minStart = Infinity
  let maxEnd = -Infinity
  schedule.forEach(it => {
    const s = convertTimeToMinutes(it.start_time)
    const e = convertTimeToMinutes(it.end_time)
    if (s < minStart) minStart = s
    if (e > maxEnd) maxEnd = e
  })
  minStart = Math.floor(minStart / step) * step
  maxEnd = Math.ceil(maxEnd / step) * step

  const slots = []
  for (let t = minStart; t < maxEnd; t += step) slots.push(t)
  return slots
}

const daysArray = Object.keys(dayOrder)
  .filter(d => d !== 'Domingo' && d !== 'Sábado')
  .map(d => ({ name: d, index: dayOrder[d] }))
  .sort((a,b) => (a.index||999)-(b.index||999))

const mapItemsByStartSlot = (schedule, slots) => {
  const mapa = {}
  (schedule || []).forEach(item => {
    const start = convertTimeToMinutes(item.start_time)
    // find closest slot equal to start
    const slot = slots.find(s => s === start)
    const key = (item.day_of_week || '—') + '|' + (slot ?? start)
    if (!mapa[key]) mapa[key] = []
    mapa[key].push(item)
  })
  return mapa
}

const sortSchedule = (schedule) => {
  return [...schedule].sort((a, b) => {
    const dayOrderA = dayOrder[a.day_of_week] || 999
    const dayOrderB = dayOrder[b.day_of_week] || 999

    if (dayOrderA !== dayOrderB) {
      return dayOrderA - dayOrderB
    }

    return convertTimeToMinutes(a.start_time) - convertTimeToMinutes(b.start_time)
  })
}

const groupSchedule = (schedule) => {
  const mapa = {}
  (schedule || []).forEach(item => {
    const rawDay = item.day_of_week ?? item.day ?? item.dia ?? item.weekday ?? item.week_day ?? item.day_number ?? item.weekday_number ?? '—'
    const day = normalizeDay(rawDay)
    if (!mapa[day]) mapa[day] = []
    mapa[day].push(item)
  })

  Object.keys(mapa).forEach(d => {
    mapa[d].sort((a,b) => convertTimeToMinutes(a.start_time) - convertTimeToMinutes(b.start_time))
  })

  return Object.keys(mapa)
    .sort((a,b) => (dayOrder[a]||999) - (dayOrder[b]||999))
    .map(d => ({ day: d, items: mapa[d] }))
}

const buildCalendarMatrix = (items, step = 30) => {
  try {
    const slots = buildTimeSlots(items, step)
    const matrix = {}
    const skip = {}

    ;(items || []).forEach(it => {
      const rawDay = it.day_of_week ?? it.day ?? it.dia ?? it.weekday ?? it.week_day ?? it.day_number ?? it.weekday_number ?? '—'
      const normalized = normalizeDay(rawDay)
      const dayIndex = dayOrder[normalized] || null
      const start = convertTimeToMinutes(it.start_time)
      const end = convertTimeToMinutes(it.end_time)
      const duration = Math.max(0, end - start)
      const rowspan = Math.max(1, Math.round(duration / step))

      const key = (dayIndex !== null ? String(dayIndex) : normalizeDay(rawDay)) + '|' + start
      matrix[key] = { item: it, rowspan, dayNormalized: normalized, dayIndex }

      for (let i = 0; i < rowspan; i++) {
        const coveredSlot = start + i * step
        const skipKey = (dayIndex !== null ? String(dayIndex) : normalizeDay(rawDay)) + '|' + coveredSlot
        skip[skipKey] = true
      }
    })

    return { slots, matrix, skip }
  } catch (err) {
    console.error('Erro em buildCalendarMatrix:', err)
    console.error(err && err.stack)
    return { slots: [], matrix: {}, skip: {} }
  }
}

const getCell = (gradeObj, dia, slot) => {
  const keyIndex = `${dia.index}|${slot}`
  const keyName = `${dia.name}|${slot}`
  const cell = gradeObj.matrix[keyIndex] || gradeObj.matrix[keyName] || null
  const keyUsed = gradeObj.matrix[keyIndex] ? keyIndex : (gradeObj.matrix[keyName] ? keyName : null)
  const conflict = cell && cell.dayIndex != null && cell.dayIndex !== dia.index
  if (conflict) {
    console.warn('Day conflict detected for slot', slot, 'column', dia.name, 'keyUsed', keyUsed, 'cellDayIndex', cell.dayIndex, 'cellDayNormalized', cell.dayNormalized, 'item', cell.item)
  }
  return { cell, keyUsed, conflict }
}

const loadSchedules = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await axios.post('http://127.0.0.1:8000/generate-schedules/', {
      student_id: 1
    }, { timeout: 10000 })
    const raw = Array.isArray(response.data) ? response.data : []
    scheduleOptions.value = raw.map((g, gi) => {
      console.debug('Raw grade', gi, g)
      const items = Array.isArray(g) ? sortSchedule(g) : []
      const { slots, matrix, skip } = buildCalendarMatrix(items, 30)
      const obj = { items, slots, matrix, skip }
      console.debug('Mapped gradeObj', gi, obj)
      return obj
    })
  } catch (error) {
    console.error('Erro ao gerar grades:', error)
    console.error(error && error.stack)
    const detalhe = error?.response?.data || error?.message || String(error)
    error.value = typeof detalhe === 'string' ? detalhe : JSON.stringify(detalhe)
    scheduleOptions.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSchedules()
})
</script>

<template>
  <v-container>
    <v-card class="mx-auto" elevation="4">
      <v-card-title class="text-h5 font-weight-bold mt-4 d-flex align-center justify-space-between">
        Grades de horários geradas
        <v-btn color="primary" variant="tonal" @click="emit('back')">
          Voltar
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4">
            <div>{{ error }}</div>
            <v-btn color="primary" class="mt-3" @click="loadSchedules">Tentar novamente</v-btn>
        </v-alert>

        <v-progress-linear v-if="loading" indeterminate class="mb-4" />

        <div v-if="!loading && scheduleOptions.length === 0 && !error">
          <v-alert type="info" variant="tonal">
            Nenhuma grade foi retornada pela API.
          </v-alert>
        </div>

        <v-row v-else>
          <v-col
            v-for="(gradeObj, scheduleIndex) in scheduleOptions"
            :key="scheduleIndex"
            cols="12"
            md="12"
          >
            <v-card variant="outlined" class="mb-4">
              <v-card-title class="text-subtitle-1 font-weight-bold">
                Opção {{ scheduleIndex + 1 }}
              </v-card-title>

              <v-card-text>
                <div class="calendar-wrapper">
                  <table class="calendar-table">
                    <thead>
                      <tr>
                        <th class="time-col">Horário</th>
                        <th v-for="dia in daysArray" :key="dia.index">{{ dia.name }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <template v-for="(slot, si) in gradeObj.slots" :key="si">
                          <tr>
                            <td class="time-col">{{ formatMinutes(slot) }}</td>
                            
                            <template v-for="(dia, di) in daysArray" :key="dia.name + '-' + slot">
                              <td v-if="getCell(gradeObj, dia, slot).cell" 
                                  :rowspan="getCell(gradeObj, dia, slot).cell.rowspan" 
                                  :class="['calendar-cell', getCell(gradeObj, dia, slot).conflict ? 'conflict' : '']">
                                <div class="calendar-item">
                                  <div class="calendar-item-title">{{ getCell(gradeObj, dia, slot).cell.item.course_name }}</div>
                                  <div class="calendar-item-meta">{{ getCell(gradeObj, dia, slot).cell.item.start_time }} - {{ getCell(gradeObj, dia, slot).cell.item.end_time }}</div>
                                </div>
                              </td>
                              <td v-else-if="!(gradeObj.skip[dia.index + '|' + slot] || gradeObj.skip[dia.name + '|' + slot])" 
                                  class="calendar-cell">
                              </td>
                            </template>
                          </tr>
                      </template>
                    </tbody>
                  </table>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<style scoped>
.calendar-table { width: 100%; border-collapse: collapse; }
.calendar-table th, .calendar-table td { border: 1px solid rgba(0,0,0,0.08); padding: 6px; vertical-align: top; }
.calendar-table thead th { background: rgba(0,0,0,0.03); text-align: left; }
.time-col { width: 96px; white-space: nowrap; }
.calendar-cell { min-height: 48px; }
.calendar-item { background: #E3F2FD; padding: 6px; border-radius: 4px; margin-bottom: 4px; }
.calendar-item-title { font-weight: 600; }
.calendar-item-meta { font-size: 0.8em; color: rgba(0,0,0,0.6); }

/* Texto preto apenas dentro dos blocos azuis claros */
.calendar-item, .calendar-item * {
  color: #000 !important;
}

.conflict { outline: 2px solid #ff5252; }
</style>