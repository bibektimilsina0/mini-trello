import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { Board, List, ListWithCards, Card } from "../../types/api";

export function useBoard(boardId: string | undefined) {
  return useQuery<Board>({
    queryKey: ["boards", boardId],
    queryFn: async () => {
      const { data } = await api.get<Board>(`/api/boards/${boardId}`);
      return data;
    },
    enabled: !!boardId,
  });
}

// Fetches lists, then fetches each list's cards, and returns one combined
// array of lists-with-cards. Simple and fine at this scale — a fancier
// version might use a single backend endpoint that returns everything
// nested in one response, worth adding later if this feels chatty.
export function useBoardLists(boardId: string | undefined) {
  return useQuery<ListWithCards[]>({
    queryKey: ["boards", boardId, "lists"],
    queryFn: async () => {
      const { data: lists } = await api.get<List[]>(`/api/boards/${boardId}/lists`);
      const withCards = await Promise.all(
        lists.map(async (list): Promise<ListWithCards> => {
          const { data: cards } = await api.get<Card[]>(`/api/lists/${list.id}/cards`);
          return { ...list, cards };
        })
      );
      return withCards;
    },
    enabled: !!boardId,
  });
}

export function useCreateList(boardId: string) {
  const queryClient = useQueryClient();
  return useMutation<List, unknown, string>({
    mutationFn: async (title) => {
      const { data } = await api.post<List>(`/api/boards/${boardId}/lists`, { title });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["boards", boardId, "lists"] });
    },
  });
}

interface CreateCardInput {
  listId: string;
  title: string;
}

export function useCreateCard(boardId: string) {
  const queryClient = useQueryClient();
  return useMutation<Card, unknown, CreateCardInput>({
    mutationFn: async ({ listId, title }) => {
      const { data } = await api.post<Card>(`/api/lists/${listId}/cards`, { title });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["boards", boardId, "lists"] });
    },
  });
}

interface MoveCardInput {
  cardId: string;
  targetListId: string;
}

export function useMoveCard(boardId: string) {
  const queryClient = useQueryClient();
  return useMutation<Card, unknown, MoveCardInput>({
    mutationFn: async ({ cardId, targetListId }) => {
      const { data } = await api.patch<Card>(`/api/cards/${cardId}/move`, {
        target_list_id: targetListId,
      });
      return data;
    },
    onSuccess: () => {
      // The WebSocket broadcast will also trigger this invalidation for
      // OTHER connected clients — this local one covers the actor's own
      // browser tab immediately, without waiting for the round trip.
      queryClient.invalidateQueries({ queryKey: ["boards", boardId, "lists"] });
    },
  });
}

export function useDeleteCard(boardId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, unknown, string>({
    mutationFn: async (cardId) => {
      await api.delete(`/api/cards/${cardId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["boards", boardId, "lists"] });
    },
  });
}
