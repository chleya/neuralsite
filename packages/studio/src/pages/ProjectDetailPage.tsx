import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { projectsApi, Project, routesApi, Route } from '../api/client';
import styles from './ProjectDetailPage.module.css';

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      try {
        const [projectData, routesData] = await Promise.all([
          projectsApi.get(id),
          routesApi.getByProject(id),
        ]);
        setProject(projectData);
        setRoutes(routesData.routes);
      } catch (error) {
        console.error('Failed to fetch project:', error);
        alert('获取项目信息失败');
        navigate('/projects');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, navigate]);

  const handleDelete = async () => {
    if (!id || !confirm('确定要删除此项目吗？此操作不可恢复。')) return;
    try {
      await projectsApi.delete(id);
      navigate('/projects');
    } catch (error) {
      console.error('Failed to delete project:', error);
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

  if (!project) {
    return (
      <div className="page-container">
        <div className={styles.notFound}>项目不存在</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className={styles.header}>
        <button className={styles.backBtn} onClick={() => navigate('/projects')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="page-title">{project.name}</h1>
        <div className={styles.headerActions}>
          <Link to={`/projects/${id}/edit`} className="btn btn-secondary">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            编辑
          </Link>
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
          <h2 className={styles.cardTitle}>项目信息</h2>
          <div className={styles.infoGrid}>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>项目代码</span>
              <span className={styles.infoValue}>{project.code || '-'}</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>起始桩号</span>
              <span className={styles.infoValue}>
                {project.start_station !== undefined ? `K${project.start_station.toFixed(3)}` : '-'}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>终止桩号</span>
              <span className={styles.infoValue}>
                {project.end_station !== undefined ? `K${project.end_station.toFixed(3)}` : '-'}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>总长度</span>
              <span className={styles.infoValue}>
                {project.total_length ? `${project.total_length.toLocaleString()} m` : '-'}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>创建时间</span>
              <span className={styles.infoValue}>
                {new Date(project.created_at).toLocaleString('zh-CN')}
              </span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>更新时间</span>
              <span className={styles.infoValue}>
                {new Date(project.updated_at).toLocaleString('zh-CN')}
              </span>
            </div>
          </div>
          {project.description && (
            <div className={styles.description}>
              <span className={styles.infoLabel}>项目描述</span>
              <p>{project.description}</p>
            </div>
          )}
        </div>

        <div className={styles.routesCard}>
          <div className={styles.routesHeader}>
            <h2 className={styles.cardTitle}>路线列表</h2>
            <Link to={`/routes/new?project_id=${id}`} className="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12h14" />
              </svg>
              新建路线
            </Link>
          </div>
          {routes.length === 0 ? (
            <div className={styles.emptyRoutes}>
              <p>暂无路线</p>
            </div>
          ) : (
            <div className={styles.routesList}>
              {routes.map((route) => (
                <Link
                  key={route.route_id}
                  to={`/routes/${route.route_id}`}
                  className={styles.routeItem}
                >
                  <div className={styles.routeInfo}>
                    <span className={styles.routeName}>{route.name}</span>
                    <span className={styles.routeCode}>{route.code || '-'}</span>
                  </div>
                  <div className={styles.routeLength}>
                    {route.total_length ? `${route.total_length.toLocaleString()} m` : '-'}
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
