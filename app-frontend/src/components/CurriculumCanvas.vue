<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useTheme } from 'vuetify'

// Importing local curriculum data (UFRGS) as backup and enrichment
import ufrgsData from '../ufrgs_data.json'
import { calculateSubjectStatuses } from '../composables/useCurriculumStatus'

const props = defineProps({
  studentId: {
    type: Number,
    default: 1
  }
})

// Reactive States
const rawSubjects = ref([])
const completedSubjectIds = ref([])
const loading = ref(false)
const usingFallback = ref(false)
const searchQuery = ref('')
const selectedSubjectId = ref(null)

// Edit Mode States
const isEditMode = ref(false)
const tempCompletedSubjectIds = ref([])
const pdfInputRef = ref(null)
const uploadingPdf = ref(false)

const theme = useTheme()

// Viewport and Canvas Elements
const viewportRef = ref(null)
const panX = ref(10)
const panY = ref(10)
const zoom = ref(0.7)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })

// Deterministic Grid Dimensions
const cardWidth = 260
const cardHeight = 115
const cardGap = 25
const cardStride = cardHeight + cardGap // 140px

const columnWidth = 260
const columnGap = 60
const columnStride = columnWidth + columnGap // 320px

const marginX = 50
const marginY = 80

// 1. Process local data from ufrgs_data.json
const localSubjectsMap = computed(() => {
  const map = {}
  if (!ufrgsData || !ufrgsData.curriculum) return map

  ufrgsData.curriculum.forEach(item => {
    const semesterNum = parseInt(item.etapa.replace(/\D/g, '')) || 1
    const prereqCodes = (item.pre_requisitos || [])
      .filter(pre => !pre.startsWith('Créditos'))
      .map(pre => pre.split(' - ')[0].trim())

    // The TCC in the original curriculum file has an empty code ("").
    // We assign the code "TCC" to ensure correct identification and reactivity.
    const code = item.codigo === "" ? "TCC" : item.codigo

    map[code] = {
      id: code,
      code: code,
      name: item.nome,
      semester: semesterNum,
      carga_horaria: parseInt(item.carga_horaria) || (parseInt(item.creditos) * 15),
      credits: parseInt(item.creditos),
      prerequisites: prereqCodes
    }
  })
  return map
})

// 2. Load Backend Data with Fallback
const loadData = async () => {
  loading.value = true
  usingFallback.value = false
  try {
    const coursesRes = await axios.get(`http://localhost:8000/students/${props.studentId}/curriculum`)
    const completedRes = await axios.get(`http://localhost:8000/students/${props.studentId}/completed-courses`)

    const backendCourses = coursesRes.data || []
    const backendCompleted = completedRes.data || []

    completedSubjectIds.value = backendCompleted.map(c => c.code === "" ? "TCC" : c.code)

    rawSubjects.value = backendCourses.map(course => {
      const code = course.code === "" ? "TCC" : course.code
      const localMeta = localSubjectsMap.value[code] || {}
      const prereqCodes = (course.prerequisites || []).map(p => p.code === "" ? "TCC" : p.code)

      return {
        id: code,
        code: code,
        dbId: course.id, // Preserve database numerical ID
        name: course.name || localMeta.name,
        semester: course.semester || localMeta.semester || 1,
        carga_horaria: (course.credits * 15) || localMeta.carga_horaria,
        credits: course.credits || localMeta.credits,
        prerequisites: prereqCodes.length > 0 ? prereqCodes : (localMeta.prerequisites || [])
      }
    })

  } catch (err) {
    console.warn('Erro ao conectar com o backend. Usando dados locais (fallback):', err)
    usingFallback.value = true
    rawSubjects.value = Object.values(localSubjectsMap.value)
    // Default completed selector for local simulation
    completedSubjectIds.value = ['INF01202', 'MAT01353', 'INF01087', 'INF05508']
  } finally {
    loading.value = false
    setupLayout()
  }
}

// Edit Mode control functions
const startEditing = () => {
  isEditMode.value = true
  tempCompletedSubjectIds.value = [...completedSubjectIds.value]
}

const cancelEditing = () => {
  isEditMode.value = false
  tempCompletedSubjectIds.value = []
  // Restore original visual statuses of subjects
  updateGridStatuses(completedSubjectIds.value)
}

const saveCompletions = async () => {
  loading.value = true
  try {
    if (usingFallback.value) {
      completedSubjectIds.value = [...tempCompletedSubjectIds.value]
      isEditMode.value = false
      return
    }

    // Map completed course codes to their database IDs
    const completedIds = tempCompletedSubjectIds.value
      .map(code => {
        const subject = rawSubjects.value.find(s => s.code === code)
        return subject ? subject.dbId : null
      })
      .filter(id => id !== null && id !== undefined)

    await axios.post(`http://localhost:8000/students/${props.studentId}/completed-courses`, completedIds)

    completedSubjectIds.value = [...tempCompletedSubjectIds.value]
    isEditMode.value = false
  } catch (error) {
    console.error('Erro ao salvar conclusões no backend:', error)
    alert('Erro ao salvar as disciplinas concluídas.')
  } finally {
    loading.value = false
  }
}

const triggerPdfUpload = () => {
  if (pdfInputRef.value) {
    pdfInputRef.value.click()
  }
}

const handlePdfUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // Reset input file value to allow uploading same file
  event.target.value = ''

  uploadingPdf.value = true
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(
      `http://localhost:8000/students/${props.studentId}/completed-courses/upload-pdf`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )

    const completedCourses = response.data || []
    completedSubjectIds.value = completedCourses.map(c => c.code === "" ? "TCC" : c.code)

    updateGridStatuses(completedSubjectIds.value)
    alert('Histórico processado com sucesso! Disciplinas concluídas atualizadas.')
  } catch (error) {
    console.error('Erro ao enviar o PDF:', error)
    const errorMsg = error.response?.data?.detail || 'Erro ao carregar e processar o arquivo PDF.'
    alert(errorMsg)
  } finally {
    uploadingPdf.value = false
    loading.value = false
  }
}

const updateGridStatuses = (completedList) => {
  const statuses = calculateSubjectStatuses(rawSubjects.value, completedList)
  subjectsWithCoords.value = subjectsWithCoords.value.map(s => ({
    ...s,
    status: statuses[s.id] || 'blocked'
  }))
}

const toggleSubjectCompletion = (subject) => {
  const code = subject.code
  const isCompleted = tempCompletedSubjectIds.value.includes(code)

  if (isCompleted) {
    // Just unmark the clicked course
    tempCompletedSubjectIds.value = tempCompletedSubjectIds.value.filter(c => c !== code)
  } else {
    // Just mark the clicked course as completed
    tempCompletedSubjectIds.value.push(code)
  }

  // Update grid visual in real time
  updateGridStatuses(tempCompletedSubjectIds.value)
}


// 3. Subject Layout Structuring (Columns and Rows)
const subjectsWithCoords = ref([])
const maxSemester = ref(8)
const maxRowsCount = ref(6)

const setupLayout = () => {
  if (rawSubjects.value.length === 0) return

  // Calculate academic status of each subject
  const statuses = calculateSubjectStatuses(rawSubjects.value, completedSubjectIds.value)

  // Group subjects by semester
  const semestersGroups = {}
  let maxSem = 1

  rawSubjects.value.forEach(subject => {
    const sem = subject.semester || 1
    if (sem > maxSem) maxSem = sem
    if (!semestersGroups[sem]) semestersGroups[sem] = []
    semestersGroups[sem].push(subject)
  })

  maxSemester.value = maxSem

  let maxRows = 0
  const tempSubjects = []

  // Calculate deterministic mathematical coordinates for each subject
  Object.keys(semestersGroups).forEach(semKey => {
    const sem = parseInt(semKey)
    const list = semestersGroups[sem]
    if (list.length > maxRows) maxRows = list.length

    list.forEach((subject, rowIndex) => {
      const x = (sem - 1) * columnStride + marginX
      const y = rowIndex * cardStride + marginY

      tempSubjects.push({
        ...subject,
        status: statuses[subject.id] || 'blocked',
        x,
        y,
        col: sem - 1,
        row: rowIndex,
        isHighlighted: false,
        isDimmed: false
      })
    })
  })

  maxRowsCount.value = maxRows
  subjectsWithCoords.value = tempSubjects

  // Center the graph at start
  setTimeout(() => {
    handleFitView()
  }, 150)
}

// Virtual total dimensions of canvas
const canvasWidth = computed(() => maxSemester.value * columnStride + marginX + 100)
const canvasHeight = computed(() => maxRowsCount.value * cardStride + marginY + 50)

// 4. SVG Prerequisite Connections
const connections = computed(() => {
  const list = []
  subjectsWithCoords.value.forEach(target => {
    const prereqs = target.prerequisites || []
    prereqs.forEach(prereqId => {
      const source = subjectsWithCoords.value.find(s => s.code === prereqId || s.id === prereqId)
      if (source) {
        // Output position (middle-right border of prerequisite card)
        const x1 = source.x + cardWidth
        const y1 = source.y + cardHeight / 2

        // Input position (middle-left border of dependent card)
        const x2 = target.x
        const y2 = target.y + cardHeight / 2

        // If semester difference is greater than 1, we bypass other courses
        // to avoid overlapping intermediate cards.
        let path = ''
        const deltaCol = target.col - source.col
        
        if (deltaCol > 1) {
          // Orthogonal bypass with rounded corners (Q Bezier)
          // Vertical channel right after source:
          const x_chan1 = x1 + 30
          // Vertical channel right before target:
          const x_chan2 = x2 - 30
          
          // Canal horizontal (folga entre as linhas):
          // We use the gap below source.row if source.row <= target.row,
          // or the gap above source.row if source.row > target.row.
          const gapIndex = source.row > target.row ? source.row - 1 : source.row
          const y_chan = gapIndex * cardStride + marginY + cardHeight + cardGap / 2
          
          const R = 12 // Raio das curvas
          const dirY = y_chan > y1 ? 1 : -1
          const dirY2 = y2 > y_chan ? 1 : -1
          
          path = `M ${x1} ${y1} ` +
                 `L ${x_chan1 - R} ${y1} ` +
                 `Q ${x_chan1} ${y1}, ${x_chan1} ${y1 + dirY * R} ` +
                 `L ${x_chan1} ${y_chan - dirY * R} ` +
                 `Q ${x_chan1} ${y_chan}, ${x_chan1 + R} ${y_chan} ` +
                 `L ${x_chan2 - R} ${y_chan} ` +
                 `Q ${x_chan2} ${y_chan}, ${x_chan2} ${y_chan + dirY2 * R} ` +
                 `L ${x_chan2} ${y2 - dirY2 * R} ` +
                 `Q ${x_chan2} ${y2}, ${x_chan2 + R} ${y2} ` +
                 `L ${x2} ${y2}`
        } else {
          // Curva Bezier cúbica suave original (vizinho direto)
          const controlOffset = 50
          const cp1x = x1 + controlOffset
          const cp1y = y1
          const cp2x = x2 - controlOffset
          const cp2y = y2
          path = `M ${x1} ${y1} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`
        }

        list.push({
          id: `${source.id}-${target.id}`,
          sourceId: source.id,
          targetId: target.id,
          path
        })
      }
    })
  })
  return list
})

// Encontra recursivamente pré-requisitos (ancestrais)
const getPredecessors = (subjectId, visited = new Set()) => {
  const current = subjectsWithCoords.value.find(s => s.id === subjectId)
  if (!current) return visited

  const prereqs = current.prerequisites || []
  prereqs.forEach(pid => {
    const parent = subjectsWithCoords.value.find(s => s.code === pid || s.id === pid)
    if (parent && !visited.has(parent.id)) {
      visited.add(parent.id)
      getPredecessors(parent.id, visited)
    }
  })
  return visited
}

// Recursively find dependent courses (successors)
const getSuccessors = (subjectId, visited = new Set()) => {
  subjectsWithCoords.value.forEach(candidate => {
    const prereqs = candidate.prerequisites || []
    const isDependent = prereqs.some(pid => pid === subjectId || (subjectsWithCoords.value.find(s => s.id === subjectId)?.code === pid))
    
    if (isDependent && !visited.has(candidate.id)) {
      visited.add(candidate.id)
      getSuccessors(candidate.id, visited)
    }
  })
  return visited
}

// Update highlights & dimming based on search and selection
const activeConnections = ref([])

const updateHighlights = () => {
  const search = searchQuery.value.trim().toLowerCase()
  const selectedId = selectedSubjectId.value

  activeConnections.value = []

  // If nothing is selected or searched, clear effects
  if (!search && !selectedId) {
    subjectsWithCoords.value.forEach(s => {
      s.isHighlighted = false
      s.isDimmed = false
    })
    return
  }

  let relatedNodes = new Set()
  let prereqCodes = new Set()

  if (selectedId) {
    relatedNodes.add(selectedId)
    const selectedSubject = subjectsWithCoords.value.find(s => s.id === selectedId)
    if (selectedSubject && selectedSubject.prerequisites) {
      selectedSubject.prerequisites.forEach(code => {
        prereqCodes.add(code.toLowerCase())
      })
    }
  }

  // Update subject card states
  subjectsWithCoords.value.forEach(s => {
    const matchesSearch = !search || s.code.toLowerCase().includes(search) || s.name.toLowerCase().includes(search)

    if (selectedId) {
      const isPrereq = prereqCodes.has(s.code.toLowerCase()) || prereqCodes.has(s.id.toLowerCase())
      const isSelected = s.id === selectedId
      const isRelated = isSelected || isPrereq
      s.isHighlighted = isRelated && matchesSearch
      s.isDimmed = !isRelated || !matchesSearch
    } else {
      s.isHighlighted = matchesSearch
      s.isDimmed = !matchesSearch
    }
  })

  // Identifica conexões SVG que devem ser destacadas (apenas as que entram na matéria selecionada)
  connections.value.forEach(conn => {
    const isDirectPrereqEdge = selectedId && conn.targetId === selectedId

    if (isDirectPrereqEdge) {
      activeConnections.value.push(conn.id)
    }
  })
}

// 5. Drag (Pan) and Scroll (Zoom) Handlers
const onMouseDown = (e) => {
  // Only left mouse button activates drag
  if (e.button !== 0) return
  isDragging.value = true
  dragStart.value = { x: e.clientX - panX.value, y: e.clientY - panY.value }
  viewportRef.value.style.cursor = 'grabbing'
}

const onMouseMove = (e) => {
  if (!isDragging.value) return
  panX.value = e.clientX - dragStart.value.x
  panY.value = e.clientY - dragStart.value.y
}

const onMouseUp = () => {
  isDragging.value = false
  if (viewportRef.value) {
    viewportRef.value.style.cursor = 'grab'
  }
}

const onTouchStart = (e) => {
  if (e.touches.length !== 1) return
  isDragging.value = true
  const touch = e.touches[0]
  dragStart.value = { x: touch.clientX - panX.value, y: touch.clientY - panY.value }
}

const onTouchMove = (e) => {
  if (!isDragging.value || e.touches.length !== 1) return
  const touch = e.touches[0]
  panX.value = touch.clientX - dragStart.value.x
  panY.value = touch.clientY - dragStart.value.y
}

const onTouchEnd = () => {
  isDragging.value = false
}

const onWheel = (e) => {
  e.preventDefault()
  const zoomFactor = 1.08
  let newZoom = zoom.value
  
  if (e.deltaY < 0) {
    newZoom = Math.min(newZoom * zoomFactor, 2.0)
  } else {
    newZoom = Math.max(newZoom / zoomFactor, 0.3)
  }

  // Zoom centralizado aproximado
  const rect = viewportRef.value.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  const canvasMouseX = (mouseX - panX.value) / zoom.value
  const canvasMouseY = (mouseY - panY.value) / zoom.value

  zoom.value = newZoom
  panX.value = mouseX - canvasMouseX * newZoom
  panY.value = mouseY - canvasMouseY * newZoom
}

// Zoom and Center buttons
const handleZoomIn = () => {
  zoom.value = Math.min(zoom.value * 1.2, 2.0)
}

const handleZoomOut = () => {
  zoom.value = Math.max(zoom.value / 1.2, 0.3)
}

const handleFitView = () => {
  if (!viewportRef.value) return
  const vWidth = viewportRef.value.clientWidth
  const vHeight = viewportRef.value.clientHeight

  const scaleX = vWidth / canvasWidth.value
  const scaleY = vHeight / canvasHeight.value
  const newZoom = Math.max(0.3, Math.min(scaleX, scaleY) * 0.9)

  zoom.value = newZoom
  panX.value = (vWidth - canvasWidth.value * newZoom) / 2
  panY.value = (vHeight - canvasHeight.value * newZoom) / 2
}

const selectSubject = (id) => {
  if (selectedSubjectId.value === id) {
    selectedSubjectId.value = null // Deseleciona
  } else {
    selectedSubjectId.value = id
  }
}

const clearSelection = (e) => {
  // Clear only if clicking on empty canvas background
  if (e.target.classList.contains('canvas-background') || e.target.classList.contains('canvas-grid')) {
    selectedSubjectId.value = null
  }
}

// Watchers
watch([searchQuery, selectedSubjectId], () => {
  updateHighlights()
})

watch(() => props.studentId, () => {
  loadData()
})

onMounted(() => {
  loadData()
})

// Academic status colors
const getStatusConfig = (status) => {
  switch (status) {
    case 'completed':
      return { color: 'success', icon: 'mdi-check-circle', border: 'rgba(76, 175, 80, 0.6)', bg: 'bg-emerald', badge: 'Concluída' }
    case 'available':
      return { color: 'warning', icon: 'mdi-star-circle', border: 'rgba(251, 192, 45, 0.7)', bg: 'bg-amber', badge: 'Disponível' }
    case 'blocked':
    default:
      return { color: 'error', icon: 'mdi-lock-outline', border: 'rgba(244, 67, 54, 0.5)', bg: 'bg-error-suttle', badge: 'Bloqueada' }
  }
}

// Carga horária
const getWorkload = (s) => {
  return s.carga_horaria ? `${s.carga_horaria}h` : `${(s.credits || 4) * 15}h`
}

// MiniMap coordinates for the visible viewport rectangle
const miniMapScale = computed(() => {
  return Math.min(180 / canvasWidth.value, 110 / canvasHeight.value)
})

const miniViewportRect = computed(() => {
  if (!viewportRef.value) return { x: 0, y: 0, w: 0, h: 0 }
  const vWidth = viewportRef.value.clientWidth
  const vHeight = viewportRef.value.clientHeight
  
  return {
    x: Math.max(0, -panX.value / zoom.value),
    y: Math.max(0, -panY.value / zoom.value),
    w: Math.min(canvasWidth.value, vWidth / zoom.value),
    h: Math.min(canvasHeight.value, vHeight / zoom.value)
  }
})
</script>

<template>
  <v-container fluid class="pa-0 fill-height d-flex flex-column">
    <!-- Toolbar -->
    <v-card class="mx-4 mt-2 mb-4 pa-4 rounded-xl shadow-premium" elevation="2">
      <v-row align="center" no-gutters>
        <!-- Legenda -->
        <v-col cols="12" md="6" class="d-flex flex-wrap align-center justify-start gap-4 mb-3 mb-md-0">
          <div class="d-flex align-center mr-4">
            <span class="legend-color legend-completed mr-2"></span>
            <span class="text-caption font-weight-medium">Concluída</span>
          </div>
          <div class="d-flex align-center mr-4">
            <span class="legend-color legend-available mr-2"></span>
            <span class="text-caption font-weight-medium">Disponível</span>
          </div>
          <div class="d-flex align-center mr-4">
            <span class="legend-color legend-blocked mr-2"></span>
            <span class="text-caption font-weight-medium">Bloqueada</span>
          </div>
        </v-col>

        <!-- Controles extras -->
        <v-col cols="12" md="6" class="d-flex justify-md-end justify-start align-center gap-2 flex-wrap">
          <v-btn-group variant="outlined" density="compact" class="rounded-lg mr-2">
            <v-btn icon="mdi-plus" @click="handleZoomIn" title="Aumentar Zoom"></v-btn>
            <v-btn icon="mdi-minus" @click="handleZoomOut" title="Diminuir Zoom"></v-btn>
          </v-btn-group>
          <v-btn
            color="secondary"
            variant="outlined"
            prepend-icon="mdi-image-filter-center-focus"
            class="rounded-lg font-weight-medium mr-2"
            @click="handleFitView"
          >
            Ajustar
          </v-btn>

          <!-- Edit Mode Buttons -->
          <input
            type="file"
            ref="pdfInputRef"
            accept=".pdf"
            class="d-none"
            @change="handlePdfUpload"
          />
          <v-btn
            v-if="!isEditMode"
            color="red-darken-2"
            variant="flat"
            prepend-icon="mdi-file-pdf-box"
            class="rounded-lg font-weight-medium text-none mr-2"
            @click="triggerPdfUpload"
            :loading="uploadingPdf"
          >
            Carregar Histórico (PDF)
          </v-btn>
          <v-btn
            v-if="!isEditMode"
            color="primary"
            variant="flat"
            prepend-icon="mdi-pencil"
            class="rounded-lg font-weight-medium text-none"
            @click="startEditing"
          >
            Editar
          </v-btn>
          <template v-else>
            <v-btn
              color="success"
              variant="flat"
              prepend-icon="mdi-check"
              class="rounded-lg font-weight-medium mr-1"
              @click="saveCompletions"
            >
              Salvar
            </v-btn>
            <v-btn
              color="grey"
              variant="outlined"
              prepend-icon="mdi-close"
              class="rounded-lg font-weight-medium"
              @click="cancelEditing"
            >
              Cancelar
            </v-btn>
          </template>
        </v-col>
      </v-row>
    </v-card>

    <!-- Main Viewport Container -->
    <v-row class="flex-grow-1 mx-4 mb-4 fill-height relative" no-gutters>
      <!-- Loading Overlay -->
      <v-overlay
        :model-value="loading"
        class="align-center justify-center rounded-xl"
        contained
        persistent
      >
        <v-progress-circular color="primary" indeterminate size="64"></v-progress-circular>
      </v-overlay>

      <v-col cols="12" class="fill-height">
        <v-card class="canvas-viewport fill-height rounded-xl overflow-hidden d-flex" elevation="2">
          
          <!-- Viewport (Área visível) -->
          <div 
            ref="viewportRef"
            class="viewport-container flex-grow-1 relative"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @mouseleave="onMouseUp"
            @touchstart="onTouchStart"
            @touchmove="onTouchMove"
            @touchend="onTouchEnd"
            @wheel="onWheel"
            @click="clearSelection"
          >
            <!-- Dica flutuante -->
            <div 
              v-if="!isEditMode" 
              class="floating-tip px-3 py-1.5 rounded-lg text-caption font-weight-medium shadow-premium"
            >
              <v-icon size="14" class="mr-1">mdi-gesture-tap</v-icon>
              Dica: Clique em uma disciplina para ver conexões. Arraste para mover, scroll para Zoom.
            </div>

            <!-- Active Edit Mode Banner -->
            <div 
              v-else 
              class="floating-edit-banner px-4 py-2 rounded-lg text-caption font-weight-bold shadow-premium bg-warning-suttle border-warning"
            >
              <v-icon size="16" color="warning" class="mr-2 animate-pulse">mdi-pencil-circle</v-icon>
              Modo Edição Ativo: Clique nas disciplinas para marcar/desmarcar como concluídas. Não esqueça de Salvar!
            </div>


            <!-- Canvas (Infinite Surface with Transform) -->
            <div 
              class="canvas-background"
              :style="{
                width: `${canvasWidth}px`,
                height: `${canvasHeight}px`,
                transform: `translate(${panX}px, ${panY}px) scale(${zoom})`
              }"
            >
              <!-- Background Dotted Grid -->
              <div class="canvas-grid"></div>

              <!-- Connections Layer (SVG) -->
              <svg class="svg-connections-layer" :width="canvasWidth" :height="canvasHeight">
                <defs>
                  <!-- Seta direcional padrão -->
                  <marker
                    id="arrow-default"
                    viewBox="0 0 10 10"
                    refX="6"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#9E9E9E" />
                  </marker>
                  <!-- Seta direcional destacada (Active) -->
                  <marker
                    id="arrow-active"
                    viewBox="0 0 10 10"
                    refX="6"
                    refY="5"
                    markerWidth="6"
                    markerHeight="6"
                    orient="auto-start-reverse"
                  >
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="rgb(var(--v-theme-primary))" />
                  </marker>
                </defs>

                <!-- Linhas ativas (Destaques ao selecionar) -->
                <path
                  v-for="conn in connections.filter(c => activeConnections.includes(c.id))"
                  :key="`fg-${conn.id}`"
                  :d="conn.path"
                  fill="none"
                  stroke="rgb(var(--v-theme-primary))"
                  stroke-width="3"
                  class="active-path"
                  marker-end="url(#arrow-active)"
                />
              </svg>

              <!-- Semester Column Headers -->
              <div
                v-for="s in maxSemester"
                :key="`head-${s}`"
                class="semester-header text-uppercase font-weight-bold text-primary"
                :style="{
                  left: `${(s - 1) * columnStride + marginX}px`,
                  top: `${marginY - 50}px`,
                  width: `${columnWidth}px`
                }"
              >
                {{ s }}º Semestre
              </div>

              <!-- Subject Cards (Grid Nodes) -->
              <div
                v-for="s in subjectsWithCoords"
                :key="s.id"
                class="subject-card-wrapper"
                :class="{
                  'is-dimmed': s.isDimmed,
                  'is-highlighted': s.isHighlighted || selectedSubjectId === s.id
                }"
                :style="{
                  left: `${s.x}px`,
                  top: `${s.y}px`,
                  width: `${cardWidth}px`,
                  height: `${cardHeight}px`
                }"
                @click.stop="isEditMode ? toggleSubjectCompletion(s) : selectSubject(s.id)"
              >
                <!-- Vuetify Card -->
                <v-card
                  variant="outlined"
                  class="subject-inner-card d-flex flex-column justify-space-between text-left fill-height"
                  :class="[
                    getStatusConfig(s.status).borderClass, 
                    getStatusConfig(s.status).bg,
                    selectedSubjectId === s.id ? 'active-border' : ''
                  ]"
                  :style="{
                    borderColor: selectedSubjectId === s.id ? 'rgb(var(--v-theme-primary))' : getStatusConfig(s.status).border,
                    borderWidth: selectedSubjectId === s.id ? '3px' : '2px'
                  }"
                  elevation="0"
                >
                  <div class="px-3 pt-2 d-flex justify-space-between align-center">
                    <span class="text-caption font-weight-bold text-mono subject-code">{{ s.code }}</span>
                    <v-chip
                      size="x-small"
                      variant="flat"
                      :color="getStatusConfig(s.status).color"
                      class="font-weight-bold"
                    >
                      {{ getStatusConfig(s.status).badge }}
                    </v-chip>
                  </div>

                  <div class="px-3 py-1 flex-grow-1 d-flex align-center">
                    <span class="text-body-2 font-weight-medium line-clamp-2 leading-tight w-100 subject-title">
                      {{ s.name }}
                    </span>
                  </div>

                  <div class="px-3 pb-2 d-flex justify-space-between align-center border-top-thin">
                    <div class="d-flex align-center">
                      <v-icon size="14" class="mr-1 text-medium-emphasis subject-workload-icon">mdi-clock-outline</v-icon>
                      <span class="text-caption text-medium-emphasis subject-workload">{{ getWorkload(s) }}</span>
                    </div>
                    <div class="d-flex align-center">
                      <v-icon size="14" :color="getStatusConfig(s.status).color" class="mr-1">
                        {{ getStatusConfig(s.status).icon }}
                      </v-icon>
                      <span class="text-caption font-weight-bold subject-semester">{{ s.semester }}º Sem.</span>
                    </div>
                  </div>
                </v-card>

                <!-- Tooltip Interativa -->
                <v-tooltip
                  activator="parent"
                  location="top"
                  open-delay="200"
                  max-width="320"
                  :content-class="theme.global.name.value === 'dark' ? 'custom-node-tooltip tooltip-theme-dark' : 'custom-node-tooltip tooltip-theme-light'"
                  :theme="theme.global.name.value"
                >
                  <div class="pa-2">
                    <div class="text-subtitle-2 font-weight-bold border-bottom pb-1 mb-1">
                      {{ s.name }}
                    </div>
                    <div class="text-caption mb-1">
                      <strong>Código:</strong> {{ s.code }}
                    </div>
                    <div class="text-caption mb-1">
                      <strong>Semestre Recomendado:</strong> {{ s.semester }}º
                    </div>
                    <div class="text-caption mb-1">
                      <strong>Créditos:</strong> {{ s.credits || 4 }}
                    </div>
                    <div class="text-caption mb-1">
                      <strong>Carga Horária:</strong> {{ getWorkload(s) }}
                    </div>
                    <div class="text-caption">
                      <strong>Situação:</strong> 
                      <span :class="`text-${getStatusConfig(s.status).color} font-weight-bold`">&nbsp;{{ getStatusConfig(s.status).badge }}</span>
                    </div>

                    <div v-if="s.prerequisites && s.prerequisites.length" class="mt-2 pt-1 border-top-thin">
                      <div class="text-caption font-weight-bold mb-1">Pré-requisitos:</div>
                      <ul class="pl-4 text-caption">
                        <li v-for="prereq in s.prerequisites" :key="prereq">
                          {{ prereq }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </v-tooltip>
              </div>

            </div>

            <!-- MINI MAP CUSTOMIZADO (SVG Reativo) -->
            <div class="minimap-container shadow-premium d-none d-sm-block">
              <svg :width="180" :height="110" :viewBox="`0 0 ${canvasWidth} ${canvasHeight}`">
                <!-- Mini Rows (Displayed only under selection) -->
                <path
                  v-for="conn in connections.filter(c => activeConnections.includes(c.id))"
                  :key="`mini-${conn.id}`"
                  :d="conn.path"
                  fill="none"
                  stroke="rgb(var(--v-theme-primary))"
                  stroke-width="15"
                  opacity="1.0"
                />

                <!-- Mini Cards -->
                <rect
                  v-for="s in subjectsWithCoords"
                  :key="`mini-${s.id}`"
                  :x="s.x"
                  :y="s.y"
                  :width="cardWidth"
                  :height="cardHeight"
                  rx="20"
                  ry="20"
                  :fill="s.status === 'completed' ? '#4CAF50' : s.status === 'available' ? '#FBC02D' : '#F44336'"
                  :opacity="s.isDimmed ? 0.3 : 0.8"
                  :stroke="selectedSubjectId === s.id ? 'rgb(var(--v-theme-primary))' : 'none'"
                  :stroke-width="selectedSubjectId === s.id ? 20 : 0"
                />

                <!-- Visible Viewport Border -->
                <rect
                  :x="miniViewportRect.x"
                  :y="miniViewportRect.y"
                  :width="miniViewportRect.w"
                  :height="miniViewportRect.h"
                  fill="rgba(var(--v-theme-primary), 0.08)"
                  stroke="rgb(var(--v-theme-primary))"
                  stroke-width="12"
                  rx="10"
                  ry="10"
                />
              </svg>
            </div>

          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.fill-height {
  height: 100% !important;
}

.relative {
  position: relative;
}

.shadow-premium {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
}

.gap-4 {
  gap: 16px;
}

/* Viewport and Canvas Styles */
.canvas-viewport {
  border: 1px solid rgba(var(--v-border-color), 0.1);
  height: 650px !important;
  min-height: 500px;
}

.viewport-container {
  width: 100%;
  height: 100%;
  background-color: rgb(var(--v-theme-background));
  overflow: hidden;
  cursor: grab;
}

.canvas-background {
  position: absolute;
  transform-origin: 0 0;
  transition: transform 0.05s ease-out;
}

/* Dotted Grid in CSS */
.canvas-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: radial-gradient(rgba(var(--v-border-color), 0.15) 1.5px, transparent 1.5px);
  background-size: 24px 24px;
  pointer-events: none;
}

.svg-connections-layer {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
  z-index: 1;
}

/* Estilo dos cabeçalhos dos semestres */
.semester-header {
  position: absolute;
  text-align: center;
  font-size: 1.1rem;
  letter-spacing: 1px;
  border-bottom: 2px solid rgba(var(--v-theme-primary), 0.2);
  padding-bottom: 8px;
  pointer-events: none;
  color: rgb(var(--v-theme-primary)) !important;
}

/* Posicionamento Absoluto dos Cards */
.subject-card-wrapper {
  position: absolute;
  z-index: 2;
  transition: opacity 0.3s ease, transform 0.2s ease, filter 0.3s ease;
}

.subject-card-wrapper:hover {
  transform: scale(1.03);
  z-index: 10 !important;
}

.subject-inner-card {
  border-radius: 12px !important;
  background-color: rgb(var(--v-theme-surface)) !important;
  color: rgb(var(--v-theme-on-surface)) !important;
  border-width: 2px !important;
  transition: all 0.25s ease;
  overflow: hidden;
}

/* Status and Highlight Modifiers */
.is-dimmed {
  opacity: 0.35;
  filter: grayscale(40%) blur(0.2px);
}

.is-highlighted {
  transform: scale(1.02);
  z-index: 8 !important;
}

/* Subtle Background Modifiers */
.bg-emerald {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(76, 175, 80, 0.02) 100%) !important;
}
.bg-amber {
  background: linear-gradient(135deg, rgba(251, 192, 45, 0.05) 0%, rgba(251, 192, 45, 0.02) 100%) !important;
}
.bg-error-suttle {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.05) 0%, rgba(244, 67, 54, 0.02) 100%) !important;
}

/* Glow effect for active elements */
.active-border {
  box-shadow: 0 0 12px rgba(var(--v-theme-primary), 0.4) !important;
}

.is-highlighted .subject-inner-card {
  box-shadow: 0 4px 15px rgba(var(--v-theme-primary), 0.1) !important;
}

/* Active Arrow with Dashed Animation */
.active-path {
  stroke-dasharray: 8;
  animation: dash 20s linear infinite;
  filter: drop-shadow(0px 0px 3px rgba(var(--v-theme-primary), 0.5));
}

@keyframes dash {
  to {
    stroke-dashoffset: -1000;
  }
}

/* Legend elements */
.legend-color {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 4px;
}

.legend-completed {
  background-color: #4CAF50;
  box-shadow: 0 0 5px rgba(76, 175, 80, 0.4);
}

.legend-available {
  background-color: #FBC02D;
  box-shadow: 0 0 5px rgba(251, 192, 45, 0.4);
}

.legend-blocked {
  background-color: #F44336;
  box-shadow: 0 0 5px rgba(244, 67, 54, 0.4);
}

/* Tipografia Monospace e Limitadores */
.text-mono {
  font-family: 'Courier New', Courier, monospace;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.leading-tight {
  line-height: 1.25;
}

.border-top-thin {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

/* Dica flutuante */
.floating-tip {
  position: absolute;
  top: 16px;
  left: 16px;
  background-color: rgba(var(--v-theme-surface), 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(var(--v-border-color), 0.15);
  z-index: 5;
  pointer-events: none;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.border-bottom {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.15);
}

/* MiniMap */
.minimap-container {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 180px;
  height: 110px;
  background-color: rgba(var(--v-theme-surface), 0.85) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(var(--v-border-color), 0.15);
  border-radius: 12px;
  z-index: 10;
  overflow: hidden;
  pointer-events: none;
}
/* Edit Mode Banner */
.floating-edit-banner {
  position: absolute;
  top: 16px;
  left: 16px;
  background-color: rgba(var(--v-theme-surface), 0.95);
  backdrop-filter: blur(10px);
  border: 2px solid rgb(var(--v-theme-warning));
  z-index: 5;
  color: rgb(var(--v-theme-on-surface));
  display: flex;
  align-items: center;
}

.bg-warning-suttle {
  background: linear-gradient(135deg, rgba(var(--v-theme-warning), 0.1) 0%, rgba(var(--v-theme-warning), 0.05) 100%) !important;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>


<style>
/* Global Tooltip Styles (to work with Teleport/v-overlay) */
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

/* Theme-specific font colors for subjects */
.v-theme--dark .subject-inner-card .subject-code,
.v-theme--dark .subject-inner-card .subject-title,
.v-theme--dark .subject-inner-card .subject-semester {
  color: #ffffff !important;
}

.v-theme--dark .subject-inner-card .subject-workload,
.v-theme--dark .subject-inner-card .subject-workload-icon {
  color: rgba(255, 255, 255, 0.7) !important;
}

.v-theme--light .subject-inner-card .subject-code,
.v-theme--light .subject-inner-card .subject-title,
.v-theme--light .subject-inner-card .subject-semester {
  color: #000000 !important;
}

.v-theme--light .subject-inner-card .subject-workload,
.v-theme--light .subject-inner-card .subject-workload-icon {
  color: rgba(0, 0, 0, 0.6) !important;
}
</style>
