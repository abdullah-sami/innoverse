import AsyncStorage from "@react-native-async-storage/async-storage";

// Base API Configuration
export const INNOVERSE_API_CONFIG = {
  BASE_URL: "https://1b0d83c26829.ngrok-free.app",
  // BASE_URL: "https://rafidabdullahsamiweb.pythonanywhere.com",
};





const getHeaders = async () => {
  const token = await AsyncStorage.getItem("access");
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};








// Login API  ********************************
export const fetchLogin = async ({
  username,
  password,
}: {
  username: string;
  password: string;
}) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/login/`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      password,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to login: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
};








// Helper function to refresh the access token **********************
const refreshAccessToken = async () => {
  const refresh = await AsyncStorage.getItem("refresh");
  if (!refresh) {
    throw new Error("Refresh token not found. Please log in again.");
  }

  const response = await fetch(
    `${INNOVERSE_API_CONFIG.BASE_URL}/api/token/refresh/`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh }),
    }
  );

  if (!response.ok) {
    await AsyncStorage.clear();
    throw new Error("Session expired. Please log in again.");
  }

  const data = await response.json();
  await AsyncStorage.setItem("access", data.access);
  return data.access;
};



