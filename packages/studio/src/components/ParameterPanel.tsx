interface RouteParams {
  route_id: string
  design_speed: number
  horizontal_alignment: any[]
  vertical_alignment: any[]
}

interface ParameterPanelProps {
  params: RouteParams
  setParams: (p: RouteParams) => void
  startStation: number
  setStartStation: (s: number) => void
  endStation: number
  setEndStation: (s: number) => void
  interval: number
  setInterval: (i: number) => void
  onCalculate: () => void
  loading: boolean
}

function ParameterPanel({ 
  params, 
  setParams,
  startStation, 
  setStartStation,
  endStation, 
  setEndStation,
  interval, 
  setInterval,
  onCalculate,
  loading 
}: ParameterPanelProps) {
  return (
    <div className="parameter-panel">
      <h2>参数设置</h2>
      
      <div className="form-group">
        <label>路线ID</label>
        <input 
          type="text" 
          value={params.route_id}
          onChange={e => setParams({...params, route_id: e.target.value})}
        />
      </div>
      
      <div className="form-group">
        <label>设计速度 (km/h)</label>
        <select 
          value={params.design_speed}
          onChange={e => setParams({...params, design_speed: Number(e.target.value)})}
        >
          <option value={20}>20</option>
          <option value={40}>40</option>
          <option value={60}>60</option>
          <option value={80}>80</option>
          <option value={100}>100</option>
          <option value={120}>120</option>
        </select>
      </div>
      
      <h3>计算范围</h3>
      
      <div className="form-group">
        <label>起点桩号 (m)</label>
        <input 
          type="number" 
          value={startStation}
          onChange={e => setStartStation(Number(e.target.value))}
          min={0}
          step={100}
        />
      </div>
      
      <div className="form-group">
        <label>终点桩号 (m)</label>
        <input 
          type="number" 
          value={endStation}
          onChange={e => setEndStation(Number(e.target.value))}
          min={0}
          step={100}
        />
      </div>
      
      <div className="form-group">
        <label>间隔 (m)</label>
        <input 
          type="number" 
          value={interval}
          onChange={e => setInterval(Number(e.target.value))}
          min={10}
          max={200}
          step={10}
        />
      </div>
      
      <button 
        className="btn-primary"
        onClick={onCalculate}
        disabled={loading}
      >
        {loading ? '计算中...' : '计算坐标'}
      </button>
      
      <h3>平曲线参数</h3>
      <div className="params-list">
        {params.horizontal_alignment.map((elem, i) => (
          <div key={i} className="param-item">
            <span className="type">{elem.element_type}</span>
            <span>{elem.start_station} - {elem.end_station}</span>
            {elem.R > 0 && <span>R={elem.R}</span>}
            {elem.A > 0 && <span>A={elem.A}</span>}
          </div>
        ))}
      </div>
      
      <h3>纵曲线参数</h3>
      <div className="params-list">
        {params.vertical_alignment.map((elem, i) => (
          <div key={i} className="param-item">
            <span>{elem.station}</span>
            <span>H={elem.elevation}m</span>
            <span>{elem.grade_out}‰</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ParameterPanel
