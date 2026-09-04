import { useEffect, useRef, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';

interface User {
  user_id: number;
  email: string;
  username: string;
  licence_class_id?: string | null;
  favourite_profile_id?: string | null;
}

function getStoredUser(): User | null {
  try {
    const storedUser = localStorage.getItem('user');

    return storedUser
      ? (JSON.parse(storedUser) as User)
      : null;
  } catch {
    return null;
  }
}

export const UserChip = () => {
  const navigate = useNavigate();

  const [user, setUser] = useState<User | null>(
    getStoredUser()
  );

  const [menuOpen, setMenuOpen] = useState(false);

  const wrapperRef = useRef<HTMLDivElement>(null);

  const isLoggedIn =
    !!localStorage.getItem('auth_token') &&
    !!user;

  /*
   * Refresh user information after login/logout.
   */
  function refreshAuth() {
    setUser(getStoredUser());
  }

  /*
   * Close dropdown when clicking outside.
   */
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(
          event.target as Node
        )
      ) {
        setMenuOpen(false);
      }
    }

    window.addEventListener(
      'auth-updated',
      refreshAuth
    );

    document.addEventListener(
      'mousedown',
      handleClickOutside
    );

    return () => {
      window.removeEventListener(
        'auth-updated',
        refreshAuth
      );

      document.removeEventListener(
        'mousedown',
        handleClickOutside
      );
    };
  }, []);

  /*
   * Navigation
   */
  function goLogin() {
    setMenuOpen(false);

    navigate({
      to: '/login',
    });
  }

  function goSignup() {
    setMenuOpen(false);

    navigate({
      to: '/signup',
    });
  }

  function goProfile() {
    setMenuOpen(false);

    navigate({
      to: '/profile',
    });
  }

  function goAddVehicle() {
    setMenuOpen(false);

    navigate({
      to: '/admin/add-vehicle',
    });
  }

  function goEditVehicle() {
    setMenuOpen(false);

    navigate({
      to: '/admin/edit-vehicle',
    });
  }

  /*
   * Logout
   */
  function signOut() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');

    sessionStorage.removeItem(
      'guest_selected_licence_class'
    );

    sessionStorage.removeItem(
      'p1_selected_licence_class'
    );

    setUser(null);
    setMenuOpen(false);

    window.dispatchEvent(
      new Event('auth-updated')
    );

    /*
     * Full refresh also clears Valhalla /
     * compliance component state.
     */
    window.location.assign('/');
  }

  /*
   * Display name
   *
   * If username accidentally contains an email,
   * only show the part before @.
   */
  const displayName = (() => {
    if (!user) {
      return 'Guest';
    }

    const name =
      user.username ||
      user.email ||
      'User';

    if (name.includes('@')) {
      return name.split('@')[0] ?? name;
    }

    return name;
  })();

  const initial = isLoggedIn
    ? displayName.charAt(0).toUpperCase()
    : 'G';

  return (
    <div
      ref={wrapperRef}
      className="relative"
    >
      {/* User chip */}
      <button
        type="button"
        onClick={() =>
          setMenuOpen((current) => !current)
        }
        className="flex items-center gap-2 rounded-full border border-border bg-background px-2.5 py-1.5 transition-colors hover:bg-accent"
      >
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
          {initial}
        </div>

        <span className="max-w-[100px] truncate text-sm font-medium text-foreground">
          {displayName}
        </span>

        <span
          className={`text-xs text-muted-foreground transition-transform ${
            menuOpen ? 'rotate-180' : ''
          }`}
        >
          ▾
        </span>
      </button>

      {/* Dropdown */}
      {menuOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-52 rounded-md border border-border bg-popover p-1 shadow-md">
          {!isLoggedIn ? (
            <>
              <button
                type="button"
                onClick={goLogin}
                className="w-full rounded-sm px-3 py-2 text-left text-sm text-popover-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                Login
              </button>

              <button
                type="button"
                onClick={goSignup}
                className="w-full rounded-sm px-3 py-2 text-left text-sm text-popover-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                Sign up
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={goProfile}
                className="w-full rounded-sm px-3 py-2 text-left text-sm text-popover-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                Configure Profile
              </button>

              <div className="my-1 border-t border-border" />

              <button
                type="button"
                onClick={goAddVehicle}
                className="w-full rounded-sm px-3 py-2 text-left text-sm text-popover-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                Add Vehicle Type
              </button>

              <button
                type="button"
                onClick={goEditVehicle}
                className="w-full rounded-sm px-3 py-2 text-left text-sm text-popover-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                Edit Vehicle Type
              </button>

              <div className="my-1 border-t border-border" />

              <button
                type="button"
                onClick={signOut}
                className="w-full rounded-sm px-3 py-2 text-left text-sm text-destructive transition-colors hover:bg-destructive/10"
              >
                Sign out
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};