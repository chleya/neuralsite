import { useState, useCallback } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useApp } from '../context/AppContext';
import { crossSectionsApi } from '../api/endpoints';
import { CrossSectionCreate, CrossSectionPoint } from '../api/types';
import { Save, Plus, Trash2, ArrowLeft, ChevronDown, ChevronUp } from 'lucide-react';

// 横断面点验证模式
const pointSchema = z.object({
  offset: z.number().min(-100).max(100, '偏移量范围: -100 ~ 100'),
  elevation: z.number().min(-100).max(10000, '高程无效'),
  description: z.string().optional(),
});

// 主表单验证模式
const crossSectionSchema = z.object({
  project_id: z.string().min(1, '请选择项目'),
  route_id: z.string().min(1, '请输入路线ID'),
  station: z.number().min(0, '桩号必须大于等于0'),
  station_display: z.string().min(1, '请输入桩号显示值'),
  cs_type: z.enum(['left', 'right', 'center', 'full']),
  mileage: z.number().optional(),
  points: z.array(pointSchema).min(2, '至少需要2个断面点'),
  description: z.string().optional(),
});

type CrossSectionFormData = z.infer<typeof crossSectionSchema>;

interface CrossSectionEntryPageProps {
  onNavigate?: (page: string) => void;
  editId?: string;
}

export default function CrossSectionEntryPage({ onNavigate, editId }: CrossSectionEntryPageProps) {
  const { state, dispatch } = useApp();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<number, boolean>>({});

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm<CrossSectionFormData>({
    resolver: zodResolver(crossSectionSchema),
    defaultValues: {
      project_id: state.selectedProject?.project_id || '',
      route_id: state.routeId || 'demo',
      station: 0,
      station_display: '',
      cs_type: 'full',
      points: [
        { offset: -10, elevation: 0, description: '左侧边坡' },
        { offset: -5, elevation: 0, description: '左坡脚' },
        { offset: 0, elevation: 0, description: '中桩' },
        { offset: 5, elevation: 0, description: '右坡脚' },
        { offset: 10, elevation: 0, description: '右侧边坡' },
      ],
    },
  });

  const { fields, append, remove, move } = useFieldArray({
    control,
    name: 'points',
  });

  // 解析桩号显示值转换为数字
  const parseStationValue = (display: string): number => {
    const match = display.match(/^([Kk])?(\d+)\+(\d{3})$/);
    if (match) {
      return parseInt(match[2]) * 1000 + parseInt(match[3]);
    }
    const num = parseFloat(display);
    return isNaN(num) ? 0 : num;
  };

  // 格式化桩号显示
  const formatStationDisplay = (value: number): string => {
    const km = Math.floor(value / 1000);
    const m = value % 1000;
    return `K${km}+${m.toString().padStart(3, '0')}`;
  };

  // 提交表单
  const onSubmit = useCallback(async (data: CrossSectionFormData) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const sectionData: CrossSectionCreate = {
        ...data,
        local_id: `local_${Date.now()}`,
      };

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setSuccess('横断面数据保存成功！');
      reset();
      
      // 更新全局状态
      dispatch({ 
        type: 'SET_SELECTED_STATION', 
        payload: data.station_display 
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败，请重试');
    } finally {
      setLoading(false);
    }
  }, [reset]);

  // 切换断面点展开状态
  const togglePoint = (index: number) => {
    setExpandedSections(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  // 添加预设断面类型
  const addPresetPoints = (type: 'full' | 'center' | 'left' | 'right') => {
    const presets: Record<string, CrossSectionPoint[]> = {
      full: [
        { offset: -20, elevation: 0, description: '左侧坡顶' },
        { offset: -10, elevation: 0, description: '左坡脚' },
        { offset: -3, elevation: 0, description: '左路肩' },
        { offset: 0, elevation: 0, description: '中桩' },
        { offset: 3, elevation: 0, description: '右路肩' },
        { offset: 10, elevation: 0, description: '右坡脚' },
        { offset: 20, elevation: 0, description: '右侧坡顶' },
      ],
      center: [
        { offset: -3, elevation: 0, description: '左路肩' },
        { offset: 0, elevation: 0, description: '中桩' },
        { offset: 3, elevation: 0, description: '右路肩' },
      ],
      left: [
        { offset: -20, elevation: 0, description: '左侧坡顶' },
        { offset: -10, elevation: 0, description: '左坡脚' },
        { offset: 0, elevation: 0, description: '中桩' },
      ],
      right: [
        { offset: 0, elevation: 0, description: '中桩' },
        { offset: 10, elevation: 0, description: '右坡脚' },
        { offset: 20, elevation: 0, description: '右侧坡顶' },
      ],
    };

    // 替换现有点
    presets[type].forEach((point, index) => {
      if (index === 0) {
        setValue('points', [point]);
      } else {
        append(point);
      }
    });
  };

  // 常用桩号
  const quickStations = [
    { value: 0, display: 'K0+000' },
    { value: 500, display: 'K0+500' },
    { value: 1000, display: 'K1+000' },
    { value: 1500, display: 'K1+500' },
    { value: 2000, display: 'K2+000' },
  ];

  return (
    <div className="cross-section-entry-page">
      {/* 顶部导航 */}
      <div className="page-header">
        <button className="btn-back" onClick={() => onNavigate?.('dashboard')}>
          <ArrowLeft size={20} />
          返回
        </button>
        <h1>📐 横断面录入</h1>
      </div>

      {/* 消息提示 */}
      {success && (
        <div className="alert success">{success}</div>
      )}
      {error && (
        <div className="alert error">{error}</div>
      )}

      {/* 表单区域 */}
      <div className="form-container">
        <form onSubmit={handleSubmit(onSubmit)} className="entry-form">
          <div className="form-section">
            <h3>基本信息</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>项目ID *</label>
                <input 
                  {...register('project_id')} 
                  placeholder="请输入项目ID"
                />
                {errors.project_id && (
                  <span className="error">{errors.project_id.message}</span>
                )}
              </div>
              
              <div className="form-group">
                <label>路线ID *</label>
                <input 
                  {...register('route_id')} 
                  placeholder="例如: demo"
                />
                {errors.route_id && (
                  <span className="error">{errors.route_id.message}</span>
                )}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>桩号(米) *</label>
                <input 
                  type="number"
                  {...register('station', { valueAsNumber: true })} 
                  placeholder="例如: 500"
                />
                {errors.station && (
                  <span className="error">{errors.station.message}</span>
                )}
              </div>
              
              <div className="form-group">
                <label>桩号显示 *</label>
                <div className="input-with-quick">
                  <input 
                    {...register('station_display')} 
                    placeholder="例如: K0+500"
                    onBlur={(e) => {
                      const value = parseStationValue(e.target.value);
                      if (value > 0) {
                        setValue('station', value);
                        setValue('station_display', formatStationDisplay(value));
                      }
                    }}
                  />
                  <div className="quick-select">
                    {quickStations.map(s => (
                      <button
                        key={s.value}
                        type="button"
                        className="quick-btn"
                        onClick={() => {
                          setValue('station', s.value);
                          setValue('station_display', s.display);
                        }}
                      >
                        {s.display}
                      </button>
                    ))}
                  </div>
                </div>
                {errors.station_display && (
                  <span className="error">{errors.station_display.message}</span>
                )}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>断面类型 *</label>
                <select {...register('cs_type')}>
                  <option value="full">全断面</option>
                  <option value="center">中桩断面</option>
                  <option value="left">左半断面</option>
                  <option value="right">右半断面</option>
                </select>
                {errors.cs_type && (
                  <span className="error">{errors.cs_type.message}</span>
                )}
              </div>
              
              <div className="form-group">
                <label>里程(米)</label>
                <input 
                  type="number"
                  {...register('mileage', { valueAsNumber: true })} 
                  placeholder="可选"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <div className="section-header">
              <h3>断面点数据 ({fields.length} 个点)</h3>
              <div className="preset-buttons">
                <button type="button" onClick={() => addPresetPoints('full')}>全断面</button>
                <button type="button" onClick={() => addPresetPoints('center')}>中桩</button>
                <button type="button" onClick={() => addPresetPoints('left')}>左半</button>
                <button type="button" onClick={() => addPresetPoints('right')}>右半</button>
              </div>
            </div>

            <div className="points-header">
              <div className="point-col">#</div>
              <div className="point-col">偏移量(m)</div>
              <div className="point-col">高程(m)</div>
              <div className="point-col desc">描述</div>
              <div className="point-col actions"></div>
            </div>

            {fields.map((field, index) => (
              <div key={field.id} className="point-row">
                <div className="point-col point-index">
                  {index + 1}
                </div>
                <div className="point-col">
                  <input
                    type="number"
                    step="0.01"
                    {...register(`points.${index}.offset`, { valueAsNumber: true })}
                    placeholder="偏移量"
                  />
                </div>
                <div className="point-col">
                  <input
                    type="number"
                    step="0.01"
                    {...register(`points.${index}.elevation`, { valueAsNumber: true })}
                    placeholder="高程"
                  />
                </div>
                <div className="point-col desc">
                  <input
                    {...register(`points.${index}.description`)}
                    placeholder="描述"
                  />
                </div>
                <div className="point-col actions">
                  <button
                    type="button"
                    className="btn-icon"
                    onClick={() => remove(index)}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}

            <button
              type="button"
              className="btn-add-point"
              onClick={() => append({ offset: 0, elevation: 0, description: '' })}
            >
              <Plus size={18} />
              添加断面点
            </button>

            {errors.points && typeof errors.points.message === 'string' && (
              <span className="error points-error">{errors.points.message}</span>
            )}
            {errors.points && Array.isArray(errors.points) && (
              <span className="error points-error">
                {errors.points.some(p => p?.offset) ? '偏移量范围: -100 ~ 100' : 
                 errors.points.some(p => p?.elevation) ? '请检查高程值' : ''}
              </span>
            )}
          </div>

          <div className="form-section">
            <h3>备注</h3>
            <textarea 
              {...register('description')} 
              placeholder="可选备注信息"
              rows={3}
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => reset()}>
              重置表单
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? '保存中...' : (
                <>
                  <Save size={18} />
                  保存横断面
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      <style>{`
        .cross-section-entry-page {
          display: flex;
          flex-direction: column;
          height: 100%;
          padding: 20px;
          overflow-y: auto;
          background: #0f0f1a;
        }

        .page-header {
          display: flex;
          align-items: center;
          gap: 20px;
          margin-bottom: 20px;
        }

        .page-header h1 {
          flex: 1;
          font-size: 20px;
          color: #fff;
          margin: 0;
        }

        .btn-back {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #aaa;
          cursor: pointer;
        }

        .btn-back:hover {
          background: #333;
          color: #fff;
        }

        .alert {
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 16px;
          font-size: 14px;
        }

        .alert.success {
          background: rgba(0, 255, 136, 0.1);
          border: 1px solid #00ff88;
          color: #00ff88;
        }

        .alert.error {
          background: rgba(255, 107, 107, 0.1);
          border: 1px solid #ff6b6b;
          color: #ff6b6b;
        }

        .form-container {
          flex: 1;
          background: #1a1a2e;
          border-radius: 12px;
          padding: 24px;
          overflow-y: auto;
        }

        .form-section {
          margin-bottom: 24px;
        }

        .form-section h3 {
          font-size: 14px;
          color: #00ff88;
          margin-bottom: 16px;
          padding-bottom: 8px;
          border-bottom: 1px solid #333;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .section-header h3 {
          margin: 0;
          padding: 0;
          border: none;
        }

        .preset-buttons {
          display: flex;
          gap: 8px;
        }

        .preset-buttons button {
          padding: 6px 12px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 4px;
          color: #aaa;
          font-size: 12px;
          cursor: pointer;
        }

        .preset-buttons button:hover {
          background: #667eea;
          border-color: #667eea;
          color: #fff;
        }

        .form-row {
          display: flex;
          gap: 16px;
          margin-bottom: 16px;
        }

        .form-group {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .form-group label {
          font-size: 12px;
          color: #888;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          padding: 10px 14px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 14px;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #667eea;
        }

        .form-group .error {
          font-size: 11px;
          color: #ff6b6b;
        }

        .input-with-quick {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .quick-select {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .quick-btn {
          padding: 4px 8px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 4px;
          color: #aaa;
          font-size: 11px;
          cursor: pointer;
        }

        .quick-btn:hover {
          background: #667eea;
          border-color: #667eea;
          color: #fff;
        }

        .points-header {
          display: grid;
          grid-template-columns: 50px 1fr 1fr 2fr 50px;
          gap: 8px;
          padding: 8px 0;
          font-size: 11px;
          color: #666;
          border-bottom: 1px solid #333;
        }

        .point-row {
          display: grid;
          grid-template-columns: 50px 1fr 1fr 2fr 50px;
          gap: 8px;
          padding: 8px 0;
          align-items: center;
          border-bottom: 1px solid #252540;
        }

        .point-col {
          display: flex;
          align-items: center;
        }

        .point-col input {
          width: 100%;
          padding: 8px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 4px;
          color: #fff;
          font-size: 13px;
        }

        .point-index {
          justify-content: center;
          font-weight: 600;
          color: #667eea;
        }

        .point-col.actions {
          justify-content: center;
        }

        .btn-icon {
          padding: 6px;
          background: transparent;
          border: none;
          color: #ff6b6b;
          cursor: pointer;
          border-radius: 4px;
        }

        .btn-icon:hover {
          background: rgba(255, 107, 107, 0.1);
        }

        .btn-add-point {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          width: 100%;
          padding: 12px;
          margin-top: 12px;
          background: #252540;
          border: 2px dashed #444;
          border-radius: 6px;
          color: #aaa;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-add-point:hover {
          background: rgba(102, 126, 234, 0.1);
          border-color: #667eea;
          color: #667eea;
        }

        .points-error {
          display: block;
          margin-top: 8px;
        }

        .form-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          padding-top: 16px;
          border-top: 1px solid #333;
        }

        .btn-primary {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: linear-gradient(135deg, #667eea, #764ba2);
          border: none;
          border-radius: 6px;
          color: #fff;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
        }

        .btn-primary:hover:not(:disabled) {
          transform: translateY(-2px);
        }

        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-secondary {
          padding: 12px 24px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #aaa;
          font-size: 14px;
          cursor: pointer;
        }

        .btn-secondary:hover {
          background: #333;
          color: #fff;
        }
      `}</style>
    </div>
  );
}
