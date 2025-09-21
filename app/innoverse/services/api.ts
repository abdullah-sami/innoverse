import AsyncStorage from "@react-native-async-storage/async-storage";

// Base API Configuration
export const INNOVERSE_API_CONFIG = {
  BASE_URL: "http://192.168.0.175",
  // BASE_URL: "https://rafidabdullahsamiweb.pythonanywhere.com",
};




// Helper function to get headers with Authorization token

const getHeaders = async () => {
  const token = await AsyncStorage.getItem("access");
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};






// Register API ****************************************
export const fetchRegister = async ({
  username,
  email,
  password,
  birthday,
}: {
  username: string;
  email: string;
  password: string;
  birthday: string;
}) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/user/api/register/`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: username,
      email: email,
      password: password,
      birthday: birthday,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    console.log("Registration error:", errorData);

    // Create a proper Error object with custom message
    let errorMessage = "Registration failed. Please try again.";

    if (errorData.username) {
      errorMessage = errorData.username[0];
    } else if (errorData.email) {
      errorMessage = errorData.email[0];
    } else if (errorData.password) {
      errorMessage = errorData.password[0];
    }

    throw new Error(errorMessage);
  }
  const data = await response.json();
  return data;
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
    `${INNOVERSE_API_CONFIG.BASE_URL}/auth/token/refresh/`,
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






// Function to handle API requests with token refresh logic  ***********************************
const fetchWithTokenRefresh = async (url: string, options: RequestInit) => {
  let response = await fetch(url, options);

  if (response.status === 401) {
    try {
      const newAccessToken = await refreshAccessToken();
      const headers = {
        ...options.headers,
        Authorization: `Bearer ${newAccessToken}`,
      };

      response = await fetch(url, { ...options, headers });
    } catch (error) {
      throw new Error("Failed to refresh token or retry request.");
    }
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Request failed: ${errorText}`);
  }

  return response;
};









// Search API **************************************
export const fetchSearchResults = async ({ query }: { query: string }) => {
  const endpoint = query
    ? `${INNOVERSE_API_CONFIG.BASE_URL}/api/search?query=${encodeURIComponent(
        query
      )}`
    : `${INNOVERSE_API_CONFIG.BASE_URL}/api/search?query=asib`;

  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch search results: ${response.statusText}`);
  }

  const data = await response.json();
  return data.results;
};














// Posts API **************************************
export const fetchPostResults = async () => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/posts`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch posts: ${response.statusText}`);
  }

  const data = await response.json();
  return data.results;
};

export const fetchPost = async ({postId}) =>{
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/posts/${postId}`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch post: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
};

// Reels API **************************************
export const fetchReelResults = async () => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/reels`;
  const headers = await getHeaders();

  const response = await fetchWithTokenRefresh(endpoint, {
    method: "GET",
    headers,
  });

  const data = await response.json();
  return data.results;
};






// Fetch the first reel for a specific post ************************************
export const fetchFirstReel = async (postId:number) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/reels/${postId}`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  const data = await response.json();
  return data;
};




// Reel Item API ***************************
export const fetchReelItem = async (post_id: string) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/reels/${post_id}`;

  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch reel: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
};












// Notifications API ******************************************
export const fetchNotifications = async () => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/notifications`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch notifications: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
};





// User Profile API **********************************

export const fetchUserProfile = async () => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/user/api/profile`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch user profile: ${response.statusText}`);
  }

  const data = await response.json();
  return data[0].user;
};





export const followUser = async (user_id: number) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/user/profile/follow/`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "POST",
    headers,
    body: JSON.stringify({ user_id: user_id }),
  });

  return response;
};






// Creator Application API ***********************

export const fetchCreatorApplication = async (user_id) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/user/api/creator-application/`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "POST",
    headers,

    body: JSON.stringify({
      user: user_id,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to process application: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
};


export const fetchCreatorApplicationStatus = async (user_id) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/user/api/creator-application/by-user/${user_id}/`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch application: ${response.statusText}`);
  }

  const data = await response.json();
  return data[0];
};







// Comments API ******************************************
export const fetchComments = async (post_id: string, page: number = 1) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/posts/${post_id}/comments/?page=${page}`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch comments: ${response.statusText}`);
  }

  const data = await response.json();
  return data; // Return the full response object instead of just data.results
};

export const postComment = async (post_id: string, comment: string) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/posts/${post_id}/comments/`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "POST",
    headers,
    body: JSON.stringify({ post: post_id, comment: comment }),
  });

  if (!response.ok) {
    throw new Error(`Failed to post comment: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
};


export const deleteComment = async (post_id: number, comment_id: number) => {
  console.log(post_id, comment_id);
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/posts/${post_id}/comments/`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "DELETE",
    headers,
    body: JSON.stringify({ comment_id: comment_id }),
  });

  if (!response.ok) {
    throw new Error(`Failed to delete comment: ${response.statusText}`);
  }

};










// Likes API ******************************************
export const postLikes = async (post_id: number) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/post_likes/${post_id}/`;
  const headers = await getHeaders();

  // Ensure Content-Type is set for POST requests
  const requestHeaders = {
    ...headers,
    'Content-Type': 'application/json',
  };

  const response = await fetch(endpoint, {
    method: "POST",
    headers: requestHeaders,
    body: JSON.stringify({}), // Send empty JSON object as body
  });

  if (!response.ok) {
    // Log more details about the error
    const errorText = await response.text();
    console.error('Error response:', response.status, response.statusText, errorText);
    throw new Error(`Failed to post like: ${response.status} ${response.statusText} - ${errorText}`);
  }

  const data = await response.json();
  return data; 
};


export const deleteLikes = async (post_id: number) => {
  const endpoint = `${INNOVERSE_API_CONFIG.BASE_URL}/api/post_likes/${post_id}/`;
  const headers = await getHeaders();

  const response = await fetch(endpoint, {
    method: "DELETE",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to delete like: ${response.statusText}`);
  }
};
