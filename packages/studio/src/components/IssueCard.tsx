import { Issue } from '../api/client';
import styles from './IssueCard.module.css';

interface IssueCardProps {
  issue: Issue;
  onDelete?: (id: number) => void;
}

const statusMap = {
  open: { label: '待处理', className: styles.statusOpen },
  in_progress: { label: '处理中', className: styles.statusProgress },
  resolved: { label: '已解决', className: styles.statusResolved },
  closed: { label: '已关闭', className: styles.statusClosed },
};

const priorityMap = {
  low: { label: '低', className: styles.priorityLow },
  medium: { label: '中', className: styles.priorityMedium },
  high: { label: '高', className: styles.priorityHigh },
  critical: { label: '严重', className: styles.priorityCritical },
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export default function IssueCard({ issue, onDelete }: IssueCardProps) {
  const status = statusMap[issue.status];
  const priority = priorityMap[issue.priority];

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.title}>{issue.title}</h3>
        <div className={styles.badges}>
          <span className={`${styles.status} ${status.className}`}>{status.label}</span>
          <span className={`${styles.priority} ${priority.className}`}>{priority.label}</span>
        </div>
      </div>
      
      <p className={styles.description}>{issue.description}</p>
      
      {issue.photos.length > 0 && (
        <div className={styles.photos}>
          {issue.photos.slice(0, 4).map((photo) => (
            <div key={photo.id} className={styles.photoThumb}>
              <img src={photo.thumbnail_url || photo.url} alt="" />
            </div>
          ))}
          {issue.photos.length > 4 && (
            <div className={styles.morePhotos}>+{issue.photos.length - 4}</div>
          )}
        </div>
      )}
      
      <div className={styles.footer}>
        <span className={styles.time}>更新于 {formatDate(issue.updated_at)}</span>
        {onDelete && (
          <button className={styles.deleteBtn} onClick={() => onDelete(issue.id)}>
            删除
          </button>
        )}
      </div>
    </div>
  );
}
