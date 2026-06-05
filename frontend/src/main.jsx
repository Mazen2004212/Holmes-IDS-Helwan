import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

// Bootstrap CSS + JS
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'

// Font Awesome
import '@fortawesome/fontawesome-free/css/all.min.css'

// Custom styles (copies of existing CSS)
import './styles/index.css'

import App from './App.jsx'

createRoot(document.getElementById('root')).render(
    <StrictMode>
        <App />
    </StrictMode>,
)
