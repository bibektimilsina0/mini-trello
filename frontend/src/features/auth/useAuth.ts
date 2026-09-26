import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { User, LoginResponse, MessageResponse } from "../../types/api";

export function useMe() {
  return useQuery<User>({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await api.get<User>("/api/auth/me");
      return data;
    },
    retry: false, // a 401 here just means "not logged in" — don't retry it
  });
}

interface SignupInput {
  email: string;
  name: string;
  password: string;
}

export function useSignup() {
  return useMutation<User, unknown, SignupInput>({
    mutationFn: async ({ email, name, password }) => {
      const { data } = await api.post<User>("/api/auth/signup", { email, name, password });
      return data;
    },
  });
}

export function useVerifyEmail() {
  return useMutation<MessageResponse, unknown, string>({
    mutationFn: async (token) => {
      const { data } = await api.get<MessageResponse>("/api/auth/verify-email", { params: { token } });
      return data;
    },
  });
}

interface LoginInput {
  email: string;
  password: string;
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation<LoginResponse, unknown, LoginInput>({
    mutationFn: async ({ email, password }) => {
      const { data } = await api.post<LoginResponse>("/api/auth/login", { email, password });
      return data;
    },
    onSuccess: (data) => {
      if (data.user) {
        queryClient.setQueryData(["me"], data.user);
      }
    },
  });
}

interface Verify2FAInput {
  email: string;
  code: string;
}

export function useVerify2FA() {
  const queryClient = useQueryClient();
  return useMutation<LoginResponse, unknown, Verify2FAInput>({
    mutationFn: async ({ email, code }) => {
      const { data } = await api.post<LoginResponse>("/api/auth/verify-2fa", { email, code });
      return data;
    },
    onSuccess: (data) => {
      if (data.user) {
        queryClient.setQueryData(["me"], data.user);
      }
    },
  });
}

export function useResend2FA() {
  return useMutation<MessageResponse, unknown, string>({
    mutationFn: async (email) => {
      const { data } = await api.post<MessageResponse>("/api/auth/resend-2fa", { email });
      return data;
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation<void, unknown, void>({
    mutationFn: async () => {
      await api.post("/api/auth/logout");
    },
    onSuccess: () => {
      queryClient.setQueryData(["me"], null);
      queryClient.clear();
    },
  });
  
}

interface Disable2FAInput {
  password: string;
}

export function useEnable2FA() {
  const queryClient = useQueryClient();
  return useMutation<MessageResponse, unknown, void>({
    mutationFn: async () => {
      const { data } = await api.post<MessageResponse>("/api/auth/2fa/enable");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useDisable2FA() {
  const queryClient = useQueryClient();
  return useMutation<MessageResponse, unknown, Disable2FAInput>({
    mutationFn: async ({ password }) => {
      const { data } = await api.post<MessageResponse>("/api/auth/2fa/disable", { password });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}