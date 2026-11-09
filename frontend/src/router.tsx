import { createBrowserRouter, Navigate } from 'react-router'
import PermissionRoute from './auth/PermissionRoute'
import ProtectedRoute from './auth/ProtectedRoute'
import Layout from './components/Layout'
import AdminSettingsPage from './pages/AdminSettingsPage'
import AdminUsersPage from './pages/AdminUsersPage'
import BandsPage from './pages/BandsPage'
import ChangePasswordPage from './pages/ChangePasswordPage'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import NewBandPage from './pages/NewBandPage'
import NotFoundPage from './pages/NotFoundPage'
import PublicNotFoundPage from './pages/PublicNotFoundPage'
import SystemStatusPage from './pages/SystemStatusPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <Layout />,
        children: [
          { path: '/status', element: <SystemStatusPage /> },
          { path: '/change-password', element: <ChangePasswordPage /> },
          {
            element: <PermissionRoute permission="bands.read" />,
            children: [{ path: '/bands', element: <BandsPage /> }],
          },
          {
            element: <PermissionRoute permission="bands.write" />,
            children: [{ path: '/bands/new', element: <NewBandPage /> }],
          },
          { path: '/articles', element: <Navigate to="/bands" replace /> },
          { path: '/articles/new', element: <Navigate to="/bands/new" replace /> },
          {
            element: <PermissionRoute permission="users.manage" />,
            children: [{ path: '/admin/users', element: <AdminUsersPage /> }],
          },
          {
            element: <PermissionRoute permission="settings.manage" />,
            children: [{ path: '/admin/settings', element: <AdminSettingsPage /> }],
          },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
  {
    path: '*',
    element: <PublicNotFoundPage />,
  },
])
