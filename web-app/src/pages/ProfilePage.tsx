import { useEffect, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';

interface User {
  user_id: number;
  email: string;
  username: string;
  licence_class_id?: string | null;
  favourite_profile_id?: string | null;
}

interface VehicleProfile {
  profile_id: string;
  display_name: string;
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

const ProfilePage = () => {
  const navigate = useNavigate();

  const [user, setUser] = useState<User | null>(
    getStoredUser()
  );

  const [licenceClass, setLicenceClass] = useState('');
  const [favouriteProfileId, setFavouriteProfileId] =
    useState('');

  const [profiles, setProfiles] = useState<
    VehicleProfile[]
  >([]);

  const [profilesLoading, setProfilesLoading] =
    useState(false);

  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  /*
   * Initialise profile values from localStorage.
   */
  useEffect(() => {
    if (!user) {
      return;
    }

    setLicenceClass(user.licence_class_id ?? '');

    setFavouriteProfileId(
      user.favourite_profile_id ?? ''
    );
  }, [user]);

  /*
   * Whenever licence changes,
   * load the vehicles allowed by that licence.
   */
  useEffect(() => {
    async function loadProfiles() {
      setProfiles([]);
      setError('');

      if (!licenceClass) {
        return;
      }

      setProfilesLoading(true);

      try {
        const response = await fetch(
          `/api/compliance/profiles-by-licence/${licenceClass}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
              'Failed to load vehicle profiles.'
          );
        }

        const loadedProfiles: VehicleProfile[] =
          Array.isArray(data) ? data : [];

        setProfiles(loadedProfiles);

        /*
         * If the currently saved favourite vehicle
         * does not belong to the newly selected licence,
         * clear it.
         */
        const favouriteStillAvailable =
          loadedProfiles.some(
            (profile) =>
              profile.profile_id ===
              favouriteProfileId
          );

        if (!favouriteStillAvailable) {
          setFavouriteProfileId('');
        }
      } catch (error) {
        console.error(
          'Failed to load vehicle profiles:',
          error
        );

        if (error instanceof Error) {
          setError(error.message);
        } else {
          setError(
            'Failed to load vehicle profiles.'
          );
        }
      } finally {
        setProfilesLoading(false);
      }
    }

    loadProfiles();
  }, [licenceClass]);

  /*
   * Save profile to Flask.
   */
  async function saveProfile() {
    setMessage('');
    setError('');

    if (!user) {
      setError(
        'You must be logged in to configure your profile.'
      );

      return;
    }

    if (!licenceClass) {
      setError('Please select a licence class.');

      return;
    }

    setSaving(true);

    try {
      const response = await fetch(
        `/api/compliance/auth/users/${user.user_id}/profile`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            licence_class_id: licenceClass,
            favourite_profile_id:
              favouriteProfileId || null,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            'Failed to update profile.'
        );
      }

      /*
       * Prefer the updated user returned by Flask.
       *
       * If Flask does not return one,
       * update our existing local user manually.
       */
      const updatedUser: User = data.user
        ? data.user
        : {
            ...user,
            licence_class_id: licenceClass,
            favourite_profile_id:
              favouriteProfileId || null,
          };

      localStorage.setItem(
        'user',
        JSON.stringify(updatedUser)
      );

      setUser(updatedUser);

      /*
       * Tell UserChip and Compliance Engine
       * that the user's profile changed.
       */
      window.dispatchEvent(
        new Event('auth-updated')
      );

      setMessage(
        'Profile updated successfully.'
      );
    } catch (error) {
      console.error(
        'Failed to update profile:',
        error
      );

      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('Failed to update profile.');
      }
    } finally {
      setSaving(false);
    }
  }

  /*
   * If somebody manually visits /profile
   * while not logged in.
   */
  if (!user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background p-4">
        <section className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-sm">
          <h1 className="text-xl font-semibold">
            Configure Profile
          </h1>

          <p className="mt-2 text-sm text-muted-foreground">
            You need to sign in before configuring
            your profile.
          </p>

          <div className="mt-6 flex gap-2">
            <button
              type="button"
              onClick={() =>
                navigate({ to: '/login' })
              }
              className="h-10 flex-1 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Login
            </button>

            <button
              type="button"
              onClick={() =>
                navigate({ to: '/' })
              }
              className="h-10 flex-1 rounded-md border border-border bg-background px-4 text-sm font-medium hover:bg-accent"
            >
              Back to Map
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4">
      <section className="relative w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-sm">

        {/* Close */}
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
          <h2 className="text-lg font-semibold">
            HeavyRoute
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            Heavy Vehicle Compliance System
          </p>
        </div>

        <h1 className="text-2xl font-semibold">
          Configure Profile
        </h1>

        <p className="mt-2 text-sm text-muted-foreground">
          Set your default licence class and favourite
          vehicle.
        </p>

        {/* Account */}
        <div className="mt-6 rounded-md bg-muted p-4">
          <p className="text-xs text-muted-foreground">
            Signed in as
          </p>

          <p className="mt-1 text-sm font-medium">
            {user.username}
          </p>

          <p className="text-xs text-muted-foreground">
            {user.email}
          </p>
        </div>

        <div className="mt-6 flex flex-col gap-5">

          {/* Licence */}
          <div className="flex flex-col gap-2">
            <label
              htmlFor="profile-licence"
              className="text-sm font-medium"
            >
              Licence Class
            </label>

            <select
              id="profile-licence"
              value={licenceClass}
              onChange={(event) => {
                setLicenceClass(
                  event.target.value
                );

                setMessage('');
                setError('');
              }}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-ring"
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

          {/* Favourite Vehicle */}
          <div className="flex flex-col gap-2">
            <label
              htmlFor="favourite-profile"
              className="text-sm font-medium"
            >
              Favourite Vehicle
            </label>

            <select
              id="favourite-profile"
              value={favouriteProfileId}
              onChange={(event) => {
                setFavouriteProfileId(
                  event.target.value
                );

                setMessage('');
                setError('');
              }}
              disabled={
                !licenceClass ||
                profilesLoading
              }
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-50 focus:ring-2 focus:ring-ring"
            >
              <option value="">
                {profilesLoading
                  ? 'Loading vehicles...'
                  : '— No favourite vehicle —'}
              </option>

              {profiles.map((profile) => (
                <option
                  key={profile.profile_id}
                  value={profile.profile_id}
                >
                  {profile.display_name}
                </option>
              ))}
            </select>

            <p className="text-xs text-muted-foreground">
              Only vehicles permitted by the selected
              licence are shown.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Success */}
          {message && (
            <div className="rounded-md border border-green-500/30 bg-green-500/10 p-3 text-sm">
              {message}
            </div>
          )}

          {/* Save */}
          <button
            type="button"
            onClick={saveProfile}
            disabled={saving}
            className="h-10 w-full rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving
              ? 'Saving...'
              : 'Save Profile'}
          </button>
        </div>
      </section>
    </main>
  );
};

export default ProfilePage;