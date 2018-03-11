<template>
  <div>
    <h1 v-if="user">Welcome<span v-if="user"> {{user}}</span>.</h1>
    <p>Tap one of the entries in the header to get started.</p>
  </div>
</template>

<script>
  import HTTP from '../http-common';

  export default {
  name: "authenticated-welcome",
  data() {
    return {
      user: null,
    }
  },
  mounted() {
    // Trigger a call to a test location
    this.$Progress.start();
    HTTP.get('v1/control/user').then( (response) => {
      this.user = response.data.username;
      this.$Progress.finish();
    }).catch( (error)=> {
      console.log(error);
    });
  },
};

</script>

<style scoped>

</style>
