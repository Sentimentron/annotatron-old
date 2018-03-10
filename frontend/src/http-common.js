import axios from 'axios';
import app from './main';

const HTTP = axios.create({
  baseURL: `/annotatron`,
  headers: {
    Authorization: 'Bearer {token}',
  },
});
/*
HTTP.interceptors.request.use((config) => {
  app.$Progress.start();
  return config;
});

HTTP.interceptors.request.use((response) => {
  app.$Progress.finish();
  return response;
});*/

export default HTTP;
