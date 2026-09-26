import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AxiosError } from "axios";
import { useVerify2FA, useResend2FA } from "../features/auth/useAuth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import type { ApiErrorResponse } from "../lib/api";

interface LocationState {
  email?: string;
}

export default function Verify2FAPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const email = (location.state as LocationState | null)?.email;

  const [code, setCode] = useState("");
  const verify = useVerify2FA();
  const resend = useResend2FA();

  if (!email) {
    // Reached directly without going through login first — send them back.
    navigate("/login");
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await verify.mutateAsync({ email: email as string, code });
      navigate("/workspaces");
    } catch {
      // error shown below
    }
  }

  const errorMessage = (verify.error as AxiosError<ApiErrorResponse> | null)?.response?.data?.detail;

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Enter your code</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-muted-foreground">
            Check the backend's console — the 6-digit code was logged there (no real email
            provider configured yet).
          </p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="code">Code</Label>
              <Input
                id="code"
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
              />
            </div>
            {verify.isError && (
              <p className="text-sm text-destructive">{errorMessage || "Incorrect or expired code"}</p>
            )}
            <Button type="submit" className="w-full" disabled={verify.isPending}>
              {verify.isPending ? "Verifying..." : "Verify"}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              disabled={resend.isPending}
              onClick={() => resend.mutate(email as string)}
            >
              {resend.isPending ? "Sending..." : "Resend code"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
