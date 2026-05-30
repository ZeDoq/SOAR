<template>
  <span :class="['status', status]">{{ $t('status.' + status) }}</span>
</template>

<script setup>
defineProps({ status: String })
</script>
