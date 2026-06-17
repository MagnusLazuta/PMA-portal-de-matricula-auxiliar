<script setup>
import CurriculumCanvas from './components/CurriculumCanvas.vue'

defineProps({
  studentId: {
    type: Number,
    required: true
  }
})
</script>

<template>
  <div>
    <h1 class="text-h4 font-weight-bold text-primary mb-4">
      Grade Curricular
    </h1>

    <v-divider class="mb-6"></v-divider>

    <v-row>
      <v-col cols="12">
        <v-card class="pa-4 rounded-xl" elevation="2">
          <v-card-title class="text-h6 font-weight-bold px-4 pt-4 mb-2 d-flex align-center">
            <v-icon color="primary" class="mr-2">mdi-sitemap</v-icon>
            Visualização do Currículo (Grafo de Pré-requisitos)
          </v-card-title>
          
          <CurriculumCanvas :studentId="studentId" />
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<style scoped>
</style>
