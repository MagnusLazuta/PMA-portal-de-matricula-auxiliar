<script setup>
import { onMounted, ref, computed } from 'vue'
import axios from 'axios'

const users = ref([])
const loading = ref(false)
const search = ref('')

// Form State
const role = ref('student')
const name = ref('')
const email = ref('')
const cardNumber = ref('')
const password = ref('ufrgs123') // Default temporary password
const currentSemester = ref(1)
const course = ref('Ciência da Computação')
const comgradRole = ref('Membro')

const coursesOptions = [
  'Ciência da Computação',
  'Engenharia de Computação'
]

const formLoading = ref(false)
const formSuccess = ref('')
const formError = ref('')

// CSV State
const csvFile = ref(null)
const csvLoading = ref(false)
const csvSuccess = ref('')
const csvError = ref('')
const csvErrorsList = ref([])

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await axios.get('http://localhost:8000/admin/users')
    users.value = res.data
  } catch (err) {
    console.error('Erro ao buscar usuários:', err)
  } finally {
    loading.value = false
  }
}

const getRoleLabel = (role) => {
  const mapping = {
    student: 'Estudante',
    comgrad: 'Membro da COMGRAD',
    admin: 'Administrador',
    comgrad_admin: 'Membro da COMGRAD e Administrador'
  }
  return mapping[role] || role
}

const getRoleColor = (role) => {
  const mapping = {
    student: 'info',
    comgrad: 'success',
    admin: 'warning',
    comgrad_admin: 'primary'
  }
  return mapping[role] || 'grey'
}

const isFormValid = computed(() => {
  const basic = name.value.trim() !== '' && 
                email.value.trim() !== '' && 
                cardNumber.value.length === 8 && 
                /^\d+$/.test(cardNumber.value) && 
                password.value.length >= 6
  return basic
})

const handleRegister = async () => {
  formSuccess.value = ''
  formError.value = ''
  formLoading.value = true
  
  const studentDetails = role.value === 'student' ? {
    current_semester: Number(currentSemester.value),
    course: course.value,
    curriculum_id: course.value === 'Engenharia de Computação' ? 2 : 1
  } : null

  try {
    await axios.post('http://localhost:8000/admin/users', {
      role: role.value,
      name: name.value,
      email: email.value,
      card_number: Number(cardNumber.value),
      password: password.value,
      student_details: studentDetails,
      comgrad_role: role.value === 'comgrad' ? comgradRole.value : null
    })
    
    formSuccess.value = `Usuário ${name.value} cadastrado com sucesso! A primeira senha de acesso é "${password.value}".`
    // Reset form fields
    name.value = ''
    email.value = ''
    cardNumber.value = ''
    password.value = 'ufrgs123'
    
    await loadUsers()
  } catch (err) {
    console.error(err)
    formError.value = err?.response?.data?.detail || 'Erro ao cadastrar usuário.'
  } finally {
    formLoading.value = false
  }
}

const handleUpgrade = async (user) => {
  if (confirm(`Deseja mesmo dar acesso administrativo para ${user.name}?`)) {
    try {
      const res = await axios.post(`http://localhost:8000/admin/users/${user.id}/upgrade-to-admin`)
      alert(res.data.message || 'Membro promovido com sucesso!')
      await loadUsers()
    } catch (err) {
      console.error(err)
      alert(err?.response?.data?.detail || 'Erro ao conceder acesso admin.')
    }
  }
}

const handleToggleStatus = async (user) => {
  const actionText = user.is_active ? 'desabilitar' : 'habilitar'
  if (confirm(`Deseja mesmo ${actionText} o usuário ${user.name}?`)) {
    try {
      const res = await axios.post(`http://localhost:8000/admin/users/${user.id}/toggle-status`)
      alert(res.data.message || `Usuário ${actionText}do com sucesso!`)
      await loadUsers()
    } catch (err) {
      console.error(err)
      alert(err?.response?.data?.detail || 'Erro ao alterar status do usuário.')
    }
  }
}

const handleDeleteUser = async (user) => {
  if (confirm(`ATENÇÃO: Deseja mesmo EXCLUIR permanentemente o usuário ${user.name}? Esta ação não pode ser desfeita.`)) {
    try {
      const res = await axios.delete(`http://localhost:8000/admin/users/${user.id}`)
      alert(res.data.message || 'Usuário excluído com sucesso!')
      await loadUsers()
    } catch (err) {
      console.error(err)
      alert(err?.response?.data?.detail || 'Erro ao excluir usuário.')
    }
  }
}

const triggerCsvUpload = () => {
  const fileInput = document.getElementById('csvFileInput')
  if (fileInput) fileInput.click()
}

const handleFileChange = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  csvLoading.value = true
  csvSuccess.value = ''
  csvError.value = ''
  csvErrorsList.value = []
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await axios.post('http://localhost:8000/admin/users/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (res.data.created > 0) {
      csvSuccess.value = `Importação concluída! ${res.data.created} usuário(s) criado(s) com sucesso.`
    }
    
    if (res.data.errors && res.data.errors.length > 0) {
      csvErrorsList.value = res.data.errors
      csvError.value = 'Houve alguns erros durante a importação.'
    }
    
    await loadUsers()
  } catch (err) {
    console.error(err)
    csvError.value = err?.response?.data?.detail || 'Erro ao importar arquivo CSV.'
  } finally {
    csvLoading.value = false
    // Clear input
    e.target.value = ''
  }
}

const filteredUsers = computed(() => {
  if (!search.value.trim()) return users.value
  const q = search.value.toLowerCase()
  return users.value.filter(u => 
    u.name.toLowerCase().includes(q) ||
    u.email.toLowerCase().includes(q) ||
    String(u.card_number).includes(q)
  )
})

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <v-container>
    <div class="mb-6">
      <h1 class="text-h4 font-weight-bold text-primary">Gerenciamento de Usuários</h1>
      <p class="text-subtitle-1 text-medium-emphasis">Cadastre estudantes, membros da COMGRAD e administradores individualmente ou via CSV.</p>
    </div>

    <v-row class="mb-6">
      <!-- Form Card -->
      <v-col cols="12" md="7">
        <v-card class="pa-6 rounded-lg h-100" elevation="2">
          <v-card-title class="text-h6 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
            <v-icon color="primary" class="mr-2">mdi-account-plus</v-icon>
            Cadastrar Novo Usuário
          </v-card-title>
          
          <v-card-text class="px-0">
            <v-alert v-if="formSuccess" type="success" variant="tonal" class="mb-4" closable @click:close="formSuccess = ''">
              {{ formSuccess }}
            </v-alert>
            <v-alert v-if="formError" type="error" variant="tonal" class="mb-4" closable @click:close="formError = ''">
              {{ formError }}
            </v-alert>

            <v-form @submit.prevent="handleRegister">
              <v-row>
                <v-col cols="12" sm="6" class="py-1">
                  <v-select
                    v-model="role"
                    label="Papel / Perfil"
                    variant="outlined"
                    density="comfortable"
                    :items="[
                      { title: 'Estudante', value: 'student' },
                      { title: 'Membro da COMGRAD', value: 'comgrad' },
                      { title: 'Administrador', value: 'admin' }
                    ]"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6" class="py-1">
                  <v-text-field
                    v-model="cardNumber"
                    label="Matrícula (8 dígitos)"
                    variant="outlined"
                    density="comfortable"
                    maxLength="8"
                    placeholder="Ex: 88888888"
                    required
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-text-field
                v-model="name"
                label="Nome Completo"
                variant="outlined"
                density="comfortable"
                required
                class="mb-1"
              ></v-text-field>

              <v-text-field
                v-model="email"
                label="E-mail"
                type="email"
                variant="outlined"
                density="comfortable"
                placeholder="exemplo@ufrgs.br"
                required
                class="mb-1"
              ></v-text-field>

              <v-text-field
                v-model="password"
                label="Senha Provisória"
                type="text"
                variant="outlined"
                density="comfortable"
                required
                hint="Alunos deverão alterar essa senha no primeiro acesso."
                persistent-hint
                class="mb-4"
              ></v-text-field>

              <!-- Extra fields based on role selection -->
              <v-divider v-if="role === 'student' || role === 'comgrad'" class="mb-4"></v-divider>

              <v-row v-if="role === 'student'">
                <v-col cols="12" sm="6" class="py-1">
                  <v-select
                    v-model="course"
                    label="Curso"
                    variant="outlined"
                    density="comfortable"
                    :items="coursesOptions"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6" class="py-1">
                  <v-text-field
                    v-model="currentSemester"
                    label="Semestre Atual"
                    type="number"
                    variant="outlined"
                    density="comfortable"
                    min="1"
                    max="14"
                    required
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-row v-if="role === 'comgrad'">
                <v-col cols="12" class="py-1">
                  <v-text-field
                    v-model="comgradRole"
                    label="Cargo na COMGRAD"
                    variant="outlined"
                    density="comfortable"
                    placeholder="Ex: Coordenador, Membro"
                    required
                  ></v-text-field>
                </v-col>
              </v-row>

              <v-btn
                type="submit"
                color="primary"
                size="large"
                class="mt-4"
                block
                :disabled="!isFormValid || formLoading"
                :loading="formLoading"
              >
                Cadastrar Usuário
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- CSV Card -->
      <v-col cols="12" md="5">
        <v-card class="pa-6 rounded-lg h-100" elevation="2">
          <v-card-title class="text-h6 font-weight-bold px-0 pt-0 mb-4 d-flex align-center">
            <v-icon color="secondary" class="mr-2">mdi-file-delimited-outline</v-icon>
            Importação em Lote (.csv)
          </v-card-title>
          
          <v-card-text class="px-0">
            <p class="text-body-2 text-medium-emphasis mb-4">
              Crie múltiplos usuários importando um arquivo CSV formatado com o seguinte cabeçalho:
            </p>
            
            <v-sheet class="pa-3 bg-grey-lighten-4 rounded text-caption font-mono mb-4 text-truncate border">
              role,name,email,card_number,password,course,current_semester,comgrad_role
            </v-sheet>

            <div class="mb-4">
              <span class="text-caption font-weight-bold text-uppercase">Legenda das colunas:</span>
              <ul class="text-caption pl-4 mt-1">
                <li><strong>role:</strong> student, comgrad, ou admin</li>
                <li><strong>course:</strong> Ciência da Computação ou Engenharia de Computação</li>
                <li><strong>current_semester:</strong> Número do semestre (apenas para student)</li>
                <li><strong>comgrad_role:</strong> Cargo (apenas para comgrad)</li>
              </ul>
            </div>

            <v-alert v-if="csvSuccess" type="success" variant="tonal" class="mb-4" closable @click:close="csvSuccess = ''">
              {{ csvSuccess }}
            </v-alert>
            <v-alert v-if="csvError" type="error" variant="tonal" class="mb-4" closable @click:close="csvError = ''">
              {{ csvError }}
              <div v-if="csvErrorsList.length" class="mt-2 text-caption">
                <div v-for="(err, idx) in csvErrorsList" :key="idx">• {{ err }}</div>
              </div>
            </v-alert>

            <input
              type="file"
              id="csvFileInput"
              accept=".csv"
              style="display: none"
              @change="handleFileChange"
            />
            
            <v-btn
              color="secondary"
              variant="outlined"
              size="large"
              prepend-icon="mdi-upload"
              :loading="csvLoading"
              @click="triggerCsvUpload"
              block
              class="mt-2"
            >
              Upload de CSV e Importar
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Users List -->
    <v-card class="pa-6 rounded-lg" elevation="2">
      <div class="d-flex justify-space-between align-center mb-4 flex-wrap">
        <v-card-title class="text-h6 font-weight-bold px-0 pt-0 d-flex align-center">
          <v-icon color="primary" class="mr-2">mdi-account-multiple</v-icon>
          Usuários Cadastrados
        </v-card-title>
        
        <v-text-field
          v-model="search"
          label="Buscar por nome, e-mail ou matrícula"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="compact"
          hide-details
          style="max-width: 350px; min-width: 250px"
        ></v-text-field>
      </div>

      <v-data-table
        v-if="!loading"
        :items="filteredUsers"
        :headers="[
          { title: 'Nome', key: 'name' },
          { title: 'Papel', key: 'role' },
          { title: 'Status', key: 'status', align: 'center' },
          { title: 'Privilégios do Usuário', key: 'privileges', sortable: false, align: 'center' },
          { title: 'Desativar', key: 'disable', sortable: false, align: 'center' },
          { title: 'Remover', key: 'remove', sortable: false, align: 'center' }
        ]"
        density="comfortable"
        class="border rounded"
        items-per-page-text="Itens por página:"
        page-text="{0}-{1} de {2}"
      >
        <template v-slot:item="{ item }">
          <tr>
            <td class="font-weight-medium">{{ item.name }}</td>
            <td>
              <v-chip :color="getRoleColor(item.role)" size="small" variant="flat">
                {{ getRoleLabel(item.role) }}
              </v-chip>
            </td>
            <td class="text-center">
              <v-chip :color="item.is_active ? 'success' : 'error'" size="small" variant="tonal">
                {{ item.is_active ? 'Ativo' : 'Desativado' }}
              </v-chip>
            </td>
            
            <!-- Privilégios do Usuário Column -->
            <td class="text-center">
              <v-btn
                v-if="item.role === 'comgrad'"
                color="warning"
                variant="outlined"
                size="small"
                prepend-icon="mdi-shield-crown"
                @click="handleUpgrade(item)"
              >
                Tornar Admin
              </v-btn>
              <span v-else-if="item.role === 'admin' || item.role === 'comgrad_admin'" class="text-caption text-success font-weight-medium">
                <v-icon color="success" size="18">mdi-check</v-icon> Admin
              </span>
              <span v-else class="text-caption text-medium-emphasis">
                —
              </span>
            </td>

            <!-- Desativar Column -->
            <td class="text-center">
              <template v-if="item.role === 'admin' || item.role === 'comgrad_admin'">
                <span class="text-caption text-medium-emphasis">Não permitido</span>
              </template>
              <template v-else>
                <v-btn
                  :color="item.is_active ? 'orange' : 'success'"
                  variant="outlined"
                  size="small"
                  @click="handleToggleStatus(item)"
                >
                  {{ item.is_active ? 'Desabilitar' : 'Habilitar' }}
                </v-btn>
              </template>
            </td>

            <!-- Remover Column -->
            <td class="text-center">
              <template v-if="item.role === 'admin' || item.role === 'comgrad_admin'">
                <span class="text-caption text-medium-emphasis">Não permitido</span>
              </template>
              <template v-else>
                <v-btn
                  color="error"
                  variant="text"
                  size="small"
                  icon="mdi-delete"
                  @click="handleDeleteUser(item)"
                  title="Excluir Usuário"
                >
                </v-btn>
              </template>
            </td>
          </tr>
        </template>
      </v-data-table>
      
      <v-progress-linear v-else indeterminate color="primary"></v-progress-linear>
    </v-card>
  </v-container>
</template>

<style scoped>
</style>
