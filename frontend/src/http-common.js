import axios from 'axios';
//import app from './main';

const HTTP = axios.create({
  baseURL: `/annotatron`,
  isAuthenticated: false,
});

HTTP.setAuthentication = (token) => {
  HTTP.isAuthenticated = true;
  HTTP.defaults.Authorization = `Token ${token}`
};

/*HTTP.interceptors.request.use((config) => {
  const token = localStorage.getItem('AnnotatronAuth');
  config.headers["Authorization"] = `Token ${token}`;
  return config;
});*/

/*
HTTP.interceptors.request.use((config) => {
  app.$Progress.start();
  return config;
});

HTTP.interceptors.request.use((response) => {
  app.$Progress.finish();
  return response;
});
*/

export default HTTP;
