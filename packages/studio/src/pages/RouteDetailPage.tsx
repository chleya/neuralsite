import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { routesApi, projectsApi, Route, Project } from '../api/client';
import styles from './RouteDetailPage.module.css';

export default function RouteDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [route, setRoute] = useState<Route | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      try {
        const routeData = await routesApi.get(id);
        setRoute(routeData);

        if (routeData.project_id) {
          try {
            const projectData = await projectsApi.get(routeData.project_id);
            setProject(projectData);
          } catch {
            // Project might have been deleted
          }
        }
      } catch (error) {
        console.error('Failed to fetch route:', error);
        alert('获取路线信息失败');
        navigate('/routes');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, navigate]);

  const handleDelete = async () => {
    if (!id || !confirm('确定要删除此路线吗？此操作不可恢复。')) return;
    try {
      await routesApi.delete(id);
      navigate('/routes');
    } catch (error) {
      console.error('Failed to delete route:', error);
      alert('删除失败，请重试');
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className={styles.loading}>加载中...</div>
      </div>
    );
  }

  if (!route) {
    return (
      <div className="page-container">
        <div className={styles.notFound}>路线不存在</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={() => navigate('/routes')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="page-title">{route.name}</h1>
        <div className={styles.headerActions}>
          <button className="btn btn-secondary" onClick={() => navigate(`/routes/${id}/edit`)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            编辑
          </button>
          <button className="btn btn-danger" onClick={handleDelete}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
            </svg>
            删除
          </button>
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.infoCard}>
          <h2 className={styles.cardTitle}>路线信息</h2>
          <div className={styles.infoGrid}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>路线代码</span>
              <span className={styles.infoValue}>{route.code || '-'}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>所属项目</span>
              <span className={styles.infoValue}>
                {project ? (
                  <a href={`/projects/${project.project_id}`} className={styles.link}>
                    {project.name}
                  </a>
                ) : route.project_id || '-'}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>起始桩号</span>
              <span className={styles.infoValue}>
                {route.start_station !== undefined ? `K${route.start_station.toFixed(3)}` : '-'}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>终止桩号</span>
              <span className={styles.infoValue}>
                {route.end_station !== undefined ? `K${route.end_station.toFixed(3)}` : '-'}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>总长度</span>
              <span className={styles.infoValue}>
                {route.total_length ? `${route.total_length.toLocaleString()} m` : '-'}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>创建时间</span>
              <span className={styles.infoValue}>
                {new Date(route.created_at).toLocaleString('zh-CN')}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>更新时间</span>
              <span className={styles.infoValue}>
                {new Date(route.updated_at).toLocaleString('zh-CN')}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
