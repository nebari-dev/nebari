<template>
<client-only>
  <v-app-bar app flat fixed color="primary" light>
   <!-- TODO: Change to base path -->
   <div>
   <a href="/qhub/">
   <v-img
   :src="myImage"
   height="180px"
   width="180px"
   contain
   ></v-img>
   </a>
   </div>
   <v-spacer></v-spacer>
   <v-toolbar-items class="hidden-sm-and-down">
      <v-btn
       nuxt
       text
       ripple
       color="white"
       active-class to="/docs">Documentation</v-btn>
      <v-btn
       text
       nuxt
       ripple
       color="white"
       active-class to="/blog">Blog</v-btn>
      <v-btn
       text
       nuxt
       ripple
       color="white"
       active-class to="/faq">F.A.Q.</v-btn>
    </v-toolbar-items>
</v-app-bar>
</client-only>
</template>

<script>
module.exports = {
  name: "Navbar",
  data() {
    return {
      myImage: require("~/assets/QS_Full_Transparent.svg")
    };
  }
};
</script>
