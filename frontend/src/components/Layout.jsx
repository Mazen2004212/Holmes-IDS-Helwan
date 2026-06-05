import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Footer from './Footer';

/**
 * Main layout wrapper — equivalent to base.html.
 * Renders Navbar, page content (via Outlet), and Footer.
 */
export default function Layout() {
    return (
        <>
            <Navbar />
            <div id="page-content" className="container-fluid mt-4">
                <Outlet />
            </div>
            <Footer />
        </>
    );
}
