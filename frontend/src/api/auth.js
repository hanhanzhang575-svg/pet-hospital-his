import http from "./http";

/** 使用OAuth2密码模式登录并返回令牌。 */
export async function loginWithPassword(username, password) {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);
  const response = await http.post("/auth/login", body, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    suppressAuthErrorToast: true
  });
  return response;
}

