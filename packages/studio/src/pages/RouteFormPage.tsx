import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { routesApi, projectsApi, Project, Route } from '../api/client';
import styles from './RouteFormPage.module.css';

const routeSchema = z.object({
  name: z.string().min(1, '路线名称不能为空').max(100, '路线名称不能超过100个字符'),
  code: z.string().max(50, '路线代码不能超过50个字符').optional(),
  project_id: z.string().optional(),
  start_station: z.number().optional().or(z.string().transform(val => val ? Number(val) : undefined)),
  end_station: z.number().optional().or(z.string().transform(val => val ? Number(val) : undefined)),
  total_length: z.number().optional().or(z.string().transform(val => val ? Number(val) : undefined)),
});

type RouteFormData = z.infer<typeof routeSchema>;

export default function RouteFormPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);
  const [projects, setProjects] = useState<Project[]>([]);

  const defaultProjectId = searchParams.get('project_id');

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<RouteFormData>({
    resolver: zodResolver(routeSchema),
    defaultValues: {
      name: '',
      code: '',
      project_id: defaultProjectId || '',
      start_station: undefined,
      end_station: undefined,
      total_length: undefined,
    },
  });

  useEffect(() => {
    // Fetch projects for selection
    const fetchProjects = async () => {
      try {
        const res = await projectsApi.list({ limit: 100 });
        setProjects(res.projects);
      } catch (error) {
        console.error('Failed to fetch projects:', error);
      }
    };
    fetchProjects();
  }, []);

  useEffect(() => {
    if (isEdit && id) {
      const fetchRoute = async () => {
        try {
          const route = await routesApi.get(id);
          reset({
            name: route.name,
            code: route.code || '',
            project_id: route.project_id || '',
            start_station: route.start_station,
            end_station: route.end_station,
            total_length: route.total_length,
          });
        } catch (error) {
          console.error('Failed to fetch route:', error);
          alert('获取路线信息失败');
          navigate('/routes');
        } finally {
          setFetching(false);
        }
      };
      fetchRoute();
    }
  }, [id, isEdit, reset, navigate]);

  const onSubmit = async (data: RouteFormData) => {
    setLoading(true);
    try {
      if (isEdit && id) {
        await routesApi.update(id, data);
      } else {
        await routesApi.create(data);
      }
      navigate('/routes');
    } catch (error) {
      console.error('Failed to save route:', error);
      alert('保存失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="page-container">
        <div className={styles.loading}>加载中...</div>
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
        <h1 className="page-title">{isEdit ? '编辑路线' : '新建路线'}</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
        <div className={styles.formGroup}>
          <label className={styles.label}>
            路线名称 <span className={styles.required}>*</span>
          </label>
          <input
            type="text"
            className={`input ${errors.name ? styles.inputError : ''}`}
            placeholder="请输入路线名称"
            {...register('name')}
          />
          {errors.name && <span className={styles.error}>{errors.name.message}</span>}
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>路线代码</label>
          <input
            type="text"
            className={`input ${errors.code ? styles.inputError : ''}`}
            placeholder="请输入路线代码（可选）"
            {...register('code')}
          />
          {errors.code && <span className={styles.error}>{errors.code.message}</span>}
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>所属项目</label>
          <select className="input" {...register('project_id')}>
            <option value="">请选择项目（可选）</option>
            {projects.map((project) => (
              <option key={project.project_id} value={project.project_id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.formRow}>
          <div className={styles.formGroup}>
            <label className={styles.label}>起始桩号 (K)</label>
            <input
              type="number"
              step="0.001"
              className="input"
              placeholder="例如: 0"
              {...register('start_station', { valueAsNumber: true })}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>终止桩号 (K)</label>
            <input
              type="number"
              step="0.001"
              className="input"
              placeholder="例如: 100"
              {...register('end_station', { valueAsNumber: true })}
            />
          </div>
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>总长度 (m)</label>
          <input
            type="number"
            step="0.001"
            className="input"
            placeholder="请输入总长度"
            {...register('total_length', { valueAsNumber: true })}
          />
        </div>

        <div className={styles.actions}>
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/routes')}>
            取消
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '保存中...' : '保存'}
          </button>
        </div>
      </form>
    </div>
  );
}
