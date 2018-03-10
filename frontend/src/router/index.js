import Vue from 'vue';
import Router from 'vue-router';
import Header from '@/components/Header';
import InitialSetup from '@/components/InitialSetup';


Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Header',
      component: Header,
      children: [{
        path: '/setup',
        name: 'InitialSetup',
        component: InitialSetup,
      }],
      meta: {
        progress: {
          func: [
            {call: 'color', modifier: 'temp', argument: '#ffb000'},
            {call: 'fail', modifier: 'temp', argument: '#6e0000'},
            {call: 'location', modifier: 'temp', argument: 'top'},
            {call: 'transition', modifier: 'temp', argument: {speed: '1.5s', opacity: '0.6s', termination: 400}}
          ]
        }
      }
    },
  ],

});
