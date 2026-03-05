import { Photo } from '../api/client';
import styles from './PhotoCard.module.css';

interface PhotoCardProps {
  photo: Photo;
  onDelete?: (id: number) => void;
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export default function PhotoCard({ photo, onDelete }: PhotoCardProps) {
  return (
    <div className={styles.card}>
      <div className={styles.imageWrapper}>
        <img src={photo.thumbnail_url || photo.url} alt={photo.filename} />
      </div>
      <div className={styles.content}>
        <h3 className={styles.filename} title={photo.filename}>
          {photo.filename}
        </h3>
        <div className={styles.meta}>
          <span>{photo.width} × {photo.height}</span>
          <span>{formatFileSize(photo.file_size)}</span>
        </div>
        <div className={styles.time}>{formatDate(photo.captured_at)}</div>
        {photo.tags.length > 0 && (
          <div className={styles.tags}>
            {photo.tags.slice(0, 3).map((tag) => (
              <span key={tag} className={styles.tag}>{tag}</span>
            ))}
          </div>
        )}
      </div>
      {onDelete && (
        <button
          className={styles.deleteBtn}
          onClick={() => onDelete(photo.id)}
          title="删除"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3,6 5,6 21,6" />
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
          </svg>
        </button>
      )}
    </div>
  );
}
