import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../api/client';
import styles from './Header.module.css';

export default function Header() {
  const navigate = useNavigate();
  const { logout, user } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <div className={styles.logo}>
          <svg width="28" height="28" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="20" stroke="#4f8cff" strokeWidth="2" />
            <circle cx="24" cy="24" r="8" fill="#4f8cff" />
            <circle cx="24" cy="24" r="3" fill="#0f0f1a" />
          </svg>
          <span className={styles.brand}>NeuralSite</span>
        </div>
      </div>
      
      <div className={styles.right}>
        <span className={styles.username}>{user?.username || '用户'}</span>
        <button className={styles.logoutBtn} onClick={handleLogout}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
            <polyline points="16,17 21,12 16,7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          退出
        </button>
      </div>
    </header>
  );
}
