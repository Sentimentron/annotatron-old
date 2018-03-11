<template>

  <div class="app-wrapper">
    <div class="header">
      <router-link :to="{}">
        <img src="../assets/logo.svg" alt="Annotatron"/>
      </router-link>
      <router-link :to="{'name': 'collect'}" class="header-navigation">
        Collect
      </router-link>
    </div>
    <div class="hello">
      <router-view></router-view>
    </div>
    <div class="hello">
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

  export default {
  name: 'HelloWorld',
  data() {
    return {
      msg: 'Welcome to Your Vue.js App',
    };
  },
  mounted() {
    HTTP.get('v1/control/setup').then((response) => {
      if (response.data.requires_setup) {
        this.$router.push( {name: 'InitialSetup'} );
      } else if (!HTTP.isAuthenticated) {
        this.$router.push( {name: 'Login'} );
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
