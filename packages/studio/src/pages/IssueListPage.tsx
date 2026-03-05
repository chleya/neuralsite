import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { issueApi, Issue } from '../api/client';
import IssueCard from '../components/IssueCard';
import styles from './IssueListPage.module.css';

export default function IssueListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [priority, setPriority] = useState(searchParams.get('priority') || '');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 20;

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const res = await issueApi.list({
        page,
        limit,
        status: status || undefined,
        priority: priority || undefined,
      });
      setIssues(res.issues);
      setTotal(res.total);
    } catch (error) {
      console.error('Failed to fetch issues:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, [page, status, priority]);

  const handleStatusChange = (newStatus: string) => {
    setStatus(newStatus);
    setPage(1);
    if (newStatus) {
      setSearchParams({ status: newStatus });
    } else {
      setSearchParams({});
    }
  };

  const handlePriorityChange = (newPriority: string) => {
    setPriority(newPriority);
    setPage(1);
    if (newPriority) {
      setSearchParams({ priority: newPriority });
    } else {
      setSearchParams({});
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这个问题吗？')) return;
    try {
      await issueApi.delete(id);
      setIssues(issues.filter(i => i.id !== id));
    } catch (error) {
      console.error('Failed to delete issue:', error);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="page-container">
      <h1 className="page-title">问题列表</h1>

      <div className={styles.filters}>
        <select
          className="input"
          value={status}
          onChange={(e) => handleStatusChange(e.target.value)}
        >
          <option value="">全部状态</option>
          <option value="open">待处理</option>
          <option value="in_progress">处理中</option>
          <option value="resolved">已解决</option>
          <option value="closed">已关闭</option>
        </select>

        <select
          className="input"
          value={priority}
          onChange={(e) => handlePriorityChange(e.target.value)}
        >
          <option value="">全部优先级</option>
          <option value="low">低</option>
          <option value="medium">中</option>
          <option value="high">高</option>
          <option value="critical">严重</option>
        </select>
      </div>

      {loading ? (
        <div className={styles.loading}>加载中...</div>
      ) : issues.length === 0 ? (
        <div className={styles.empty}>暂无问题</div>
      ) : (
        <>
          <div className={styles.list}>
            {issues.map((issue) => (
              <IssueCard key={issue.id} issue={issue} onDelete={handleDelete} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                className="btn btn-secondary"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                上一页
              </button>
              <span className={styles.pageInfo}>
                第 {page} / {totalPages} 页
              </span>
              <button
                className="btn btn-secondary"
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
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
