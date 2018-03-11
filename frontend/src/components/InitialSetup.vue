<template>
  <div class="form-container">
    <div class="form">
      <h1>Let's finish setting up.</h1>
      <p>This username and password will be used to create other users and secure Annotatron.</p>
      <div>
        <input v-model="username" type="text" placeholder="Enter an initial username (e.g. 'admin')"/>
      </div>
      <div>
        <input v-model="password" type="password" placeholder="Enter a strong, secure password"/>
      </div>
      <div>
        <input v-model="email" type="email" placeholder="Enter a valid email"/>
      </div>
      <div class="form-finalize">
        <button v-on:click="createDefaultUser()">Create Initial User</button>
        <p v-bind:class="state">{{promptText}}</p>
      </div>
    </div>
  </div>

</template>

<script>
  import HTTP from '../http-common';

  export default {
    name: 'initial-setup',
    data() {
      return {
        username: '',
        password: '',
        email: '',
        promptText: 'If you forget this password, you\'ll need to recover Annotatron.',
        state: 'normal',
      };
    },
    methods: {
      createDefaultUser() {
        const success = (response) => {
          this.promptText = 'Welcome.';
          this.state = 'success';
          const redirectToLogin = () => {
            this.$router.push({name: 'home'});
          };
          setTimeout(redirectToLogin, 1500);
        };

        const failure = (response) => {
          this.state = 'error';
          this.promptText = 'Something went wrong';
          console.log(response);
        };

        const warning = (err) => {
          const error = err.response.data;
          alert(JSON.stringify(error["errors"]));
          for (let key in error["errors"]) {
            this.promptText = key + ": " + error["errors"][key];
          }
          this.state = 'warning';
        };

        HTTP.post('v1/control/setup', {
          username: this.username,
          password: this.password,
          email: this.email,
          is_superuser: true,
          is_staff: true,
        }).then((response) => {
          success(response);
        }).catch((error) => {
          console.log(JSON.stringify(error));
          if (error.response.status === 422) {
            warning(error);
          } else {
            failure(error);
          }
        });
      },
    },
  };

</script>

<style scoped>

  .form {
    display: flex;
    flex-direction: column;
    background: #D8D8D8;
    border: 1px solid #979797;
    box-shadow: 2px 2px 3px 0 rgba(183, 183, 183, 0.50);
    width: 780px;
    padding: 15px;
  }

  .form-container {
    margin-top: 15px;
    display: flex;
    flex-direction: row;
    justify-content: center;
    text-align: left;
  }

  .form-finalize {
    display: flex;
  }

  .form-finalize > p {
    justify-content: right;
    padding-left: 30px;
  }

  .form > div {
    margin-top: 15px;
  }

  .form > h1 {
    margin-top: 0px;
    margin-bottom: 20px;
    padding-left: 5px;
  }

  .form > p {
    margin-top: 0px;
    margin-bottom: 12px;
    padding-left: 5px;
  }

  input {
    height: 50px;
    width: 500px;
    font-size: 20px;
    line-height: 75px;
    padding-left: 15px;
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
