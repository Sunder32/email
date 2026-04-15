import api from "./client";
import type { LoginRequest, TokenResponse, User } from "@/types/auth";

export const login = (data: LoginRequest) =>
  api.post<TokenResponse>("/auth/login", data).then((r) => r.data);

export const register = (data: LoginRequest) =>
  api.post<User>("/auth/register", data).then((r) => r.data);

export const getMe = () =>
  api.get<User>("/auth/me").then((r) => r.data);
