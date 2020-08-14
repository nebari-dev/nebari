<template>
<v-app>
<div><Navbar></Navbar></div>

<v-container fluid>
  <br>
  <br>
  <br>
<div class="text-xs-center display-2 font-weight-thin"> Frequently Asked Questions </div> 
<v-row align="center"
justify="center">
<v-col align="center"
justify="center">
<ul>
<li> What is QHub? </li>
<li> What makes Qhub different, than, say, JupyterHub? </li>
<li> Can I use Qhub offline? </li>
</ul>
</v-col>
</v-row>
</v-container>
</v-app>
</template>

<script>
import Navbar from "./navbar.vue";
export default {
  data() {
    return {};
  },
  components: {
    Navbar
  }
};
</script>
