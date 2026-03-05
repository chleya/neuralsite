import { useState, useCallback } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useApp } from '../context/AppContext';
import { stationsApi } from '../api/endpoints';
import { StationCreate } from '../api/types';
import { Save, Plus, Trash2, ArrowLeft, Upload } from 'lucide-react';

// 桩号表单验证模式
const stationSchema = z.object({
  project_id: z.string().min(1, '请选择项目'),
  route_id: z.string().min(1, '请输入路线ID'),
  station: z.number().min(0, '桩号必须大于等于0'),
  station_display: z.string().min(1, '请输入桩号显示值'),
  x: z.number().min(-180).max(180, 'X坐标无效'),
  y: z.number().min(-90).max(90, 'Y坐标无效'),
  z: z.number().min(-1000).max(10000, '高程无效'),
  azimuth: z.number().min(0).max(360, '方位角需在0-360之间'),
  horizontal_elem: z.string().optional(),
  vertical_elem: z.string().optional(),
  mileage: z.number().optional(),
  description: z.string().optional(),
});

type StationFormData = z.infer<typeof stationSchema>;

// 批量录入模式
const batchStationSchema = z.object({
  project_id: z.string().min(1, '请选择项目'),
  route_id: z.string().min(1, '请输入路线ID'),
  stations: z.array(stationSchema).min(1, '请至少录入一个桩号'),
});

type BatchStationFormData = z.infer<typeof batchStationSchema>;

interface StationEntryPageProps {
  onNavigate?: (page: string) => void;
  editId?: string;
}

export default function StationEntryPage({ onNavigate, editId }: StationEntryPageProps) {
  const { state, dispatch } = useApp();
  const [mode, setMode] = useState<'single' | 'batch'>('single');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 单条录入表单
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm<StationFormData>({
    resolver: zodResolver(stationSchema),
    defaultValues: {
      project_id: state.selectedProject?.project_id || '',
      route_id: state.routeId || 'demo',
      station: 0,
      station_display: '',
      x: 0,
      y: 0,
      z: 0,
      azimuth: 0,
      horizontal_elem: '直线',
      vertical_elem: '直线',
    },
  });

  // 批量录入表单
  const {
    register: registerBatch,
    handleSubmit: handleBatchSubmit,
    control: batchControl,
    formState: { errors: batchErrors },
  } = useForm<BatchStationFormData>({
    resolver: zodResolver(batchStationSchema),
    defaultValues: {
      project_id: state.selectedProject?.project_id || '',
      route_id: state.routeId || 'demo',
      stations: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: batchControl,
    name: 'stations',
  });

  // 解析桩号显示值转换为数字
  const parseStationValue = (display: string): number => {
    // 支持格式: K0+000, K1+500, 0+000, 1000 等
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

  // 提交单条记录
  const onSubmitSingle = useCallback(async (data: StationFormData) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const stationData: StationCreate = {
        ...data,
        local_id: `local_${Date.now()}`,
      };

      // 模拟API调用（后端未启动时）
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setSuccess('桩号数据保存成功！');
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
  }, [reset, dispatch]);

  // 提交批量记录
  const onSubmitBatch = useCallback(async (data: BatchStationFormData) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // 模拟API调用（后端未启动时）
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setSuccess(`成功保存 ${data.stations.length} 条桩号数据！`);
      
      // 清空批量数据
      data.stations.forEach((_, index) => remove(index));
    } catch (err) {
      setError(err instanceof Error ? err.message : '批量保存失败，请重试');
    } finally {
      setLoading(false);
    }
  }, [remove]);

  // 添加批量条目
  const addBatchItem = useCallback(() => {
    append({
      project_id: watch('project_id'),
      route_id: watch('route_id'),
      station: 0,
      station_display: '',
      x: 0,
      y: 0,
      z: 0,
      azimuth: 0,
      horizontal_elem: '直线',
      vertical_elem: '直线',
    });
  }, [append, watch]);

  // 常用桩号快速选择
  const quickStations = [
    { value: 0, display: 'K0+000' },
    { value: 500, display: 'K0+500' },
    { value: 1000, display: 'K1+000' },
    { value: 1500, display: 'K1+500' },
    { value: 2000, display: 'K2+000' },
  ];

  return (
    <div className="station-entry-page">
      {/* 顶部导航 */}
      <div className="page-header">
        <button className="btn-back" onClick={() => onNavigate?.('dashboard')}>
          <ArrowLeft size={20} />
          返回
        </button>
        <h1>📍 桩号录入</h1>
        <div className="mode-switch">
          <button 
            className={mode === 'single' ? 'active' : ''} 
            onClick={() => setMode('single')}
          >
            单条录入
          </button>
          <button 
            className={mode === 'batch' ? 'active' : ''} 
            onClick={() => setMode('batch')}
          >
            批量录入
          </button>
        </div>
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
        {mode === 'single' ? (
          /* 单条录入 */
          <form onSubmit={handleSubmit(onSubmitSingle)} className="entry-form">
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
            </div>

            <div className="form-section">
              <h3>坐标信息</h3>
              
              <div className="form-row three-col">
                <div className="form-group">
                  <label>X坐标 *</label>
                  <input 
                    type="number"
                    step="0.001"
                    {...register('x', { valueAsNumber: true })} 
                    placeholder="例如: 500000"
                  />
                  {errors.x && <span className="error">{errors.x.message}</span>}
                </div>
                
                <div className="form-group">
                  <label>Y坐标 *</label>
                  <input 
                    type="number"
                    step="0.001"
                    {...register('y', { valueAsNumber: true })} 
                    placeholder="例如: 3000000"
                  />
                  {errors.y && <span className="error">{errors.y.message}</span>}
                </div>
                
                <div className="form-group">
                  <label>高程Z(m) *</label>
                  <input 
                    type="number"
                    step="0.001"
                    {...register('z', { valueAsNumber: true })} 
                    placeholder="例如: 100.5"
                  />
                  {errors.z && <span className="error">{errors.z.message}</span>}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>方位角(°) *</label>
                  <input 
                    type="number"
                    step="0.1"
                    {...register('azimuth', { valueAsNumber: true })} 
                    placeholder="例如: 45"
                  />
                  {errors.azimuth && (
                    <span className="error">{errors.azimuth.message}</span>
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
              <h3>线元信息</h3>
              
              <div className="form-row">
                <div className="form-group">
                  <label>平曲线元素</label>
                  <select {...register('horizontal_elem')}>
                    <option value="直线">直线</option>
                    <option value="缓和曲线">缓和曲线</option>
                    <option value="圆曲线">圆曲线</option>
                  </select>
                </div>
                
                <div className="form-group">
                  <label>纵曲线元素</label>
                  <select {...register('vertical_elem')}>
                    <option value="直线">直线</option>
                    <option value="凸形竖曲线">凸形竖曲线</option>
                    <option value="凹形竖曲线">凹形竖曲线</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>备注</label>
                <textarea 
                  {...register('description')} 
                  placeholder="可选备注信息"
                  rows={3}
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="button" className="btn-secondary" onClick={() => reset()}>
                重置表单
              </button>
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? '保存中...' : (
                  <>
                    <Save size={18} />
                    保存桩号
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          /* 批量录入 */
          <form onSubmit={handleBatchSubmit(onSubmitBatch)} className="entry-form">
            <div className="form-section">
              <div className="section-header">
                <h3>批量录入 ({fields.length} 条)</h3>
                <button 
                  type="button" 
                  className="btn-add"
                  onClick={addBatchItem}
                >
                  <Plus size={18} />
                  添加
                </button>
              </div>

              <div className="batch-header">
                <div className="batch-col">桩号</div>
                <div className="batch-col">X坐标</div>
                <div className="batch-col">Y坐标</div>
                <div className="batch-col">高程Z</div>
                <div className="batch-col">方位角</div>
                <div className="batch-col actions"></div>
              </div>

              {fields.map((field, index) => (
                <div key={field.id} className="batch-row">
                  <div className="batch-col">
                    <input
                      {...registerBatch(`stations.${index}.station_display`)}
                      placeholder="K0+000"
                    />
                  </div>
                  <div className="batch-col">
                    <input
                      type="number"
                      step="0.001"
                      {...registerBatch(`stations.${index}.x`, { valueAsNumber: true })}
                    />
                  </div>
                  <div className="batch-col">
                    <input
                      type="number"
                      step="0.001"
                      {...registerBatch(`stations.${index}.y`, { valueAsNumber: true })}
                    />
                  </div>
                  <div className="batch-col">
                    <input
                      type="number"
                      step="0.001"
                      {...registerBatch(`stations.${index}.z`, { valueAsNumber: true })}
                    />
                  </div>
                  <div className="batch-col">
                    <input
                      type="number"
                      step="0.1"
                      {...registerBatch(`stations.${index}.azimuth`, { valueAsNumber: true })}
                    />
                  </div>
                  <div className="batch-col actions">
                    <button
                      type="button"
                      className="btn-remove"
                      onClick={() => remove(index)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}

              {fields.length === 0 && (
                <div className="empty-batch">
                  点击"添加"按钮添加批量数据
                </div>
              )}
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading || fields.length === 0}>
                {loading ? '保存中...' : (
                  <>
                    <Save size={18} />
                    批量保存
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>

      <style>{`
        .station-entry-page {
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
          transition: all 0.2s;
        }

        .btn-back:hover {
          background: #333;
          color: #fff;
        }

        .mode-switch {
          display: flex;
          background: #1a1a2e;
          border-radius: 8px;
          padding: 4px;
        }

        .mode-switch button {
          padding: 8px 16px;
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
          border-radius: 6px;
          transition: all 0.2s;
        }

        .mode-switch button.active {
          background: #667eea;
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

        .form-row {
          display: flex;
          gap: 16px;
          margin-bottom: 16px;
        }

        .form-row.three-col {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
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
          transition: all 0.2s;
        }

        .quick-btn:hover {
          background: #667eea;
          border-color: #667eea;
          color: #fff;
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
          transition: all 0.2s;
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
          transition: all 0.2s;
        }

        .btn-secondary:hover {
          background: #333;
          color: #fff;
        }

        .btn-add {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: #252540;
          border: 1px solid #667eea;
          border-radius: 6px;
          color: #667eea;
          font-size: 13px;
          cursor: pointer;
        }

        .btn-add:hover {
          background: #667eea;
          color: #fff;
        }

        .batch-header {
          display: grid;
          grid-template-columns: 2fr 1.5fr 1.5fr 1fr 1fr 50px;
          gap: 8px;
          padding: 8px 0;
          font-size: 11px;
          color: #666;
          border-bottom: 1px solid #333;
        }

        .batch-row {
          display: grid;
          grid-template-columns: 2fr 1.5fr 1.5fr 1fr 1fr 50px;
          gap: 8px;
          padding: 8px 0;
          align-items: center;
          border-bottom: 1px solid #252540;
        }

        .batch-col input {
          width: 100%;
          padding: 8px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 4px;
          color: #fff;
          font-size: 13px;
        }

        .batch-col.actions {
          display: flex;
          justify-content: center;
        }

        .btn-remove {
          padding: 6px;
          background: transparent;
          border: none;
          color: #ff6b6b;
          cursor: pointer;
          border-radius: 4px;
        }

        .btn-remove:hover {
          background: rgba(255, 107, 107, 0.1);
        }

        .empty-batch {
          padding: 40px;
          text-align: center;
          color: #666;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
}
