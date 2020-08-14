<template>
<div>
<vue-typed-js :strings="['students', 'scientists', 'startups', 'hackers', 'engineers', 'you.']">
  <h1>The perfect environment for: <span class="typing"></span></h1>
</vue-typed-js>
</div>
</template>

<script>
export default {
  name: "DescriptionChanger",
  data: function() {
    return {};
  }
};
</script>
