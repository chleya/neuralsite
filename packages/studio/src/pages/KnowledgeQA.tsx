import { useState } from 'react'

// 模拟知识图谱问答
const mockKGData: Record<string, any> = {
  '公路': {
    answer: '公路是连接城市、乡村和工矿基地的公共道路设施，主要供汽车行驶。',
    entities: [
      { id: '1', name: '高速公路', type: '道路等级' },
      { id: '2', name: '一级公路', type: '道路等级' },
      { id: '3', name: '二级公路', type: '道路等级' }
    ],
    relations: [
      { source: '高速公路', target: '全封闭', relation: '特征' },
      { source: '高速公路', target: '汽车专用', relation: '用途' }
    ]
  },
  '桩号': {
    answer: '桩号是公路路线上表示里程的标记。通常以K表示千米，+号后面表示米数。例如K1+500表示距起点1500米。',
    entities: [
      { id: '1', name: 'K0+000', type: '桩号' },
      { id: '2', name: 'K1+500', type: '桩号' }
    ],
    relations: [
      { source: '桩号', target: '里程', relation: '表示' },
      { source: 'K', target: '千米', relation: '含义' }
    ]
  },
  '缓和曲线': {
    answer: '缓和曲线是设置在直线与圆曲线之间的过渡曲线，使车辆行驶更加平稳舒适。常用的缓和曲线类型有回旋线和三次抛物线。',
    entities: [
      { id: '1', name: '回旋线', type: '曲线类型' },
      { id: '2', name: '三次抛物线', type: '曲线类型' }
    ],
    relations: [
      { source: '缓和曲线', target: '直线', relation: '连接' },
      { source: '缓和曲线', target: '圆曲线', relation: '连接' }
    ]
  }
}

export default function KnowledgeQA() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<Array<{q: string, a: string}>>([])
  
  // 预设问题
  const presetQuestions = [
    '什么是公路桩号?',
    '缓和曲线的作用是什么?',
    '公路有哪些等级?',
    '平曲线设计要素有哪些?',
    '纵断面设计考虑什么?'
  ]
  
  // 处理查询
  const handleQuery = async () => {
    if (!question.trim()) return
    
    setLoading(true)
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 简单的关键词匹配
    let result = null
    const q = question.toLowerCase()
    
    if (q.includes('桩号')) {
      result = mockKGData['桩号']
    } else if (q.includes('缓和曲线')) {
      result = mockKGData['缓和曲线']
    } else if (q.includes('公路')) {
      result = mockKGData['公路']
    } else {
      result = {
        answer: '抱歉，我目前知识库中还没有收录这个问题。你可以尝试查询：桩号、缓和曲线、公路等级等关键词。',
        entities: [],
        relations: []
      }
    }
    
    setAnswer(result)
    setHistory(prev => [...prev, { q: question, a: result.answer }])
    setQuestion('')
    setLoading(false)
  }
  
  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleQuery()
    }
  }
  
  // 处理预设问题
  const handlePreset = (q: string) => {
    setQuestion(q)
  }

  return (
    <div className="knowledge-qa">
      {/* 标题 */}
      <div className="header">
        <h2>💡 知识问答</h2>
        <p>基于知识图谱的智能问答系统</p>
      </div>
      
      {/* 预设问题 */}
      <div className="preset-section">
        <h4>常见问题</h4>
        <div className="preset-buttons">
          {presetQuestions.map((q, i) => (
            <button 
              key={i} 
              className="preset-btn"
              onClick={() => handlePreset(q)}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
      
      {/* 输入区域 */}
      <div className="input-section">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="请输入问题..."
          className="question-input"
        />
        <button 
          className="query-btn"
          onClick={handleQuery}
          disabled={loading || !question.trim()}
        >
          {loading ? '查询中...' : '查询'}
        </button>
      </div>
      
      {/* 回答区域 */}
      {answer && (
        <div className="answer-section">
          <h3>回答</h3>
          <div className="answer-content">
            <p>{answer.answer}</p>
          </div>
          
          {/* 关联实体 */}
          {answer.entities && answer.entities.length > 0 && (
            <div className="entities">
              <h4>相关实体</h4>
              <div className="entity-list">
                {answer.entities.map((e: any) => (
                  <span key={e.id} className="entity-tag">
                    {e.name} <small>({e.type})</small>
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* 关系 */}
          {answer.relations && answer.relations.length > 0 && (
            <div className="relations">
              <h4>知识图谱关系</h4>
              <div className="relation-list">
                {answer.relations.map((r: any, i: number) => (
                  <div key={i} className="relation-item">
                    <span className="source">{r.source}</span>
                    <span className="relation">—{r.relation}→</span>
                    <span className="target">{r.target}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* 历史记录 */}
      {history.length > 0 && (
        <div className="history-section">
          <h4>历史记录</h4>
          <div className="history-list">
            {history.slice(-5).reverse().map((item, i) => (
              <div key={i} className="history-item">
                <div className="history-q">Q: {item.q}</div>
                <div className="history-a">A: {item.a.substring(0, 50)}...</div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <style>{`
        .knowledge-qa {
          display: flex;
          flex-direction: column;
          height: 100%;
          padding: 20px;
          overflow-y: auto;
          gap: 20px;
        }
        
        .header h2 {
          font-size: 20px;
          color: #00ff88;
          margin-bottom: 4px;
        }
        
        .header p {
          font-size: 13px;
          color: #888;
        }
        
        .preset-section {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 16px;
        }
        
        .preset-section h4 {
          font-size: 13px;
          color: #888;
          margin-bottom: 12px;
        }
        
        .preset-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        
        .preset-btn {
          padding: 8px 14px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 20px;
          color: #aaa;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .preset-btn:hover {
          background: #667eea;
          border-color: #667eea;
          color: #fff;
        }
        
        .input-section {
          display: flex;
          gap: 12px;
        }
        
        .question-input {
          flex: 1;
          padding: 14px 18px;
          background: #1a1a2e;
          border: 1px solid #444;
          border-radius: 8px;
          color: #fff;
          font-size: 15px;
        }
        
        .question-input:focus {
          outline: none;
          border-color: #667eea;
        }
        
        .query-btn {
          padding: 14px 28px;
          background: linear-gradient(135deg, #667eea, #764ba2);
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }
        
        .query-btn:hover:not(:disabled) {
          transform: translateY(-2px);
        }
        
        .query-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .answer-section {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
        }
        
        .answer-section h3 {
          font-size: 16px;
          color: #00ff88;
          margin-bottom: 12px;
        }
        
        .answer-content {
          background: #252540;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 16px;
        }
        
        .answer-content p {
          color: #eee;
          line-height: 1.6;
          font-size: 14px;
        }
        
        .entities, .relations {
          margin-bottom: 16px;
        }
        
        .entities h4, .relations h4 {
          font-size: 12px;
          color: #888;
          margin-bottom: 10px;
        }
        
        .entity-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        
        .entity-tag {
          padding: 6px 12px;
          background: #252540;
          border: 1px solid #667eea;
          border-radius: 16px;
          color: #fff;
          font-size: 12px;
        }
        
        .entity-tag small {
          color: #888;
          margin-left: 4px;
        }
        
        .relation-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .relation-item {
          font-size: 13px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .relation-item .source {
          color: #667eea;
        }
        
        .relation-item .relation {
          color: #888;
        }
        
        .relation-item .target {
          color: #00ff88;
        }
        
        .history-section {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 16px;
        }
        
        .history-section h4 {
          font-size: 13px;
          color: #888;
          margin-bottom: 12px;
        }
        
        .history-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .history-item {
          padding: 10px;
          background: #252540;
          border-radius: 6px;
          font-size: 12px;
        }
        
        .history-q {
          color: #667eea;
          margin-bottom: 4px;
        }
        
        .history-a {
          color: #aaa;
        }
      `}</style>
    </div>
  )
}
