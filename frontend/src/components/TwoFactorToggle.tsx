import { useState, type FormEvent } from "react";
import { AxiosError } from "axios";
import { useMe, useEnable2FA, useDisable2FA } from "../features/auth/useAuth";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import type { ApiErrorResponse } from "../lib/api";

export default function TwoFactorToggle() {
  const { data: me } = useMe();
  const enable2FA = useEnable2FA();
  const disable2FA = useDisable2FA();

  const [showPasswordPrompt, setShowPasswordPrompt] = useState(false);
  const [password, setPassword] = useState("");

  if (!me) return null;

  async function handleEnable() {
    await enable2FA.mutateAsync();
  }

  async function handleDisable(e: FormEvent) {
    e.preventDefault();
    try {
      await disable2FA.mutateAsync({ password });
      setShowPasswordPrompt(false);
      setPassword("");
    } catch {
      // error shown below via disable2FA.isError
    }
  }

  const disableError = (disable2FA.error as AxiosError<ApiErrorResponse> | null)?.response?.data?.detail;

  if (!me.is_2fa_enabled) {
    return (
      <Button variant="outline" size="sm" onClick={handleEnable} disabled={enable2FA.isPending}>
        {enable2FA.isPending ? "Enabling..." : "Enable 2FA"}
      </Button>
    );
  }

  if (showPasswordPrompt) {
    return (
      <form onSubmit={handleDisable} className="flex items-center gap-2">
        <Input
          type="password"
          placeholder="Confirm password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="h-8 w-40"
          autoFocus
          required
        />
        <Button type="submit" variant="destructive" size="sm" disabled={disable2FA.isPending}>
          {disable2FA.isPending ? "Disabling..." : "Confirm"}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={() => setShowPasswordPrompt(false)}>
          Cancel
        </Button>
        {disable2FA.isError && <p className="text-xs text-destructive">{disableError || "Incorrect password"}</p>}
      </form>
    );
  }

  return (
    <Button variant="outline" size="sm" onClick={() => setShowPasswordPrompt(true)}>
      Disable 2FA
    </Button>
  );
}