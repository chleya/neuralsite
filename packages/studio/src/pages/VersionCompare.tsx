import { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import styles from './VersionCompare.module.css';

// 版本数据类型
interface VersionData {
  version_id: string;
  version: string;
  name: string;
  created_at: string;
  created_by: string;
  description: string;
  // 项目基本字段
  projectData: {
    name: string;
    code: string;
    total_length: number;
    start_station: number;
    end_station: number;
    description: string;
  };
  // 路线数据
  routes: {
    route_id: string;
    name: string;
    total_length: number;
    station_count: number;
  }[];
  // 桩号数据
  stations: {
    station_id: string;
    station: number;
    station_display: string;
    x: number;
    y: number;
    z: number;
  }[];
  // 照片数量
  photo_count: number;
  // 问题数量
  issue_count: number;
}

// 差异类型
interface DiffField {
  field: string;
  fieldName: string;
  oldValue: any;
  newValue: any;
  type: 'changed' | 'added' | 'removed';
}

interface DiffSection {
  section: string;
  sectionName: string;
  fields: DiffField[];
}

// 模拟版本数据 - 实际项目中应该从 API 获取
const mockVersions: VersionData[] = [
  {
    version_id: 'v1',
    version: '1.0.0',
    name: '初始版本',
    created_at: '2026-01-15T10:00:00Z',
    created_by: '张三',
    description: '项目初始化版本',
    projectData: {
      name: '京雄高速',
      code: 'JX-2026-001',
      total_length: 10000,
      start_station: 0,
      end_station: 10000,
      description: '京雄高速公路项目'
    },
    routes: [
      { route_id: 'r1', name: '主线', total_length: 10000, station_count: 101 },
      { route_id: 'r2', name: '匝道A', total_length: 500, station_count: 6 }
    ],
    stations: Array.from({ length: 20 }, (_, i) => ({
      station_id: `s${i + 1}`,
      station: i * 500,
      station_display: `K${i + 1}+${(i * 500) % 500}`,
      x: 1000 + i * 10,
      y: 500 + i * 5,
      z: 100 + i
    })),
    photo_count: 150,
    issue_count: 5
  },
  {
    version_id: 'v2',
    version: '1.1.0',
    name: '第一次修订',
    created_at: '2026-02-20T14:30:00Z',
    created_by: '李四',
    description: '增加路线和桩号数据',
    projectData: {
      name: '京雄高速',
      code: 'JX-2026-001',
      total_length: 12000,
      start_station: 0,
      end_station: 12000,
      description: '京雄高速公路项目 - 扩建'
    },
    routes: [
      { route_id: 'r1', name: '主线', total_length: 12000, station_count: 121 },
      { route_id: 'r2', name: '匝道A', total_length: 500, station_count: 6 },
      { route_id: 'r3', name: '匝道B', total_length: 800, station_count: 9 }
    ],
    stations: Array.from({ length: 30 }, (_, i) => ({
      station_id: `s${i + 1}`,
      station: i * 400,
      station_display: `K${Math.floor(i * 400 / 1000)}+${(i * 400) % 1000}`,
      x: 1000 + i * 12,
      y: 500 + i * 6,
      z: 100 + i * 1.5
    })),
    photo_count: 280,
    issue_count: 8
  },
  {
    version_id: 'v3',
    version: '1.2.0',
    name: '第二次修订',
    created_at: '2026-03-01T09:15:00Z',
    created_by: '王五',
    description: '优化桩号精度，添加照片',
    projectData: {
      name: '京雄高速',
      code: 'JX-2026-001',
      total_length: 12000,
      start_station: 0,
      end_station: 12000,
      description: '京雄高速公路项目 - 最终版'
    },
    routes: [
      { route_id: 'r1', name: '主线', total_length: 12000, station_count: 121 },
      { route_id: 'r2', name: '匝道A', total_length: 500, station_count: 6 },
      { route_id: 'r3', name: '匝道B', total_length: 800, station_count: 9 }
    ],
    stations: Array.from({ length: 35 }, (_, i) => ({
      station_id: `s${i + 1}`,
      station: i * 350,
      station_display: `K${Math.floor(i * 350 / 1000)}+${(i * 350) % 1000}`,
      x: 1000 + i * 11,
      y: 500 + i * 5.5,
      z: 100 + i * 1.2
    })),
    photo_count: 450,
    issue_count: 3
  }
];

export default function VersionCompare() {
  const [versions, setVersions] = useState<VersionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVersion1, setSelectedVersion1] = useState<string>('');
  const [selectedVersion2, setSelectedVersion2] = useState<string>('');
  const [diffResult, setDiffResult] = useState<DiffSection[]>([]);
  const [stats, setStats] = useState({ changed: 0, added: 0, removed: 0 });

  // 加载版本列表
  useEffect(() => {
    // 模拟 API 调用
    setTimeout(() => {
      setVersions(mockVersions);
      setLoading(false);
    }, 500);
  }, []);

  // 计算差异
  const calculateDiff = () => {
    if (!selectedVersion1 || !selectedVersion2) return;

    const v1 = versions.find(v => v.version_id === selectedVersion1);
    const v2 = versions.find(v => v.version_id === selectedVersion2);
    if (!v1 || !v2) return;

    const diffSections: DiffSection[] = [];
    let changedCount = 0;
    let addedCount = 0;
    let removedCount = 0;

    // 1. 项目基本信息差异
    const projectFields: DiffField[] = [];
    const fieldsToCompare: { key: keyof typeof v1.projectData; name: string }[] = [
      { key: 'name', name: '项目名称' },
      { key: 'code', name: '项目代码' },
      { key: 'total_length', name: '总长度' },
      { key: 'start_station', name: '起始桩号' },
      { key: 'end_station', name: '结束桩号' },
      { key: 'description', name: '项目描述' }
    ];

    fieldsToCompare.forEach(({ key, name }) => {
      if (v1.projectData[key] !== v2.projectData[key]) {
        const field: DiffField = {
          field: key,
          fieldName: name,
          oldValue: v1.projectData[key],
          newValue: v2.projectData[key],
          type: 'changed'
        };
        // 判断是新增还是删除（旧值为空或新值为空）
        if (!v1.projectData[key] && v2.projectData[key]) {
          field.type = 'added';
          addedCount++;
        } else if (v1.projectData[key] && !v2.projectData[key]) {
          field.type = 'removed';
          removedCount++;
        } else {
          changedCount++;
        }
        projectFields.push(field);
      }
    });

    if (projectFields.length > 0) {
      diffSections.push({ section: 'project', sectionName: '项目信息', fields: projectFields });
    }

    // 2. 路线差异
    const routeFields: DiffField[] = [];
    const v1RouteIds = v1.routes.map(r => r.route_id);
    const v2RouteIds = v2.routes.map(r => r.route_id);
    
    // 新增路线
    v2.routes.forEach(r2 => {
      if (!v1RouteIds.includes(r2.route_id)) {
        routeFields.push({
          field: 'routes',
          fieldName: `路线: ${r2.name}`,
          oldValue: null,
          newValue: r2,
          type: 'added'
        });
        addedCount++;
      }
    });
    
    // 删除路线
    v1.routes.forEach(r1 => {
      if (!v2RouteIds.includes(r1.route_id)) {
        routeFields.push({
          field: 'routes',
          fieldName: `路线: ${r1.name}`,
          oldValue: r1,
          newValue: null,
          type: 'removed'
        });
        removedCount++;
      }
    });

    // 路线长度变化
    v1.routes.forEach(r1 => {
      const r2 = v2.routes.find(r => r.route_id === r1.route_id);
      if (r2 && r1.total_length !== r2.total_length) {
        routeFields.push({
          field: 'routes.length',
          fieldName: `${r1.name} - 长度`,
          oldValue: r1.total_length,
          newValue: r2.total_length,
          type: 'changed'
        });
        changedCount++;
      }
      if (r2 && r1.station_count !== r2.station_count) {
        routeFields.push({
          field: 'routes.stations',
          fieldName: `${r1.name} - 桩号数`,
          oldValue: r1.station_count,
          newValue: r2.station_count,
          type: 'changed'
        });
        changedCount++;
      }
    });

    if (routeFields.length > 0) {
      diffSections.push({ section: 'routes', sectionName: '路线数据', fields: routeFields });
    }

    // 3. 桩号数量差异
    if (v1.stations.length !== v2.stations.length) {
      const stationDiff: DiffField[] = [{
        field: 'station_count',
        fieldName: '桩号总数',
        oldValue: v1.stations.length,
        newValue: v2.stations.length,
        type: v2.stations.length > v1.stations.length ? 'added' : 'removed'
      }];
      if (v2.stations.length > v1.stations.length) {
        addedCount += v2.stations.length - v1.stations.length;
      } else {
        removedCount += v1.stations.length - v2.stations.length;
      }
      diffSections.push({ section: 'stations', sectionName: '桩号数据', fields: stationDiff });
    }

    // 4. 照片数量差异
    if (v1.photo_count !== v2.photo_count) {
      const photoFields: DiffField[] = [{
        field: 'photo_count',
        fieldName: '照片数量',
        oldValue: v1.photo_count,
        newValue: v2.photo_count,
        type: v2.photo_count > v1.photo_count ? 'added' : 'changed'
      }];
      changedCount += Math.abs(v2.photo_count - v1.photo_count);
      diffSections.push({ section: 'photos', sectionName: '照片数据', fields: photoFields });
    }

    // 5. 问题数量差异
    if (v1.issue_count !== v2.issue_count) {
      const issueFields: DiffField[] = [{
        field: 'issue_count',
        fieldName: '问题数量',
        oldValue: v1.issue_count,
        newValue: v2.issue_count,
        type: v2.issue_count > v1.issue_count ? 'added' : 'removed'
      }];
      if (v2.issue_count > v1.issue_count) {
        addedCount += v2.issue_count - v1.issue_count;
      } else {
        removedCount += v1.issue_count - v2.issue_count;
      }
      diffSections.push({ section: 'issues', sectionName: '问题数据', fields: issueFields });
    }

    setDiffResult(diffSections);
    setStats({ changed: changedCount, added: addedCount, removed: removedCount });
  };

  // 导出对比报告
  const exportReport = () => {
    if (!selectedVersion1 || !selectedVersion2 || diffResult.length === 0) return;

    const v1 = versions.find(v => v.version_id === selectedVersion1);
    const v2 = versions.find(v => v.version_id === selectedVersion2);
    if (!v1 || !v2) return;

    let report = `# 版本对比报告\n\n`;
    report += `## 对比信息\n`;
    report += `- 版本1: ${v1.version} (${v1.name})\n`;
    report += `- 版本2: ${v2.version} (${v2.name})\n`;
    report += `- 对比时间: ${new Date().toLocaleString('zh-CN')}\n\n`;

    report += `## 变更统计\n`;
    report += `- 变更: ${stats.changed} 项\n`;
    report += `- 新增: ${stats.added} 项\n`;
    report += `- 删除: ${stats.removed} 项\n\n`;

    report += `## 详细差异\n`;
    diffResult.forEach((section) => {
      report += `### ${section.sectionName}\n`;
      section.fields.forEach((field) => {
        const typeLabel = field.type === 'changed' ? '修改' : field.type === 'added' ? '新增' : '删除';
        report += `- ${field.fieldName}: ${field.type === 'added' ? JSON.stringify(field.newValue) : JSON.stringify(field.oldValue)} → ${JSON.stringify(field.newValue)} [${typeLabel}]\n`;
      });
      report += '\n';
    });

    // 创建并下载文件
    const blob = new Blob([report], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `version-comparison-${v1.version}-vs-${v2.version}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // 图表配置
  const chartOption = {
    title: {
      text: '变更统计',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold', color: '#fff' }
    },
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      textStyle: { color: '#fff' }
    },
    color: ['#3b82f6', '#22c55e', '#ef4444'],
    series: [
      {
        name: '变更类型',
        type: 'pie',
        radius: ['30%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#1a1a2e', borderWidth: 2 },
        label: { show: true, formatter: '{b}: {c}', color: '#fff' },
        data: [
          { name: '变更', value: stats.changed },
          { name: '新增', value: stats.added },
          { name: '删除', value: stats.removed }
        ]
      }
    ]
  };

  if (loading) {
    return <div className={styles.loading}>加载中...</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>版本对比</h1>
        <p className={styles.subtitle}>比较两个版本之间的差异</p>
      </div>

      {/* 版本选择器 */}
      <div className={styles.selectorSection}>
        <div className={styles.selector}>
          <label className={styles.label}>版本 1 (旧版本)</label>
          <select
            className={styles.select}
            value={selectedVersion1}
            onChange={(e) => setSelectedVersion1(e.target.value)}
          >
            <option value="">请选择版本</option>
            {versions.map((v) => (
              <option key={v.version_id} value={v.version_id}>
                {v.version} - {v.name} ({new Date(v.created_at).toLocaleDateString('zh-CN')})
              </option>
            ))}
          </select>
        </div>

        <div className={styles.selector}>
          <label className={styles.label}>版本 2 (新版本)</label>
          <select
            className={styles.select}
            value={selectedVersion2}
            onChange={(e) => setSelectedVersion2(e.target.value)}
          >
            <option value="">请选择版本</option>
            {versions.map((v) => (
              <option key={v.version_id} value={v.version_id}>
                {v.version} - {v.name} ({new Date(v.created_at).toLocaleDateString('zh-CN')})
              </option>
            ))}
          </select>
        </div>

        <div className={styles.actions}>
          <button
            className={styles.compareBtn}
            onClick={calculateDiff}
            disabled={!selectedVersion1 || !selectedVersion2}
          >
            开始对比
          </button>
          <button
            className={styles.exportBtn}
            onClick={exportReport}
            disabled={diffResult.length === 0}
          >
            导出报告
          </button>
        </div>
      </div>

      {/* 对比结果 */}
      {diffResult.length > 0 && (
        <>
          {/* 统计图表 */}
          <div className={styles.statsSection}>
            <div className={styles.statsCards}>
              <div className={styles.statCard}>
                <span className={styles.statLabel}>变更</span>
                <span className={`${styles.statValue} ${styles.statChanged}`}>{stats.changed}</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statLabel}>新增</span>
                <span className={`${styles.statValue} ${styles.statAdded}`}>{stats.added}</span>
              </div>
              <div className={styles.statCard}>
                <span className={styles.statLabel}>删除</span>
                <span className={`${styles.statValue} ${styles.statRemoved}`}>{stats.removed}</span>
              </div>
            </div>
            <div className={styles.chartContainer}>
              <ReactECharts option={chartOption} style={{ height: '280px' }} />
            </div>
          </div>

          {/* 差异详情 */}
          <div className={styles.diffSection}>
            <h2 className={styles.sectionTitle}>详细差异</h2>
            {diffResult.map((section, idx) => (
              <div key={idx} className={styles.diffCard}>
                <h3 className={styles.diffCardTitle}>{section.sectionName}</h3>
                <div className={styles.diffFields}>
                  {section.fields.map((field, fieldIdx) => (
                    <div
                      key={fieldIdx}
                      className={`${styles.diffField} ${styles[field.type]}`}
                    >
                      <span className={styles.fieldName}>{field.fieldName}</span>
                      <div className={styles.fieldValues}>
                        {field.type === 'added' ? (
                          <span className={styles.newValue}>+ {JSON.stringify(field.newValue)}</span>
                        ) : field.type === 'removed' ? (
                          <span className={styles.oldValue}>- {JSON.stringify(field.oldValue)}</span>
                        ) : (
                          <>
                            <span className={styles.oldValue}>{JSON.stringify(field.oldValue)}</span>
                            <span className={styles.arrow}>→</span>
                            <span className={styles.newValue}>{JSON.stringify(field.newValue)}</span>
                          </>
                        )}
                      </div>
                      <span className={styles.diffType}>
                        {field.type === 'changed' ? '修改' : field.type === 'added' ? '新增' : '删除'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* 空状态 */}
      {(!selectedVersion1 || !selectedVersion2) && (
        <div className={styles.emptyState}>
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p>请选择两个版本进行对比</p>
        </div>
      )}
    </div>
  );
}
