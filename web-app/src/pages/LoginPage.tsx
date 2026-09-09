import { useState } from 'react';
import { useNavigate } from '@tanstack/react-router';

const LoginPage = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setMessage('');

    try {
      const response = await fetch('/api/compliance/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          login: email,
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setMessage(data.detail || 'Login failed.');
        return;
      }

      localStorage.setItem('auth_token', 'local_dev_token');
      localStorage.setItem('user', JSON.stringify(data.user));

      window.dispatchEvent(new Event('auth-updated'));

      navigate({ to: '/' });
    } catch (error) {
      console.error(error);

      setMessage('Unable to connect to the server.');
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4">
      <section className="relative w-full max-w-sm rounded-lg border border-border bg-card p-6 shadow-sm">

        {/* Close button */}
        <button
          type="button"
          onClick={() => navigate({ to: '/' })}
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          title="Back to map"
        >
          ×
        </button>

        {/* Header */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-card-foreground">
            HeavyRoute
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            Heavy Vehicle Compliance System
          </p>
        </div>

        <h1 className="text-2xl font-semibold text-card-foreground">
          Sign in
        </h1>

        <p className="mt-2 text-sm text-muted-foreground">
          Sign in to save vehicle preferences and access compliance features.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-6 flex flex-col gap-4"
        >
          {/* Email */}
          <div className="flex flex-col gap-2">
            <label
              htmlFor="email"
              className="text-sm font-medium text-card-foreground"
            >
              Email
            </label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter email"
              required
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Password */}
          <div className="flex flex-col gap-2">
            <label
              htmlFor="password"
              className="text-sm font-medium text-card-foreground"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter password"
              required
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Login */}
          <button
            type="submit"
            className="mt-2 h-10 w-full rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Login
          </button>

          {/* Create account */}
          <button
            type="button"
            onClick={() => navigate({ to: '/signup' })}
            className="h-10 w-full rounded-md border border-border bg-background px-4 text-sm font-medium text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            Create Account
          </button>
        </form>

        {message && (
          <div className="mt-4 rounded-md bg-muted p-3 text-sm text-muted-foreground">
            {message}
          </div>
        )}
      </section>
    </main>
  );
};

export default LoginPage;