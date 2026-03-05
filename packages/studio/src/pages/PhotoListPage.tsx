import { useEffect, useState } from 'react';
import { photoApi, Photo } from '../api/client';
import PhotoCard from '../components/PhotoCard';
import styles from './PhotoListPage.module.css';

export default function PhotoListPage() {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 20;

  const fetchPhotos = async () => {
    setLoading(true);
    try {
      const res = await photoApi.list({ page, limit, search: search || undefined });
      setPhotos(res.photos);
      setTotal(res.total);
    } catch (error) {
      console.error('Failed to fetch photos:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPhotos();
  }, [page]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchPhotos();
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这张照片吗？')) return;
    try {
      await photoApi.delete(id);
      setPhotos(photos.filter(p => p.id !== id));
    } catch (error) {
      console.error('Failed to delete photo:', error);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="page-container">
      <h1 className="page-title">照片管理</h1>

      <form onSubmit={handleSearch} className={styles.searchBar}>
        <input
          type="text"
          className="input"
          placeholder="搜索照片..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit" className="btn btn-primary">搜索</button>
      </form>

      {loading ? (
        <div className={styles.loading}>加载中...</div>
      ) : photos.length === 0 ? (
        <div className={styles.empty}>
          <p>暂无照片</p>
          <a href="/capture" className="btn btn-primary">去拍照</a>
        </div>
      ) : (
        <>
          <div className={styles.grid}>
            {photos.map((photo) => (
              <PhotoCard key={photo.id} photo={photo} onDelete={handleDelete} />
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
