import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { projectsApi, Project } from '../api/client';
import styles from './ProjectFormPage.module.css';

const projectSchema = z.object({
  name: z.string().min(1, '项目名称不能为空').max(100, '项目名称不能超过100个字符'),
  code: z.string().max(50, '项目代码不能超过50个字符').optional(),
  description: z.string().max(500, '描述不能超过500个字符').optional(),
  start_station: z.number().optional().or(z.string().transform(val => val ? Number(val) : undefined)),
  end_station: z.number().optional().or(z.string().transform(val => val ? Number(val) : undefined)),
  total_length: z.number().optional().or(z.string().transform(val => val ? Number(val) : undefined)),
});

type ProjectFormData = z.infer<typeof projectSchema>;

export default function ProjectFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(isEdit);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: '',
      code: '',
      description: '',
      start_station: undefined,
      end_station: undefined,
      total_length: undefined,
    },
  });

  useEffect(() => {
    if (isEdit && id) {
      const fetchProject = async () => {
        try {
          const project = await projectsApi.get(id);
          reset({
            name: project.name,
            code: project.code || '',
            description: project.description || '',
            start_station: project.start_station,
            end_station: project.end_station,
            total_length: project.total_length,
          });
        } catch (error) {
          console.error('Failed to fetch project:', error);
          alert('获取项目信息失败');
          navigate('/projects');
        } finally {
          setFetching(false);
        }
      };
      fetchProject();
    }
  }, [id, isEdit, reset, navigate]);

  const onSubmit = async (data: ProjectFormData) => {
    setLoading(true);
    try {
      if (isEdit && id) {
        await projectsApi.update(id, data);
      } else {
        await projectsApi.create(data);
      }
      navigate('/projects');
    } catch (error) {
      console.error('Failed to save project:', error);
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
        <button className={styles.backBtn} onClick={() => navigate('/projects')}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="page-title">{isEdit ? '编辑项目' : '新建项目'}</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
        <div className={styles.formGroup}>
          <label className={styles.label}>
            项目名称 <span className={styles.required}>*</span>
          </label>
          <input
            type="text"
            className={`input ${errors.name ? styles.inputError : ''}`}
            placeholder="请输入项目名称"
            {...register('name')}
          />
          {errors.name && <span className={styles.error}>{errors.name.message}</span>}
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>项目代码</label>
          <input
            type="text"
            className={`input ${errors.code ? styles.inputError : ''}`}
            placeholder="请输入项目代码（可选）"
            {...register('code')}
          />
          {errors.code && <span className={styles.error}>{errors.code.message}</span>}
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>项目描述</label>
          <textarea
            className={`input ${styles.textarea} ${errors.description ? styles.inputError : ''}`}
            placeholder="请输入项目描述（可选）"
            rows={4}
            {...register('description')}
          />
          {errors.description && <span className={styles.error}>{errors.description.message}</span>}
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
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/projects')}>
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
