import { useState, type FormEvent } from "react";
import { useParams, Link } from "react-router-dom";
import {
  useBoard,
  useBoardLists,
  useCreateList,
  useCreateCard,
  useMoveCard,
  useDeleteCard,
} from "../features/boards/useBoard";
import { useBoardWebSocket } from "../hooks/useWebSocket";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import type { Card as CardType, ListWithCards } from "../types/api";

export default function BoardPage() {
  const { boardId } = useParams<{ boardId: string }>();
  const { data: board } = useBoard(boardId);
  const { data: lists, isLoading } = useBoardLists(boardId);

  // Live sync: any card create/update/move/delete from another connected
  // client re-fetches this board's lists automatically.
  useBoardWebSocket(boardId);

  return (
    <div className="min-h-screen p-6">
      <div className="mb-6 flex items-center gap-3">
        <Link to="/workspaces" className="text-sm text-muted-foreground hover:underline">
          ← Workspaces
        </Link>
        <h1 className="text-xl font-semibold">{board?.title}</h1>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading board...</p>}

      <div className="flex gap-4 overflow-x-auto pb-4">
        {lists?.map((list) => (
          <ListColumn key={list.id} list={list} boardId={boardId as string} allLists={lists} />
        ))}
        <NewListForm boardId={boardId as string} />
      </div>
    </div>
  );
}

function NewListForm({ boardId }: { boardId: string }) {
  const [title, setTitle] = useState("");
  const createList = useCreateList(boardId);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    await createList.mutateAsync(title);
    setTitle("");
  }

  return (
    <form onSubmit={handleSubmit} className="w-64 shrink-0">
      <Input placeholder="+ Add a list" value={title} onChange={(e) => setTitle(e.target.value)} />
    </form>
  );
}

interface ListColumnProps {
  list: ListWithCards;
  boardId: string;
  allLists: ListWithCards[];
}

function ListColumn({ list, boardId, allLists }: ListColumnProps) {
  const createCard = useCreateCard(boardId);
  const [title, setTitle] = useState("");

  async function handleAddCard(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    await createCard.mutateAsync({ listId: list.id, title });
    setTitle("");
  }

  return (
    <div className="w-64 shrink-0">
      <Card className="bg-muted">
        <CardHeader>
          <CardTitle>{list.title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {list.cards.map((card) => (
            <CardItem key={card.id} card={card} boardId={boardId} currentListId={list.id} allLists={allLists} />
          ))}
          <form onSubmit={handleAddCard} className="pt-2">
            <Input placeholder="+ Add a card" value={title} onChange={(e) => setTitle(e.target.value)} />
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

interface CardItemProps {
  card: CardType;
  boardId: string;
  currentListId: string;
  allLists: ListWithCards[];
}

function CardItem({ card, boardId, currentListId, allLists }: CardItemProps) {
  const moveCard = useMoveCard(boardId);
  const deleteCard = useDeleteCard(boardId);

  const currentIndex = allLists.findIndex((l) => l.id === currentListId);
  const prevList = allLists[currentIndex - 1];
  const nextList = allLists[currentIndex + 1];

  return (
    <div className="rounded-md border border-border bg-background p-2 text-sm shadow-sm">
      <p className="mb-1">{card.title}</p>
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {prevList && (
            <button
              className="text-xs text-muted-foreground hover:underline"
              onClick={() => moveCard.mutate({ cardId: card.id, targetListId: prevList.id })}
              title={`Move to ${prevList.title}`}
            >
              ←
            </button>
          )}
          {nextList && (
            <button
              className="text-xs text-muted-foreground hover:underline"
              onClick={() => moveCard.mutate({ cardId: card.id, targetListId: nextList.id })}
              title={`Move to ${nextList.title}`}
            >
              →
            </button>
          )}
        </div>
        <button className="text-xs text-destructive hover:underline" onClick={() => deleteCard.mutate(card.id)}>
          delete
        </button>
      </div>
    </div>
  );
}
