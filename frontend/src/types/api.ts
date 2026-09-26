export interface User {
  id: string;
  email: string;
  name: string;
  is_email_verified: boolean;
  is_2fa_enabled: boolean;
}

export interface LoginResponse {
  user: User | null;
  requires_2fa: boolean;
}

export interface Workspace {
  id: string;
  name: string;
  owner_id: string;
  created_at: string;
}

export type WorkspaceRole = "owner" | "member";

export interface WorkspaceMember {
  user_id: string;
  email: string;
  name: string;
  role: WorkspaceRole;
}

export interface Board {
  id: string;
  workspace_id: string;
  title: string;
  created_by: string;
  created_at: string;
}

export interface List {
  id: string;
  board_id: string;
  title: string;
  position: number;
}

export interface ListWithCards extends List {
  cards: Card[];
}

export interface Card {
  id: string;
  list_id: string;
  title: string;
  description: string | null;
  position: number;
  due_date: string | null;
  assignee_id: string | null;
  created_at: string;
}

export interface Comment {
  id: string;
  card_id: string;
  user_id: string;
  author_name: string;
  body: string;
  created_at: string;
}

export interface MessageResponse {
  message: string;
}

// WebSocket event envelope — matches build_event() on the backend.
export type BoardEventType = "card_created" | "card_updated" | "card_moved" | "card_deleted";

export interface BoardEvent<T = unknown> {
  type: BoardEventType;
  payload: T;
}
