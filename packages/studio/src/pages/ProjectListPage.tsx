import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsApi, Project } from '../api/client';
import styles from './ProjectListPage.module.css';

interface ProjectListState {
  projects: Project[];
  loading: boolean;
  page: number;
  total: number;
  limit: number;
  search: string;
}

export default function ProjectListPage() {
  const [state, setState] = useState<ProjectListState>({
    projects: [],
    loading: true,
    page: 1,
    total: 0,
    limit: 10,
    search: '',
  });

  const fetchProjects = async () => {
    setState(prev => ({ ...prev, loading: true }));
    try {
      const res = await projectsApi.list({
        page: state.page,
        limit: state.limit,
        search: state.search || undefined,
      });
      setState(prev => ({
        ...prev,
        projects: res.projects,
        total: res.total,
        loading: false,
      }));
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [state.page, state.limit]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setState(prev => ({ ...prev, page: 1 }));
    fetchProjects();
  };

  const handleDelete = async (projectId: string) => {
    if (!confirm('确定要删除此项目吗？此操作不可恢复。')) return;
    try {
      await projectsApi.delete(projectId);
      setState(prev => ({
        ...prev,
        projects: prev.projects.filter(p => p.project_id !== projectId),
      }));
    } catch (error) {
      console.error('Failed to delete project:', error);
      alert('删除失败，请重试');
    }
  };

  const totalPages = Math.ceil(state.total / state.limit);

  return (
    <div className="page-container">
      <div className={styles.header}>
        <h1 className="page-title">项目管理</h1>
        <Link to="/projects/new" className="btn btn-primary">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          新建项目
        </Link>
      </div>

      <form onSubmit={handleSearch} className={styles.searchForm}>
        <input
          type="text"
          className="input"
          placeholder="搜索项目名称或代码..."
          value={state.search}
          onChange={(e) => setState(prev => ({ ...prev, search: e.target.value }))}
        />
        <button type="submit" className="btn btn-secondary">搜索</button>
      </form>

      {state.loading ? (
        <div className={styles.loading}>加载中...</div>
      ) : state.projects.length === 0 ? (
        <div className={styles.empty}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <p>暂无项目</p>
          <Link to="/projects/new" className="btn btn-primary">创建第一个项目</Link>
        </div>
      ) : (
        <>
          <div className={styles.table}>
            <div className={styles.tableHeader}>
              <div className={styles.colName}>项目名称</div>
              <div className={styles.colCode}>项目代码</div>
              <div className={styles.colLength}>总长度 (m)</div>
              <div className={styles.colDate}>创建时间</div>
              <div className={styles.colActions}>操作</div>
            </div>
            <div className={styles.tableBody}>
              {state.projects.map((project) => (
                <div key={project.project_id} className={styles.tableRow}>
                  <div className={styles.colName}>
                    <Link to={`/projects/${project.project_id}`} className={styles.projectName}>
                      {project.name}
                    </Link>
                    {project.description && (
                      <span className={styles.projectDesc}>{project.description}</span>
                    )}
                  </div>
                  <div className={styles.colCode}>{project.code || '-'}</div>
                  <div className={styles.colLength}>{project.total_length ? `${project.total_length.toLocaleString()}` : '-'}</div>
                  <div className={styles.colDate}>{new Date(project.created_at).toLocaleDateString('zh-CN')}</div>
                  <div className={styles.colActions}>
                    <Link to={`/projects/${project.project_id}`} className={styles.actionBtn} title="查看">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    </Link>
                    <Link to={`/projects/${project.project_id}/edit`} className={styles.actionBtn} title="编辑">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                    </Link>
                    <button
                      className={styles.actionBtnDanger}
                      title="删除"
                      onClick={() => handleDelete(project.project_id)}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                className="btn btn-secondary"
                disabled={state.page === 1}
                onClick={() => setState(prev => ({ ...prev, page: prev.page - 1 }))}
              >
                上一页
              </button>
              <span className={styles.pageInfo}>
                第 {state.page} / {totalPages} 页 (共 {state.total} 条)
              </span>
              <button
                className="btn btn-secondary"
                disabled={state.page === totalPages}
                onClick={() => setState(prev => ({ ...prev, page: prev.page + 1 }))}
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
