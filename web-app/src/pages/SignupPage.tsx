import { useState } from 'react';
import { useNavigate } from '@tanstack/react-router';

const SignupPage = () => {
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [licenceClass, setLicenceClass] = useState('');
  const [message, setMessage] = useState('');

    async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setMessage('');

    try {
        const response = await fetch('/api/compliance/auth/signup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            email: email,
            password: password,
            licence_class_id: licenceClass || null,
        }),
        });

        const data = await response.json();

        if (!response.ok) {
        setMessage(data.detail || 'Signup failed.');
        return;
        }

        setMessage('Account created successfully.');

        console.log('Signup response:', data);
    } catch (error) {
        console.error(error);

        setMessage('Unable to connect to the server.');
    }
    }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4">
      <section className="relative w-full max-w-sm rounded-lg border border-border bg-card p-6 shadow-sm">

        <button
          type="button"
          onClick={() => navigate({ to: '/' })}
          className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          title="Back to map"
        >
          ×
        </button>

        <div className="mb-6">
          <h2 className="text-lg font-semibold text-card-foreground">
            HeavyRoute
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            Heavy Vehicle Compliance System
          </p>
        </div>

        <h1 className="text-2xl font-semibold text-card-foreground">
          Create account
        </h1>

        <p className="mt-2 text-sm text-muted-foreground">
          Create an account to save vehicles and compliance preferences.
        </p>

        <form
          onSubmit={handleSubmit}
          className="mt-6 flex flex-col gap-4"
        >
          <div className="flex flex-col gap-2">
            <label
              htmlFor="username"
              className="text-sm font-medium text-card-foreground"
            >
              Username
            </label>

            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Enter username"
              required
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
            />
          </div>

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

          <div className="flex flex-col gap-2">
            <label
              htmlFor="licenceClass"
              className="text-sm font-medium text-card-foreground"
            >
              Licence Class
            </label>

            <select
              id="licenceClass"
              value={licenceClass}
              onChange={(event) => setLicenceClass(event.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">
                — Select licence class —
              </option>

              <option value="MC">
                MC — Multi Combination
              </option>

              <option value="HC">
                HC — Heavy Combination
              </option>

              <option value="HR">
                HR — Heavy Rigid
              </option>

              <option value="MR">
                MR — Medium Rigid
              </option>

              <option value="LR">
                LR — Light Rigid
              </option>
            </select>
          </div>

          <button
            type="submit"
            className="mt-2 h-10 w-full rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Sign up
          </button>

          <button
            type="button"
            onClick={() => navigate({ to: '/login' })}
            className="h-10 w-full rounded-md border border-border bg-background px-4 text-sm font-medium text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            Back to Login
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

export default SignupPage;