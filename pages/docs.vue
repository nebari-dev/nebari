<template>
  <v-app>
  <Navbar></Navbar>
  <v-container fluid fill-height>
   <v-layout
        >
	<iframe src="https://qhub.readthedocs.io/en/latest/README.html" 
	width="100%"
	frameborder="0"
	></iframe>
 </v-layout>
 </v-container>
  </v-app>
</template>
<script>
import Navbar from "./navbar.vue";

export default {
  components: {
    Navbar
  },
  data() {
    return {};
  }
};
</script>

