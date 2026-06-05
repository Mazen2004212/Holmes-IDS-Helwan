export default function Footer() {
    return (
        <footer className="text-center py-4 mt-5">
            <div className="container">
                <p className="mb-1">&copy; {new Date().getFullYear()} HOLMES IDS — Hybrid Online Learning Model for Enhanced Security</p>
                <p className="text-muted small">Capital University — Intrusion Detection System</p>
            </div>
        </footer>
    );
}
