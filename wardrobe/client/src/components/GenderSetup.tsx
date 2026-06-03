export default function GenderSetup({ onChoose }: { onChoose: (g: 'men' | 'women') => void }) {
  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'linear-gradient(160deg, #0f172a 0%, #1e3a5f 60%, #2563EB 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9000, padding: 20,
    }}>
      <div style={{ background: 'var(--sf)', borderRadius: 20, width: '100%', maxWidth: 440, overflow: 'hidden', boxShadow: '0 25px 60px rgba(0,0,0,.35)' }}>
        {/* Header */}
        <div style={{ background: 'linear-gradient(135deg,#0f172a,#2563EB)', padding: '32px 24px 24px', color: '#fff', textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🧥</div>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-.4px' }}>My Wardrobe</div>
          <div style={{ fontSize: 13, opacity: .6, marginTop: 6 }}>Smart outfit recommendations from your closet</div>
        </div>

        {/* Body */}
        <div style={{ padding: 24 }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--tx2)', textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: 16 }}>
            Which wardrobe are we building?
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
            <button
              className="btn btn-full"
              style={{ padding: '18px 16px', fontSize: 15, fontWeight: 600, gap: 10, border: '1.5px solid var(--bd)' }}
              onClick={() => onChoose('men')}
            >
              <span style={{ fontSize: 22 }}>👔</span> Menswear
            </button>
            <button
              className="btn btn-full"
              style={{ padding: '18px 16px', fontSize: 15, fontWeight: 600, gap: 10, border: '1.5px solid var(--bd)' }}
              onClick={() => onChoose('women')}
            >
              <span style={{ fontSize: 22 }}>👗</span> Womenswear
            </button>
          </div>

          <p style={{ fontSize: 11, color: 'var(--tx3)', textAlign: 'center' }}>
            You can change this anytime in settings
          </p>
        </div>
      </div>
    </div>
  );
}
