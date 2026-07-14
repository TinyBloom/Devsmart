import React, { useState, useEffect } from 'react';

interface TechOption {
  key: string;
  name: string;
  pros: string[];
  cons: string[];
  suitable_for: string[];
  not_suitable_for: string[];
  complexity: string;
  performance: string;
  time_to_market: string;
}

interface TechStackRecommendation {
  name: string;
  description: string;
  backend: TechOption;
  frontend: TechOption;
  database: TechOption;
  cache?: TechOption;
  deployment: TechOption;
  cicd: TechOption;
  reason: string;
  trade_offs: {
    pros: string[];
    cons: string[];
    complexity: string;
    performance: string;
    time_to_market: string;
    suitable_for: string[];
    not_suitable_for: string[];
  };
}

interface ValidationResult {
  status: 'passed' | 'warning';
  warnings: Array<{
    type: string;
    severity: string;
    message: string;
    suggestion?: string;
  }>;
  suggestions: Array<{
    type: string;
    message: string;
  }>;
  summary: string;
}

interface TechStackSelectorProps {
  projectName: string;
  onComplete: (techStack: any) => void;
}

const TechStackSelector: React.FC<TechStackSelectorProps> = ({ projectName, onComplete }) => {
  const [library, setLibrary] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<TechStackRecommendation[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTechStackLibrary();
  }, [projectName]);

  const loadTechStackLibrary = async () => {
    try {
      setLoading(true);
      // 获取技术栈选项库
      const libResponse = await fetch('/api/tech-stack/library');
      const libData = await libResponse.json();
      setLibrary(libData.library);

      // 获取推荐方案
      const recResponse = await fetch('/api/tech-stack/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_name: projectName })
      });
      const recData = await recResponse.json();
      setRecommendations(recData.recommendations || []);
      setAnalysis(recData.analysis || {});
    } catch (err) {
      setError('加载技术栈信息失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (index: number) => {
    setSelectedIndex(index);

    // 验证选择
    const selected = recommendations[index];
    if (!selected) return;

    const stackSelection = {
      backend: { key: selected.backend.key, name: selected.backend.name },
      frontend: { key: selected.frontend.key, name: selected.frontend.name },
      database: { key: selected.database.key, name: selected.database.name },
      cache: selected.cache ? { key: selected.cache.key, name: selected.cache.name } : null,
      deployment: { key: selected.deployment.key, name: selected.deployment.name },
      cicd: { key: selected.cicd.key, name: selected.cicd.name }
    };

    try {
      const response = await fetch('/api/tech-stack/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectName,
          selected_stack: stackSelection
        })
      });
      const data = await response.json();
      setValidation(data.validation);
    } catch (err) {
      console.error('验证失败:', err);
    }
  };

  const handleConfirm = async () => {
    const selected = recommendations[selectedIndex];
    if (!selected) return;

    setSaving(true);
    try {
      const stackSelection = {
        backend: { key: selected.backend.key, name: selected.backend.name },
        frontend: { key: selected.frontend.key, name: selected.frontend.name },
        database: { key: selected.database.key, name: selected.database.name },
        cache: selected.cache ? { key: selected.cache.key, name: selected.cache.name } : null,
        deployment: { key: selected.deployment.key, name: selected.deployment.name },
        cicd: { key: selected.cicd.key, name: selected.cicd.name }
      };

      const response = await fetch(`/api/tech-stack/${projectName}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(stackSelection)
      });

      if (response.ok) {
        onComplete(stackSelection);
      } else {
        setError('保存技术栈失败');
      }
    } catch (err) {
      setError('保存技术栈失败');
    } finally {
      setSaving(false);
    }
  };

  const renderTradeOffBadge = (label: string, value: string) => {
    const colorMap: Record<string, string> = {
      '极高': 'bg-green-100 text-green-800',
      '高': 'bg-green-50 text-green-700',
      '中': 'bg-yellow-100 text-yellow-800',
      '低': 'bg-red-100 text-red-800',
      '快': 'bg-green-100 text-green-800',
      '很快': 'bg-green-100 text-green-800',
      '慢': 'bg-red-100 text-red-800',
      '高(复杂)': 'bg-red-100 text-red-800'
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colorMap[value] || 'bg-gray-100 text-gray-800'}`}>
        {label}: {value}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">加载技术栈选项...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-600">{error}</p>
        <button
          onClick={loadTechStackLibrary}
          className="mt-2 text-sm text-blue-600 hover:underline"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900">需求分析</h3>
        <div className="mt-2 text-sm text-blue-700">
          {analysis && (
            <div className="grid grid-cols-2 gap-2">
              <span>规模: {analysis.scale}</span>
              <span>团队: {analysis.team?.size || '未知'}</span>
              <span>性能要求: {analysis.performance}</span>
              <span>时间压力: {analysis.time_pressure}</span>
            </div>
          )}
        </div>
        {library && (
          <div className="mt-3 pt-3 border-t border-blue-200">
            <h4 className="text-xs font-medium text-blue-700 uppercase">可用技术栈选项</h4>
            <div className="flex flex-wrap gap-2 mt-1 text-xs">
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                后端: {Object.keys(library.backend || {}).length}
              </span>
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                前端: {Object.keys(library.frontend || {}).length}
              </span>
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                数据库: {Object.keys(library.database || {}).length}
              </span>
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                部署: {Object.keys(library.deployment || {}).length}
              </span>
            </div>
          </div>
        )}
      </div>

      <h3 className="text-lg font-medium text-gray-900">推荐方案</h3>

      <div className="space-y-4">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
              selectedIndex === index
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleSelect(index)}
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-medium text-gray-900">{rec.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                <p className="text-sm text-blue-600 mt-2">
                  <span className="font-medium">推荐理由:</span> {rec.reason}
                </p>
              </div>
              {selectedIndex === index && (
                <div className="flex-shrink-0">
                  <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              )}
            </div>

            {/* 权衡指标 */}
            <div className="flex gap-2 mt-3 flex-wrap">
              {renderTradeOffBadge('复杂度', rec.trade_offs.complexity)}
              {renderTradeOffBadge('性能', rec.trade_offs.performance)}
              {renderTradeOffBadge('上市时间', rec.trade_offs.time_to_market)}
            </div>

            {/* 详细技术栈 */}
            {selectedIndex === index && (
              <div className="mt-4 border-t pt-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <h5 className="text-xs font-medium text-gray-500 uppercase">后端</h5>
                    <p className="mt-1 font-medium">{rec.backend.name}</p>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-500 uppercase">前端</h5>
                    <p className="mt-1 font-medium">{rec.frontend.name}</p>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-500 uppercase">数据库</h5>
                    <p className="mt-1 font-medium">{rec.database.name}</p>
                  </div>
                  {rec.cache && (
                    <div>
                      <h5 className="text-xs font-medium text-gray-500 uppercase">缓存</h5>
                      <p className="mt-1 font-medium">{rec.cache.name}</p>
                    </div>
                  )}
                  <div>
                    <h5 className="text-xs font-medium text-gray-500 uppercase">部署</h5>
                    <p className="mt-1 font-medium">{rec.deployment.name}</p>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-500 uppercase">CI/CD</h5>
                    <p className="mt-1 font-medium">{rec.cicd.name}</p>
                  </div>
                </div>

                {/* 优缺点 */}
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <h5 className="text-xs font-medium text-green-600 uppercase">优点</h5>
                    <ul className="mt-1 text-sm text-gray-700 space-y-1">
                      {rec.trade_offs.pros.slice(0, 3).map((pro, i) => (
                        <li key={i} className="flex items-start">
                          <span className="text-green-500 mr-1">+</span>
                          {pro}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-red-600 uppercase">缺点</h5>
                    <ul className="mt-1 text-sm text-gray-700 space-y-1">
                      {rec.trade_offs.cons.slice(0, 3).map((con, i) => (
                        <li key={i} className="flex items-start">
                          <span className="text-red-500 mr-1">-</span>
                          {con}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 适用场景 */}
                <div className="mt-4">
                  <h5 className="text-xs font-medium text-gray-500 uppercase">适用场景</h5>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {rec.trade_offs.suitable_for.map((s, i) => (
                      <span key={i} className="px-2 py-0.5 bg-green-50 text-green-700 rounded text-xs">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 验证结果 */}
      {validation && selectedIndex >= 0 && (
        <div className={`border rounded-lg p-4 ${
          validation.status === 'passed' ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'
        }`}>
          <h4 className={`font-medium ${validation.status === 'passed' ? 'text-green-900' : 'text-yellow-900'}`}>
            {validation.status === 'passed' ? '验证通过' : '存在警告'}
          </h4>
          <p className="text-sm mt-1 text-gray-700">{validation.summary}</p>

          {validation.warnings.map((w, i) => (
            <div key={i} className="mt-2 p-2 bg-white border border-yellow-200 rounded">
              <p className="text-sm text-yellow-800">
                <span className="font-medium">⚠️ {w.severity.toUpperCase()}:</span> {w.message}
              </p>
              {w.suggestion && (
                <p className="text-sm text-gray-600 mt-1">建议: {w.suggestion}</p>
              )}
            </div>
          ))}

          {validation.suggestions.map((s, i) => (
            <div key={i} className="mt-2 p-2 bg-white border border-blue-200 rounded">
              <p className="text-sm text-blue-800">💡 {s.message}</p>
            </div>
          ))}
        </div>
      )}

      {/* 确认按钮 */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          onClick={handleConfirm}
          disabled={saving || recommendations.length === 0}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? '保存中...' : '确认技术栈'}
        </button>
      </div>
    </div>
  );
};

export default TechStackSelector;
