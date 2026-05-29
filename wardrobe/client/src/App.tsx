import { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import Closet from './pages/Closet';
import AddItem from './pages/AddItem';
import GetOutfit from './pages/GetOutfit';
import GenderSetup from './components/GenderSetup';

export type Gender = 'men' | 'women';

const GENDER_KEY = 'wardrobe_gender';

export function getGender(): Gender | null {
  return (localStorage.getItem(GENDER_KEY) as Gender) ?? null;
}
export function setGender(g: Gender) {
  localStorage.setItem(GENDER_KEY, g);
}

function Shell({ gender, onChangeGender }: { gender: Gender; onChangeGender: () => void }) {
  const location = useLocation();
  const titles: Record<string, string> = {
    '/': 'My Wardrobe',
    '/add': 'Add Item',
    '/outfit': 'Get Outfit',
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.7 }}>
          <path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.57a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.57a2 2 0 0 0-1.34-2.23z"/>
        </svg>
        <span className="tb-logo">{titles[location.pathname] ?? 'My Wardrobe'} <em>CLOSET</em></span>
        <button
          onClick={onChangeGender}
          title="Switch wardrobe"
          style={{ background: 'none', border: 'none', color: 'rgba(255,255,255,.5)', cursor: 'pointer', fontSize: 18, padding: 4, lineHeight: 1 }}
        >
          {gender === 'men' ? '👔' : '👗'}
        </button>
      </header>

      <Routes>
        <Route path="/" element={<Closet />} />
        <Route path="/add" element={<AddItem gender={gender} />} />
        <Route path="/outfit" element={<GetOutfit />} />
      </Routes>

      <nav className="bot-nav">
        <NavLink to="/" end className={({ isActive }) => `bn-item${isActive ? ' active' : ''}`}>
          <span className="bn-ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9,22 9,12 15,12 15,22"/>
            </svg>
          </span>
          Closet
        </NavLink>
        <NavLink to="/add" className={({ isActive }) => `bn-item${isActive ? ' active' : ''}`}>
          <span className="bn-ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="16"/>
              <line x1="8" y1="12" x2="16" y2="12"/>
            </svg>
          </span>
          Add Item
        </NavLink>
        <NavLink to="/outfit" className={({ isActive }) => `bn-item${isActive ? ' active' : ''}`}>
          <span className="bn-ic">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </span>
          Outfit
        </NavLink>
      </nav>
    </div>
  );
}

export default function App() {
  const [gender, setGenderState] = useState<Gender | null>(getGender);
  const [showSetup, setShowSetup] = useState(false);

  function handleChoose(g: Gender) {
    setGender(g);
    setGenderState(g);
    setShowSetup(false);
  }

  if (!gender || showSetup) {
    return <GenderSetup onChoose={handleChoose} />;
  }

  return (
    <BrowserRouter>
      <Shell gender={gender} onChangeGender={() => setShowSetup(true)} />
    </BrowserRouter>
  );
}
