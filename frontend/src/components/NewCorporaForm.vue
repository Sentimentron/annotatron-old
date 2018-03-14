<!-- This component allows the user to add a Corpus object. -->

<template>
  <div>
    <h1>Adding a new corpus.</h1>
    <div class="form">
      <form v-on:submit.prevent="createCorpus">
        <div>
          <input v-model="corpusName" type="text" placeholder="Enter a name for the new corpus"/>
        </div>
        <div>
          <textarea v-model="description" type="password" placeholder="(Optional) Enter a description"/>
        </div>
        <div class="form-finalize">
          <button value="Login" type="submit" v-on:click="createCorpus()">Create New Corpus</button>
          <p v-bind:class="state">{{promptText}}</p>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
  import HTTP from '../http-common';
  export default {
    name: "new-corpora-form",
    data: function() {
      return {
        state: "normal",
        promptText: "",
        description: "",
        corpusName: ""
      };
    },
    methods: {

      createCorpus() {

        let processResult = (response) => {
          console.log(response);
          this.$Progress.stop();
        };

        let processError = (response) => {
          console.error(response);
          this.$Progress.fail();
          this.state = 'error';
          this.promptText = 'Internal error :(';
        };

        let processValidationError = (response) => {
          this.state = 'warning';
          this.$Progress.fail();
          for (let key in response.data) {
            this.promptText = `${key}: ${response.data[key]}`;
            break;
          }
        };

        this.state = 'working';
        this.promptText = 'Working...';
        this.$Progress.start();

        HTTP.post('v1/corpora/', {
          name: this.corpusName,
          description: this.description
        }).then( (response) => {
          processResult(response);
        }).catch( (error) => {
          if (error.response.status === 400) {
            processValidationError(error.response);
          } else {
            processError(error);
          }
        });

      }
    }
  }
</script>

<style scoped>

  form > div {
    margin-top: 5px;
    margin-bottom: 5px;
  }

  input, textarea {
    width: 500px;
    font-size: 20px;
    line-height: 75px;
    padding-left: 15px;
    border: 1px solid #CCCCCC;
  }

  input {
    height: 50px;
  }

  button {
    background-image: radial-gradient(50% 196%, #06B06D 50%, #04A163 100%);
    border-radius: 10px;
    padding: 15px;
    color: white;
    font-size: 20px;
    display: flex;
  }

</style>
