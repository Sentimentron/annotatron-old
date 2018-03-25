<template>

  <div class="app-wrapper">
    <div class="header">
      <router-link :to="{}">
        <img src="../assets/logo.svg" alt="Annotatron"/>
      </router-link>
      <span v-if="authenticationStatus === 'admin'">
        <router-link :to="{'name': 'Corpora'}" class="header-navigation">
          Collect
        </router-link>
      </span>
      <span v-if="authenticationStatus !== 'notAuthenticated'">
        <router-link :to="{'name': 'collect'}" class="header-navigation">
          Annotate
        </router-link>
      </span>
      <span v-if="authenticationStatus === 'admin'">
        <router-link :to="{'name': 'collect'}" class="header-navigation">
          Process
        </router-link>
      </span>
      <span v-if="authenticationStatus === 'admin'">
        <router-link :to="{'name': 'export'}" class="header-navigation">
          Export
        </router-link>
      </span>
      <span v-if="authenticationStatus === 'notAuthenticated'"><button
        v-on:click="$router.push({path: '/login', params: {'authenticationBus': this.bus}})">Log In</button></span>
      <span
        v-if="authenticationStatus !== 'notAuthenticated'"><button v-on:click="signOut()">Sign Out</button></span>
    </div>
    <div class="hello">
      <router-view></router-view>
    </div>
    <div class="hello" style="display:none">
      <h1>{{ msg }}</h1>
      <h2>Essential Links and stuff</h2>
      <ul>
        <li>
          <a
            href="https://vuejs.org"
            target="_blank"
          >
            Core Docs
          </a>
        </li>
        <li>
          <a
            href="https://forum.vuejs.org"
            target="_blank"
          >
            Forum
          </a>
        </li>
        <li>
          <a
            href="https://chat.vuejs.org"
            target="_blank"
          >
            Community Chat
          </a>
        </li>
        <li>
          <a
            href="https://twitter.com/vuejs"
            target="_blank"
          >
            Twitter
          </a>
        </li>
        <br>
        <li>
          <a
            href="http://vuejs-templates.github.io/webpack/"
            target="_blank"
          >
            Docs for This Template
          </a>
        </li>
      </ul>
      <h2>Ecosystem</h2>
      <ul>
        <li>
          <a
            href="http://router.vuejs.org/"
            target="_blank"
          >
            vue-router
          </a>
        </li>
        <li>
          <a
            href="http://vuex.vuejs.org/"
            target="_blank"
          >
            vuex
          </a>
        </li>
        <li>
          <a
            href="http://vue-loader.vuejs.org/"
            target="_blank"
          >
            vue-loader
          </a>
        </li>
        <li>
          <a
            href="https://github.com/vuejs/awesome-vue"
            target="_blank"
          >
            awesome-vue
          </a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
  import HTTP from '../http-common';
  import {EventBus} from '../global-bus';

  export default {
  name: 'Header',
  data() {
    return {
      msg: 'Welcome to Your Vue.js App',
      authenticationStatus: '',
    };
  },

  methods: {
    signOut() {
      EventBus.$emit('authenticationChanged', {authenticated: 'notAuthenticated'});
      localStorage.clear();
      this.$router.push('/login');
    },
  },

  mounted() {
    // Make sure that we show the right sign-in, sign-out buttons.
    EventBus.$on('authenticationChanged', (data) => {
      this.authenticationStatus = data.authenticated;
    });

    HTTP.get('v1/control/setup').then((response) => {
      if (response.data.requires_setup) {
        //this.bus.$emit('AuthenticationChange', { authenticated: 'notAuthenticated' });
        this.$router.push({ name: 'InitialSetup' });
      } else {
        const token = localStorage.getItem('Token');
        HTTP.defaults.headers.common.Authorization = 'Token ' + token;
        EventBus.$emit('AuthenticationChange', { authenticated: 'notConfirmed' });
        HTTP.get('v1/control/user').then( (innerResponse) => {
          if (innerResponse.data.is_superuser) {
            EventBus.$emit('authenticationChanged', { authenticated: 'admin' });
          } else if (innerResponse.data.is_staff) {
            EventBus.$emit('authenticationChanged', { authenticated: 'staff' });
          } else {
            EventBus.$emit('authenticationChanged', { authenticated: 'annotator' });
          }
        }).catch( (error) => {
          alert("Something went wrong.");
          console.log(error);
        });
      }
    }).catch((error) => {
      alert('Something went wrong...');
      console.log(error);
    });
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

  .header {
    /* Rectangle: */
    background: #06B06D;
    box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.50);
    width: 100%;
    text-align: left;
    flex-direction: row;
    justify-content: center;
    height: 51px;
  }

  .header-img {
    text-decoration: flex;
  }

  .header-navigation {
    margin-left: 15px;
    text-decoration: none;
    font-size: 20px;
    color: white;
  }

  .header-navigation:first-of-type {
    margin-left: 30px;
  }

  .header ul .navigation {
    display: inline;
    list-style: none;
  }

  h1, h2 {
    font-weight: normal;
  }

  ul {
    list-style-type: none;
    padding: 0;
  }

  li {
    display: inline-block;
    margin: 0 10px;
  }

  a {
    color: #42b983;
  }
</style>
