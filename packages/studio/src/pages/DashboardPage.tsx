import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { photoApi, issueApi } from '../api/client';
import { ProgressChart, StationDistributionChart, QualityTrendChart } from '../components/charts';
import styles from './DashboardPage.module.css';

interface Stats {
  photos: number;
  issues: number;
  openIssues: number;
  criticalIssues: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({
    photos: 0,
    issues: 0,
    openIssues: 0,
    criticalIssues: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [photosRes, issuesRes] = await Promise.all([
          photoApi.list({ limit: 1 }),
          issueApi.list({ limit: 1 }),
        ]);
        
        setStats({
          photos: photosRes.total,
          issues: issuesRes.total,
          openIssues: issuesRes.issues.filter(i => i.status === 'open').length,
          criticalIssues: issuesRes.issues.filter(i => i.priority === 'critical').length,
        });
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="page-container">加载中...</div>;
  }

  return (
    <div className="page-container">
      <h1 className="page-title">仪表盘</h1>
      
      <div className={styles.statsGrid}>
        <Link to="/photos" className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{stats.photos}</span>
            <span className={styles.statLabel}>照片总数</span>
          </div>
        </Link>

        <Link to="/issues" className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.issueIcon}`}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{stats.openIssues}</span>
            <span className={styles.statLabel}>待处理问题</span>
          </div>
        </Link>

        <Link to="/issues?priority=critical" className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.criticalIcon}`}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              <path d="M12 9v4M12 17h.01" />
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{stats.criticalIssues}</span>
            <span className={styles.statLabel}>严重问题</span>
          </div>
        </Link>

        <div className={styles.statCard}>
          <div className={`${styles.statIcon} ${styles.totalIcon}`}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statValue}>{stats.issues}</span>
            <span className={styles.statLabel}>问题总数</span>
          </div>
        </div>
      </div>

      <div className={styles.quickActions}>
        <h2 className={styles.sectionTitle}>快捷操作</h2>
        <div className={styles.actionGrid}>
          <Link to="/capture" className={styles.actionCard}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <span>拍照采集</span>
          </Link>
          <Link to="/photos" className={styles.actionCard}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <path d="M21 15l-5-5L5 21" />
            </svg>
            <span>照片管理</span>
          </Link>
          <Link to="/issues" className={styles.actionCard}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <path d="M14 2v6h6M12 18v-6M9 15h6" />
            </svg>
            <span>问题列表</span>
          </Link>
        </div>
      </div>

      <div className="mt-8">
        <h2 className={styles.sectionTitle}>数据统计</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px' }}>
          <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '16px' }}>
            <ProgressChart />
          </div>
          <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '16px' }}>
            <StationDistributionChart />
          </div>
        </div>
        <div style={{ marginTop: '16px', background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '16px' }}>
          <QualityTrendChart />
        </div>
      </div>
    </div>
  );
}
