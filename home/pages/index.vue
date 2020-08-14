<template>
 <v-app>
  <div>
  <Navbar></Navbar>
  </div>
  <v-container fill-height fluid> 
  <v-row align="center"
      justify="center">
      <v-col align="center"
      justify="center">
    <transition name="fade">
      <div class="display-4"> This is QHub </div> 
    </transition>
      </v-col>
  </v-row>
  <v-row align="center"
      justify="center">
  <div>
  <DescriptionChanger></DescriptionChanger>
  </div>
  </v-row>
</v-container>
  </v-app>
</template>

<script>
import Navbar from "./navbar.vue";
import DescriptionChanger from "./description.vue";

export default {
  data() {
    return {
      show: false
    };
  },
  components: {
    Navbar,
    DescriptionChanger
  }
};
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity .5s;
}
.fade-enter, .fade-leave-to /* .fade-leave-active below version 2.1.8 */ {
  opacity: 0;
}
</style>