import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { Workspace, Board } from "../../types/api";

export function useWorkspaces() {
  return useQuery<Workspace[]>({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const { data } = await api.get<Workspace[]>("/api/workspaces");
      return data;
    },
  });
} 

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation<Workspace, unknown, string>({
    mutationFn: async (name) => {
      const { data } = await api.post<Workspace>("/api/workspaces", { name });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },  
  });
}

export function useBoards(workspaceId: string | null) {
  return useQuery<Board[]>({
    queryKey: ["workspaces", workspaceId, "boards"],
    queryFn: async () => {
      const { data } = await api.get<Board[]>(`/api/workspaces/${workspaceId}/boards`);
      return data;
    },
    enabled: !!workspaceId,
  });
}

export function useCreateBoard(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation<Board, unknown, string>({
    mutationFn: async (title) => {
      const { data } = await api.post<Board>(`/api/workspaces/${workspaceId}/boards`, { title });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "boards"] });
    },
  });
}
