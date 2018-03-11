// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue';
import VueProgressBar from 'vue-progressbar';

import App from './App';
import router from './router';

const options = {
  color: '#bffaf3',
  failedColor: 'red',
  thickness: '2px',
  transition: {
    speed: '1.2s',
    opacity: '0.3s',
    termination: 300,
  },
  autoRevert: true,
  location: 'top',
  inverse: false,
};

Vue.use(VueProgressBar, options);

Vue.config.productionTip = false;

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>',
});
