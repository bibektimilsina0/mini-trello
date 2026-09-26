import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  useWorkspaces,
  useCreateWorkspace,
  useBoards,
  useCreateBoard,
} from "../features/workspaces/useWorkspaces";
import { useLogout, useMe } from "../features/auth/useAuth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import TwoFactorToggle from "../components/TwoFactorToggle";

export default function WorkspacesPage() {
  const { data: me } = useMe();
  const { data: workspaces, isLoading } = useWorkspaces();
  const createWorkspace = useCreateWorkspace();
  const logout = useLogout();
  const [newName, setNewName] = useState("");
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);

  async function handleCreateWorkspace(e: FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    await createWorkspace.mutateAsync(newName);
    setNewName("");
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
     <div className="mb-6 flex items-center justify-between">
  <h1 className="text-xl font-semibold">Workspaces {me ? `— ${me.name}` : ""}</h1>
  <div className="flex items-center gap-2">
    <TwoFactorToggle />
    <Button variant="outline" size="sm" onClick={() => logout.mutate()}>
      Log out
    </Button>
  </div>
</div>
      <form onSubmit={handleCreateWorkspace} className="mb-6 flex gap-2">
        <Input placeholder="New workspace name" value={newName} onChange={(e) => setNewName(e.target.value)} />
        <Button type="submit" disabled={createWorkspace.isPending}>
          Create
        </Button>
      </form>

      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}

      <div className="space-y-3">
        {workspaces?.map((ws) => (
          <Card key={ws.id}>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle
                className="cursor-pointer"
                onClick={() => setActiveWorkspaceId(activeWorkspaceId === ws.id ? null : ws.id)}
              >
                {ws.name}
              </CardTitle>
            </CardHeader>
            {activeWorkspaceId === ws.id && <WorkspaceBoards workspaceId={ws.id} />}
          </Card>
        ))}
      </div>
    </div>
  );
}

function WorkspaceBoards({ workspaceId }: { workspaceId: string }) {
  const { data: boards, isLoading } = useBoards(workspaceId);
  const createBoard = useCreateBoard(workspaceId);
  const [title, setTitle] = useState("");

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    await createBoard.mutateAsync(title);
    setTitle("");
  }

  return (
    <CardContent>
      <form onSubmit={handleCreate} className="mb-3 flex gap-2">
        <Input placeholder="New board title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <Button type="submit" size="sm" disabled={createBoard.isPending}>
          Add board
        </Button>
      </form>
      {isLoading && <p className="text-sm text-muted-foreground">Loading boards...</p>}
      <div className="flex flex-wrap gap-2">
        {boards?.map((board) => (
          <Link
            key={board.id}
            to={`/boards/${board.id}`}
            className="rounded-md border border-border px-3 py-1.5 text-sm hover:bg-muted"
          >
            {board.title}
          </Link>
        ))}
      </div>
    </CardContent>
  );
}
