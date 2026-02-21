import React from 'react'
import ReactDOM from 'react-dom/client'
import { Auth0Provider } from '@auth0/auth0-react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

const queryClient = new QueryClient()

const domain = import.meta.env.VITE_AUTH0_DOMAIN || ''
const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID || ''

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: window.location.origin,
        scope: 'openid profile email offline_access',
        audience: import.meta.env.VITE_AUTH0_AUDIENCE || `https://${domain}/api/v2/`
      }}
      cacheLocation="localstorage"
      useRefreshTokens={true}
    >
      <QueryClientProvider client={queryClient}>
        <App />
        <Toaster position="top-right" />
      </QueryClientProvider>
    </Auth0Provider>
  </React.StrictMode>,
)
