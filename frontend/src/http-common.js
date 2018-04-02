import axios from 'axios';


const HTTP = axios.create({
  baseURL: `/annotatron`,
});

HTTP.isAuthenticated = () => {
  const token = localStorage.getItem("Token");
  if (!token) return false;
  return true;
};

export default HTTP;
