import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { useVerifyEmail } from "../features/auth/useAuth";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";

type Status = "verifying" | "success" | "error";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const verifyEmail = useVerifyEmail();
  const [status, setStatus] = useState<Status>("verifying");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }
    verifyEmail.mutate(token, {
      onSuccess: () => setStatus("success"),
      onError: () => setStatus("error"),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Email verification</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          {status === "verifying" && <p>Verifying...</p>}
          {status === "success" && (
            <>
              <p>Your email is verified. You can log in now.</p>
              <Link to="/login" className="underline">
                Go to login
              </Link>
            </>
          )}
          {status === "error" && (
            <p className="text-destructive">
              This link is invalid or expired. Try signing up again, or request a new link.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
