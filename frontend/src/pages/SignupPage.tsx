import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { AxiosError } from "axios";
import { useSignup } from "../features/auth/useAuth";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";
import type { ApiErrorResponse } from "../lib/api";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const signup = useSignup();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    try {
      await signup.mutateAsync({ email, name, password });
      setDone(true);
    } catch {
      // error shown below via signup.isError
    }
  }

  const errorMessage = (signup.error as AxiosError<ApiErrorResponse> | null)?.response?.data?.detail;

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle>Check your terminal</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Account created. The verification link was logged to the backend's console
            (no real email provider configured yet). Copy the token from there and visit{" "}
            <Link className="underline" to="/verify-email">
              /verify-email?token=...
            </Link>
            .
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Create an account</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="name">Name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {signup.isError && <p className="text-sm text-destructive">{errorMessage || "Something went wrong"}</p>}
            <Button type="submit" className="w-full" disabled={signup.isPending}>
              {signup.isPending ? "Creating account..." : "Sign up"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="underline">
              Log in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
