<script setup>
import { ref } from 'vue'

const emit = defineEmits(['logout', 'change-page'])

const isCompact = ref(false)
</script>

<template>
  <v-navigation-drawer
    permanent
    theme="dark"
    :rail="isCompact"
  >
    <v-list density="compact" nav>
      <v-list-item
        :prepend-icon="isCompact ? 'mdi-chevron-right' : 'mdi-chevron-left'"
        title="Ocultar Menu"
        class="mb-2"
        @click="isCompact = !isCompact"
      ></v-list-item>

      <v-divider class="mb-2"></v-divider>

      <v-list-item
        prepend-icon="mdi-home"
        title="Início"
        value="home"
        @click="emit('change-page', 'home')"
      ></v-list-item>

      <v-list-item
        prepend-icon="mdi-calendar-clock"
        title="Gerar Grade de Horários"
        value="generate_schedules"
        @click="emit('change-page', 'generate_schedules')"
      ></v-list-item>

    </v-list>

    <template v-slot:append>
      <v-divider></v-divider>
      <v-list density="compact" nav>
        <v-list-item
          prepend-icon="mdi-logout"
          title="Sair (Logout)"
          base-color="error"
          @click="emit('logout')"
        ></v-list-item>
      </v-list>
    </template>
  </v-navigation-drawer>
</template>

<style scoped>
</style>