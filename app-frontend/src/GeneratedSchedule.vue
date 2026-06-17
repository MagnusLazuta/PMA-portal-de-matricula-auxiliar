<script setup>
import { onMounted, ref } from 'vue'
import axios from 'axios'
import { useTheme } from 'vuetify'

const theme = useTheme()

const props = defineProps({
  studentId: {
    type: Number,
    required: true
  },
  semester: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['back'])

const scheduleOptions = ref([])
const loading = ref(false)
const error = ref('')

// Calendar scale configurations (Google Calendar style)
const SCALE_Y = 1.2 // 1.2px per minute
const HOUR_HEIGHT = 60 * SCALE_Y // 72px per hour

const dayOrder = {
  'Segunda-feira': 1,
  'Terça-feira': 2,
  'Quarta-feira': 3,
  'Quinta-feira': 4,
  'Sexta-feira': 5,
  'Sábado': 6,
  'Domingo': 7,
}

const formatRoom = (room) => {
  if (!room) return ''
  return room
    .replace(/SALA DE AULA/gi, 'Sala')
    .replace(/ - Campus:.*$/gi, '')
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

const daysArray = Object.keys(dayOrder)
  .filter(d => d !== 'Domingo' && d !== 'Sábado')
  .map(d => ({ name: d, index: dayOrder[d] }))
  .sort((a, b) => a.index - b.index)

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

// Returns absolute coordinates and dimensions in pixels for the card, using the option's dynamic startHour
const getCardStyle = (item, startHour) => {
  const start = convertTimeToMinutes(item.start_time)
  const end = convertTimeToMinutes(item.end_time)
  const duration = Math.max(0, end - start)
  
  const startMinutes = startHour * 60
  const top = (start - startMinutes) * SCALE_Y
  const height = (duration * SCALE_Y) - 6 // Small visual gap for consecutive cards
  
  return {
    top: `${top}px`,
    height: `${height}px`,
    position: 'absolute',
    left: '4px',
    right: '4px',
    zIndex: 10
  }
}

// Checks if the current class has a schedule conflict with any other class
const getCellConflict = (items, currentItem) => {
  const currentStart = convertTimeToMinutes(currentItem.start_time)
  const currentEnd = convertTimeToMinutes(currentItem.end_time)
  
  return items.some(other => {
    // Skip comparison with itself
    if (other.id === currentItem.id || (other.course_code === currentItem.course_code && other.start_time === currentItem.start_time)) {
      return false
    }
    
    // Same column/day of the week
    if (normalizeDay(other.day_of_week) !== normalizeDay(currentItem.day_of_week)) {
      return false
    }
    
    const otherStart = convertTimeToMinutes(other.start_time)
    const otherEnd = convertTimeToMinutes(other.end_time)
    
    // Check overlap
    return currentStart < otherEnd && otherStart < currentEnd
  })
}

const loadSchedules = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await axios.post('http://127.0.0.1:8000/generate-schedules/ranked', {
      student_id: props.studentId,
      semester: props.semester
    }, { timeout: 10000 })
    
    const raw = Array.isArray(response.data) ? response.data : []
    scheduleOptions.value = raw.map((option, gi) => {
      const flatItems = []
      if (Array.isArray(option.schedule)) {
        option.schedule.forEach(section => {
          if (Array.isArray(section.schedules)) {
            section.schedules.forEach(sched => {
              flatItems.push({
                id: sched.id,
                section_id: section.section_id,
                section_code: section.section_code,
                course_name: section.course_name,
                course_code: section.course_code,
                professor_name: section.professor_name,
                day_of_week: sched.day_of_week,
                start_time: sched.start_time,
                end_time: sched.end_time,
                room: sched.room,
                all_schedules: section.schedules.map(s => ({
                  day_of_week: normalizeDay(s.day_of_week),
                  start_time: s.start_time,
                  end_time: s.end_time,
                  room: s.room
                }))
              })
            })
          }
        })
      }
      
      const sortedItems = sortSchedule(flatItems)
      
      // Find the minimum start time and maximum end time for this specific option
      let minStartMin = Infinity
      let maxEndMin = -Infinity
      
      sortedItems.forEach(item => {
        const start = convertTimeToMinutes(item.start_time)
        const end = convertTimeToMinutes(item.end_time)
        if (start < minStartMin) minStartMin = start
        if (end > maxEndMin) maxEndMin = end
      })
      
      // Dynamic definitions of schedules with margins
      let startHour = 8
      let endHour = 22
      
      if (minStartMin !== Infinity && maxEndMin !== -Infinity) {
        // Exact schedules rounded to the nearest hour (without a 1-hour margin)
        startHour = Math.max(0, Math.floor(minStartMin / 60))
        endHour = Math.min(23, Math.ceil(maxEndMin / 60))
      }
      
      // Group classes by day of the week
      const groupedByDay = {}
      daysArray.forEach(dia => {
        groupedByDay[dia.index] = []
      })
      
      sortedItems.forEach(item => {
        const rawDay = item.day_of_week
        const normalized = normalizeDay(rawDay)
        const dayIndex = dayOrder[normalized] || null
        if (dayIndex && groupedByDay[dayIndex]) {
          groupedByDay[dayIndex].push(item)
        }
      })
      
      return {
        items: sortedItems,
        groupedByDay,
        startHour,
        endHour,
        totalHeight: (endHour - startHour + 1) * HOUR_HEIGHT,
        score: option.score,
        selected_course_count: option.selected_course_count,
        total_course_priority: option.total_course_priority,
        matched_preference_count: option.matched_preference_count
      }
    })
  } catch (err) {
    console.error('Erro ao gerar grades:', err)
    const detalhe = err?.response?.data || err?.message || String(err)
    error.value = typeof detalhe === 'string' ? detalhe : JSON.stringify(detalhe)
    scheduleOptions.value = []
  } finally {
    loading.value = false
  }
}

const exportToPDF = (gradeObj, scheduleIndex) => {
  const startHour = gradeObj.startHour
  const endHour = gradeObj.endHour
  const totalHeight = gradeObj.totalHeight
  
  // 1. Generate the table rows for the summary (deduplicated by section_id)
  const uniqueSectionsMap = new Map()
  gradeObj.items.forEach(item => {
    if (!uniqueSectionsMap.has(item.section_id)) {
      uniqueSectionsMap.set(item.section_id, item)
    }
  })

  let tableRows = ''
  uniqueSectionsMap.forEach(item => {
    // Unique list of schedule blocks for this course
    const timesList = item.all_schedules.map(s => 
      `${s.day_of_week} das ${s.start_time.substring(0, 5)} às ${s.end_time.substring(0, 5)}${s.room ? ` (${formatRoom(s.room)})` : ''}`
    ).join('<br>')

    tableRows += `
      <tr>
        <td><strong>${item.course_name}</strong></td>
        <td>${item.course_code}</td>
        <td>${item.section_code}</td>
        <td>${item.professor_name || '—'}</td>
        <td>${timesList}</td>
      </tr>
    `
  })

  // 2. Generate the visual calendar days
  let calendarColumns = ''
  daysArray.forEach(dia => {
    let dayCards = ''
    const itemsForDay = gradeObj.groupedByDay[dia.index] || []
    
    itemsForDay.forEach(item => {
      const start = convertTimeToMinutes(item.start_time)
      const end = convertTimeToMinutes(item.end_time)
      const duration = Math.max(0, end - start)
      const startMinutes = startHour * 60
      const top = (start - startMinutes) * SCALE_Y
      const height = (duration * SCALE_Y) - 6
      const isConflict = getCellConflict(gradeObj.items, item)
      
      dayCards += `
        <div class="class-card ${isConflict ? 'conflict' : ''}" style="top: ${top}px; height: ${height}px;">
          <div class="class-card-title ${isConflict ? 'conflict' : ''}">${item.course_name}</div>
          <div class="class-card-details">Turma: ${item.section_code}</div>
          <div class="class-card-details">${item.start_time.substring(0, 5)} - ${item.end_time.substring(0, 5)}</div>
          ${item.room ? `<div class="class-card-details">${formatRoom(item.room)}</div>` : ''}
        </div>
      `
    })

    calendarColumns += `
      <div class="day-column">
        ${dayCards}
      </div>
    `
  })

  // 3. Generate background grid rows
  let gridRows = ''
  for (let h = startHour; h <= endHour; h++) {
    gridRows += `<div class="grid-hour-row" style="height: ${HOUR_HEIGHT}px;"></div>`
  }

  // 4. Generate time labels on the axis
  let timeLabels = ''
  for (let h = startHour; h <= endHour; h++) {
    timeLabels += `
      <div class="time-label-container" style="height: ${HOUR_HEIGHT}px;">
        <span class="time-label">${String(h).padStart(2, '0')}:00</span>
      </div>
    `
  }

  // Build the complete HTML document
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Grade de Horários - Opção ${scheduleIndex + 1}</title>
      <style>
        body {
          font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          color: #333;
          padding: 20px;
          margin: 0;
          background-color: #fff;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
        .header {
          text-align: center;
          margin-bottom: 20px;
          border-bottom: 2px solid #1976d2;
          padding-bottom: 10px;
        }
        .header h1 {
          font-size: 22px;
          color: #1976d2;
          margin: 0 0 5px 0;
        }
        .header p {
          margin: 0;
          color: #666;
          font-size: 13px;
        }
        .summary-title {
          font-size: 16px;
          font-weight: bold;
          margin: 20px 0 10px 0;
          color: #1976d2;
        }
        .summary-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 25px;
        }
        .summary-table th, .summary-table td {
          border: 1px solid #e0e0e0;
          padding: 8px 10px;
          text-align: left;
          font-size: 11px;
        }
        .summary-table th {
          background-color: #f5f5f5 !important;
          font-weight: bold;
        }
        
        /* Calendar layout */
        .calendar-container {
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          overflow: hidden;
          margin-top: 15px;
          display: flex;
          flex-direction: column;
          background-color: #fff;
        }
        .calendar-header {
          display: flex;
          background-color: #f5f5f5 !important;
          font-weight: bold;
          border-bottom: 1px solid #e0e0e0;
        }
        .time-axis-header {
          width: 60px;
          border-right: 1px solid #e0e0e0;
          flex-shrink: 0;
        }
        .day-header-col {
          flex: 1;
          text-align: center;
          padding: 8px 5px;
          font-size: 11px;
          border-right: 1px solid #e0e0e0;
        }
        .day-header-col:last-child {
          border-right: none;
        }
        .calendar-body {
          display: flex;
          position: relative;
        }
        .time-axis {
          width: 60px;
          border-right: 1px solid #e0e0e0;
          background-color: #fafafa !important;
          flex-shrink: 0;
        }
        .time-label-container {
          display: flex;
          justify-content: center;
          align-items: flex-start;
          padding-top: 2px;
          box-sizing: border-box;
        }
        .time-label {
          font-size: 9px;
          font-weight: bold;
          color: #666;
        }
        .grid-area {
          flex-grow: 1;
          position: relative;
        }
        .grid-lines-bg {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          pointer-events: none;
        }
        .grid-hour-row {
          border-bottom: 1px dashed #e0e0e0;
          box-sizing: border-box;
        }
        .grid-hour-row:last-child {
          border-bottom: none;
        }
        .columns-container {
          display: flex;
          position: relative;
          width: 100%;
        }
        .day-column {
          flex: 1;
          position: relative;
          height: 100%;
          border-right: 1px solid #e0e0e0;
          box-sizing: border-box;
        }
        .day-column:last-child {
          border-right: none;
        }
        .class-card {
          position: absolute;
          left: 4px;
          right: 4px;
          background-color: #e3f2fd !important;
          border: 1px solid #90caf9 !important;
          border-left: 4px solid #1976d2 !important;
          border-radius: 4px;
          padding: 5px;
          font-size: 9px;
          box-sizing: border-box;
          overflow: hidden;
          line-height: 1.2;
        }
        .class-card.conflict {
          background-color: #ffebee !important;
          border: 1px solid #ef9a9a !important;
          border-left: 4px solid #d32f2f !important;
        }
        .class-card-title {
          font-weight: bold;
          margin-bottom: 2px;
          color: #0d47a1 !important;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }
        .class-card-title.conflict {
          color: #b71c1c !important;
        }
        .class-card-details {
          color: #555;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          margin-top: 1px;
        }
        
        @media print {
          body {
            padding: 10px;
          }
          .no-print {
            display: none;
          }
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>UFRGS - Planejador de Grade Horária</h1>
        <p>Grade de Horários Gerada — Opção ${scheduleIndex + 1}</p>
      </div>

      <div class="summary-title">Resumo das Disciplinas</div>
      <table class="summary-table">
        <thead>
          <tr>
            <th>Disciplina</th>
            <th>Código</th>
            <th>Turma</th>
            <th>Professor</th>
            <th>Horários e Salas</th>
          </tr>
        </thead>
        <tbody>
          ${tableRows}
        </tbody>
      </table>

      <div style="page-break-inside: avoid; margin-top: 25px;">
        <div class="summary-title">Grade Semanal</div>
        <div class="calendar-container">
          <div class="calendar-header">
            <div class="time-axis-header"></div>
            ${daysArray.map(d => `<div class="day-header-col">${d.name}</div>`).join('')}
          </div>
          <div class="calendar-body">
            <div class="time-axis">
              ${timeLabels}
            </div>
            <div class="grid-area">
              <div class="grid-lines-bg">
                ${gridRows}
              </div>
              <div class="columns-container" style="height: ${totalHeight}px;">
                ${calendarColumns}
              </div>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
  `

  const printWindow = window.open('', '_blank')
  printWindow.document.write(htmlContent)
  printWindow.document.close()
  
  setTimeout(() => {
    printWindow.focus()
    printWindow.print()
  }, 250)
}

onMounted(() => {
  loadSchedules()
})
</script>

<template>
  <v-container>
    <v-card class="mx-auto rounded-xl shadow-premium" elevation="2">
      <v-card-title class="text-h5 font-weight-bold pa-6 d-flex align-center justify-space-between border-bottom">
        Grades de Horários Geradas
        <v-btn color="primary" variant="outlined" class="rounded-lg" @click="emit('back')">
          Voltar
        </v-btn>
      </v-card-title>

      <v-card-text class="pa-6">
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4 rounded-lg">
          <div>{{ error }}</div>
          <v-btn color="error" variant="flat" class="mt-3 rounded-lg" @click="loadSchedules">Tentar novamente</v-btn>
        </v-alert>

        <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-4 rounded-lg" />

        <div v-if="!loading && scheduleOptions.length === 0 && !error">
          <v-alert type="info" variant="tonal" class="rounded-lg">
            Nenhuma grade foi retornada pela API.
          </v-alert>
        </div>

        <v-row v-else>
          <v-col
            v-for="(gradeObj, scheduleIndex) in scheduleOptions"
            :key="scheduleIndex"
            cols="12"
          >
            <v-card variant="outlined" class="mb-6 rounded-xl border-thin">
              <v-card-title class="text-subtitle-1 font-weight-bold pa-4 d-flex justify-space-between align-center flex-wrap border-bottom">
                <span>Opção {{ scheduleIndex + 1 }}</span>
                <v-btn
                  color="primary"
                  variant="flat"
                  size="small"
                  prepend-icon="mdi-file-pdf-box"
                  class="rounded-lg font-weight-bold"
                  @click="exportToPDF(gradeObj, scheduleIndex)"
                >
                  Salvar PDF
                </v-btn>
              </v-card-title>

              <v-card-text class="pa-4">
                <div class="calendar-wrapper rounded-xl border-thin bg-surface">
                  <div class="calendar-container">
                    
                    <!-- Cabeçalho de Dias -->
                    <div class="calendar-header border-bottom">
                      <div class="time-axis-header"></div>
                      <div 
                        v-for="dia in daysArray" 
                        :key="dia.index" 
                        class="day-header-col"
                      >
                        {{ dia.name }}
                      </div>
                    </div>

                    <!-- Corpo do Calendário -->
                    <div class="calendar-body">
                      
                      <!-- Eixo do Tempo (Esquerda Dinâmica) -->
                      <div class="time-axis">
                        <div 
                          v-for="hour in (gradeObj.endHour - gradeObj.startHour + 1)" 
                          :key="hour"
                          class="time-label-container"
                          :style="{ height: `${HOUR_HEIGHT}px` }"
                        >
                          <span class="time-label">{{ String(gradeObj.startHour + hour - 1).padStart(2, '0') }}:00</span>
                        </div>
                      </div>

                      <!-- Área da Grade de Colunas (Direita) -->
                      <div class="grid-area">
                        
                        <!-- Linhas Horárias de Fundo -->
                        <div class="grid-lines-bg">
                          <div 
                            v-for="hour in (gradeObj.endHour - gradeObj.startHour + 1)" 
                            :key="hour"
                            class="grid-hour-row"
                            :style="{ height: `${HOUR_HEIGHT}px` }"
                          ></div>
                        </div>

                        <!-- Colunas dos Dias (Sobrepostas no Grid) -->
                        <div class="columns-container" :style="{ height: `${gradeObj.totalHeight}px` }">
                          <div 
                            v-for="dia in daysArray" 
                            :key="dia.index" 
                            class="day-column"
                          >
                            <!-- Cartões de Disciplinas Deste Dia -->
                            <v-card
                              v-for="item in gradeObj.groupedByDay[dia.index]"
                              :key="item.id || item.course_code + '-' + item.start_time"
                              variant="tonal"
                              :color="getCellConflict(gradeObj.items, item) ? 'error' : 'primary'"
                              class="pa-2 rounded-xl text-left class-card"
                              elevation="0"
                              :class="{ 'conflict-border': getCellConflict(gradeObj.items, item) }"
                              :style="getCardStyle(item, gradeObj.startHour)"
                            >
                              <div class="text-caption font-weight-bold card-title-clamp">
                                {{ item.course_name }}
                              </div>
                              <div class="text-caption opacity-90 card-text-clamp">
                                <strong>Turma:</strong> {{ item.section_code }}
                                <span v-if="item.professor_name"> | Prof: {{ item.professor_name }}</span>
                              </div>
                              <div class="text-caption opacity-80 card-text-clamp">
                                {{ item.start_time.substring(0, 5) }} - {{ item.end_time.substring(0, 5) }}
                                <span v-if="item.room"> | {{ formatRoom(item.room) }}</span>
                              </div>

                              <!-- Tooltip Interativa (Estilo Grade Curricular) -->
                              <v-tooltip
                                activator="parent"
                                location="top"
                                open-delay="200"
                                max-width="340"
                                :content-class="theme.global.name.value === 'dark' ? 'custom-node-tooltip tooltip-theme-dark' : 'custom-node-tooltip tooltip-theme-light'"
                                :theme="theme.global.name.value"
                              >
                                <div class="pa-2">
                                  <div class="text-subtitle-2 font-weight-bold border-bottom pb-1 mb-1">
                                    {{ item.course_name }}
                                  </div>
                                  <div class="text-caption mb-1">
                                    <strong>Código da Cadeira:</strong> {{ item.course_code }}
                                  </div>
                                  <div class="text-caption mb-1">
                                    <strong>Turma:</strong> {{ item.section_code }}
                                  </div>
                                  <div v-if="item.professor_name" class="text-caption mb-1">
                                    <strong>Professor:</strong> {{ item.professor_name }}
                                  </div>
                                  <div class="mt-2 pt-1 border-top-thin">
                                    <div class="text-caption font-weight-bold mb-1">Horários da Turma:</div>
                                    <ul class="pl-4 text-caption">
                                      <li v-for="sched in item.all_schedules" :key="sched.day_of_week + sched.start_time">
                                        {{ sched.day_of_week }}: {{ sched.start_time.substring(0, 5) }} - {{ sched.end_time.substring(0, 5) }}
                                        <span v-if="sched.room"> ({{ formatRoom(sched.room) }})</span>
                                      </li>
                                    </ul>
                                  </div>
                                </div>
                              </v-tooltip>
                            </v-card>
                          </div>
                        </div>

                      </div>
                    </div>

                  </div>
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
.shadow-premium {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
}

.border-bottom {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08) !important;
}

.border-thin {
  border: 1px solid rgba(var(--v-border-color), 0.08) !important;
}

.calendar-wrapper {
  overflow-x: auto;
}

.calendar-container {
  min-width: 850px;
  display: flex;
  flex-direction: column;
}

/* Cabeçalho */
.calendar-header {
  display: flex;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  font-weight: bold;
}

.time-axis-header {
  width: 75px;
  flex-shrink: 0;
  border-right: 1px solid rgba(var(--v-border-color), 0.08);
}

.day-header-col {
  flex: 1;
  text-align: center;
  padding: 14px 6px;
  color: rgb(var(--v-theme-on-surface));
  border-right: 1px solid rgba(var(--v-border-color), 0.08);
}

.day-header-col:last-child {
  border-right: none;
}

/* Corpo */
.calendar-body {
  display: flex;
  position: relative;
}

/* Eixo de Tempo */
.time-axis {
  width: 75px;
  flex-shrink: 0;
  border-right: 1px solid rgba(var(--v-border-color), 0.08);
  background-color: rgba(var(--v-theme-on-surface), 0.01);
  user-select: none;
}

.time-label-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 4px;
}

.time-label {
  font-size: 0.75rem;
  font-weight: bold;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Área de Grade */
.grid-area {
  flex-grow: 1;
  position: relative;
}

.grid-lines-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.grid-hour-row {
  border-bottom: 1px dashed rgba(var(--v-border-color), 0.08);
  box-sizing: border-box;
}

.grid-hour-row:last-child {
  border-bottom: none;
}

/* Colunas dos Dias */
.columns-container {
  display: flex;
  position: relative;
  width: 100%;
  z-index: 1;
}

.day-column {
  flex: 1;
  position: relative;
  height: 100%;
  border-right: 1px solid rgba(var(--v-border-color), 0.08);
  box-sizing: border-box;
}

.day-column:last-child {
  border-right: none;
}

/* Cartão da Aula */
.class-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  overflow: hidden;
  box-sizing: border-box;
}

.class-card:hover {
  transform: scale(1.02);
  z-index: 20 !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

.conflict-border {
  outline: 2px solid rgb(var(--v-theme-error)) !important;
}

.card-title-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}

.card-text-clamp {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.border-top-thin {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>

<style>
/* Estilos Globais da Tooltip (para funcionar com Teleport/v-overlay) */
.tooltip-theme-dark {
  backdrop-filter: blur(8px) !important;
  background-color: rgba(30, 30, 30, 0.98) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
}

.tooltip-theme-dark *:not(.text-success):not(.text-warning):not(.text-error):not(.text-info):not(.text-grey) {
  color: #ffffff !important;
}

.tooltip-theme-light {
  backdrop-filter: blur(8px) !important;
  background-color: rgba(255, 255, 255, 0.98) !important;
  color: #000000 !important;
  border: 1px solid rgba(0, 0, 0, 0.15) !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
}

.tooltip-theme-light *:not(.text-success):not(.text-warning):not(.text-error):not(.text-info):not(.text-grey) {
  color: #000000 !important;
}
</style>