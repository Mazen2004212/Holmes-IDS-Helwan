import { useState, createContext, useContext, useCallback } from 'react';

const FlashContext = createContext(null);

export function FlashProvider({ children }) {
    const [messages, setMessages] = useState([]);

    const flash = useCallback((text, type = 'info') => {
        const id = Date.now();
        setMessages(prev => [...prev, { id, text, type }]);
        setTimeout(() => {
            setMessages(prev => prev.filter(m => m.id !== id));
        }, 5000);
    }, []);

    return (
        <FlashContext.Provider value={flash}>
            {children}
            <div className="position-fixed top-0 end-0 p-3" style={{ zIndex: 9999 }}>
                {messages.map(m => (
                    <div
                        key={m.id}
                        className={`alert alert-${m.type} alert-dismissible fade show`}
                        role="alert"
                    >
                        {m.text}
                        <button
                            type="button"
                            className="btn-close"
                            onClick={() => setMessages(prev => prev.filter(msg => msg.id !== m.id))}
                        />
                    </div>
                ))}
            </div>
        </FlashContext.Provider>
    );
}

export function useFlash() {
    const ctx = useContext(FlashContext);
    if (!ctx) throw new Error('useFlash must be used within FlashProvider');
    return ctx;
}
