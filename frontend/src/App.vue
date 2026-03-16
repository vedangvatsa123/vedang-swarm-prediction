<template>
  <div id="vedang-app">
    <nav class="top-nav">
      <router-link to="/" class="logo">Vedang</router-link>
      <div class="nav-links">
        <router-link to="/wiki">How it works</router-link>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script>
export default { name: 'App' }
</script>
