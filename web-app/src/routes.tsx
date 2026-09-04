import {
  createRootRoute,
  createRoute,
  createRouter,
  redirect,
  retainSearchParams,
} from '@tanstack/react-router';
import { zodValidator } from '@tanstack/zod-adapter';
import { App } from './app';
import { RootComponent } from './components/root-component';
import * as TanStackQueryProvider from './lib/tanstack-query/root-provider';
import { searchParamsSchema, isValidTab } from './utils/route-schemas';
import type { Profile } from './stores/common-store';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProfilePage from './pages/ProfilePage';
import AddVehiclePage from './pages/AddVehiclePage';
import EditVehiclePage from './pages/EditVehiclePage';

const defaultProfile = ((import.meta.env
  .VITE_DEFAULT_COSTING_MODEL as string) || 'bicycle') as Profile;

export const rootRoute = createRootRoute({ component: RootComponent });

const TanStackQueryProviderContext = TanStackQueryProvider.getContext();

export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: App,
  beforeLoad: () => {
    throw redirect({
      to: '/$activeTab',
      params: { activeTab: 'directions' },
      search: {
        profile: defaultProfile,
      },
    });
  },
});

const activeTabRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/$activeTab',
  component: App,
  validateSearch: zodValidator(searchParamsSchema),
  search: {
    middlewares: [
      retainSearchParams([
        'profile',
        'style',
        'use_ferry',
        'use_highways',
        'use_tolls',
        'alternates',
        'lang',
      ]),
    ],
  },
  beforeLoad: ({ params, search }) => {
    if (!isValidTab(params.activeTab)) {
      throw redirect({
        to: '/$activeTab',
        params: { activeTab: 'directions' },
        search: {
          profile: defaultProfile,
        },
      });
    }
    if (!search.profile) {
      throw redirect({
        to: '/$activeTab',
        params: { activeTab: params.activeTab },
        search: {
          ...search,
          profile: defaultProfile,
        },
      });
    }
  },
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage,
});

const signupRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/signup',
  component: SignupPage,
});

const profileRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/profile',
  component: ProfilePage,
});

const addVehicleRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/admin/add-vehicle',
  component: AddVehiclePage,
});

const editVehicleRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/admin/edit-vehicle',
  component: EditVehiclePage,
});

export const routeTree = rootRoute.addChildren([
  indexRoute,
  activeTabRoute,
  loginRoute,
  signupRoute,
  profileRoute,
  addVehicleRoute,
  editVehicleRoute,
  
]);

export const router = createRouter({
  routeTree,
  context: { ...TanStackQueryProviderContext },
  defaultPreload: 'intent',
  scrollRestoration: true,
  defaultStructuralSharing: true,
  defaultPreloadStaleTime: 0,
  basepath: import.meta.env.BASE_URL,
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
