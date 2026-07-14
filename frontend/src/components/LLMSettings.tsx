/**
 * LLMSettings Component
 * LLM 设置页面组件
 * 根据 DevSmart_PRD_v1.0.md Section 5.0.7 设计
 */

import { useState, useEffect } from 'react';
import type { LLMSettings as LLMSettingsType, TestConnectionResult } from '../types';
import { settingsApi } from '../services/api';

interface LLMSettingsProps {
  onClose: () => void;
}

const PROVIDERS = [
  'openai',
  'anthropic',
  'google',
  'ollama',
  'kimi',
  'glm',
  'bytedance',
  'minimax',
  'qwen',
  'custom',
];

const PROVIDER_MODELS: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
  anthropic: ['claude-sonnet-4-6', 'claude-3-5-sonnet', 'claude-3-opus', 'claude-3-sonnet'],
  google: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
  ollama: ['llama3', 'mistral', 'phi3', 'qwen'],
  kimi: ['kimi', 'kimi-8k', 'kimi-32k', 'kimi-128k'],
  glm: ['glm-4', 'glm-4-9b', 'glm-3-turbo', 'glm-3-9b'],
  bytedance: ['doubao', 'doubao-pro', 'doubao-lite'],
  minimax: ['abab6-chat', 'abab5.5-chat', 'abab5-chat'],
  qwen: ['qwen-2', 'qwen-2.5', 'qwen-plus', 'qwen-turbo', 'qwen-long'],
  custom: [],
};

const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
  ollama: 'Ollama',
  kimi: 'Kimi',
  glm: 'GLM',
  bytedance: 'ByteDance',
  minimax: 'MiniMax',
  qwen: 'Qwen',
  custom: '自定义',
};

export function LLMSettings({ onClose }: LLMSettingsProps) {
  const [settings, setSettings] = useState<LLMSettingsType>({
    id: '',
    llm_provider: 'anthropic',
    llm_model: 'claude-sonnet-4-6',
    api_key: '',
    base_url: '',
    temperature: 0.7,
    max_tokens: 8192,
    streaming: true,
    created_at: '',
    updated_at: '',
  });

  const [testResult, setTestResult] = useState<TestConnectionResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await settingsApi.getSettings();
      setSettings(data);
    } catch (error) {
      console.error('加载设置失败:', error);
    }
  };

  const handleProviderChange = (provider: string) => {
    const models = PROVIDER_MODELS[provider];
    const defaultModel = models.length > 0 ? models[0] : '';
    setSettings({ ...settings, llm_provider: provider, llm_model: defaultModel });
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await settingsApi.testConnection();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        status: 'error',
        message: '测试失败，请检查配置',
        provider: settings.llm_provider,
        model: settings.llm_model,
      });
    }
    setTesting(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await settingsApi.updateSettings({
        llm_provider: settings.llm_provider,
        llm_model: settings.llm_model,
        api_key: settings.api_key,
        base_url: settings.base_url,
        temperature: settings.temperature,
        max_tokens: settings.max_tokens,
        streaming: settings.streaming,
      });
      onClose();
    } catch (error) {
      console.error('保存设置失败:', error);
    }
    setSaving(false);
  };

  return (
    <div className="settings-overlay">
      <div className="settings-panel">
        <div className="settings-header">
          <h2>LLM 设置</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="settings-content">
          {/* 1. LLM 提供商 */}
          <div className="setting-group">
            <label>LLM 提供商</label>
            <div className="provider-options">
              {PROVIDERS.map((provider) => (
                <button
                  key={provider}
                  className={`provider-btn ${settings.llm_provider === provider ? 'active' : ''}`}
                  onClick={() => handleProviderChange(provider)}
                >
                  {PROVIDER_DISPLAY_NAMES[provider] || provider}
                </button>
              ))}
            </div>
          </div>

          {/* 2. 模型选择 */}
          <div className="setting-group">
            <label>模型选择</label>
            {settings.llm_provider === 'custom' ? (
              <input
                type="text"
                value={settings.llm_model}
                onChange={(e) => setSettings({ ...settings, llm_model: e.target.value })}
                placeholder="输入自定义模型名称"
                className="model-input"
              />
            ) : (
              <select
                value={settings.llm_model}
                onChange={(e) => setSettings({ ...settings, llm_model: e.target.value })}
                className="model-select"
              >
                {PROVIDER_MODELS[settings.llm_provider]?.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* 3. 自定义 Base URL（自定义模式时显示） */}
          {(settings.llm_provider === 'custom' || settings.llm_provider === 'ollama') && (
            <div className="setting-group">
              <label>Base URL</label>
              <input
                type="text"
                value={settings.base_url}
                onChange={(e) => setSettings({ ...settings, base_url: e.target.value })}
                placeholder="API 基础地址"
                className="base-url-input"
              />
              <p className="hint">提示：Ollama 默认 http://localhost:11434</p>
            </div>
          )}

          {/* 3. API Key */}
          <div className="setting-group">
            <label>API Key</label>
            <div className="api-key-input">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={settings.api_key}
                onChange={(e) => setSettings({ ...settings, api_key: e.target.value })}
                placeholder="API Key（可选，环境变量优先）"
              />
              <button
                className="toggle-visibility"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? '隐藏' : '显示'}
              </button>
            </div>
            <p className="hint">提示：Key 通过环境变量注入时留空</p>
          </div>

          {/* 4. 高级参数 */}
          <div className="setting-group advanced">
            <label>高级参数</label>

            <div className="param-item">
              <span>温度</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
              />
              <span className="param-value">{settings.temperature}</span>
            </div>

            <div className="param-item">
              <span>最大 Token</span>
              <input
                type="number"
                value={settings.max_tokens}
                onChange={(e) => setSettings({ ...settings, max_tokens: parseInt(e.target.value) })}
                min="100"
                max="100000"
              />
            </div>

            <div className="param-item">
              <span>流式输出</span>
              <input
                type="checkbox"
                checked={settings.streaming}
                onChange={(e) => setSettings({ ...settings, streaming: e.target.checked })}
              />
            </div>
          </div>

          {/* 测试结果 */}
          {testResult && (
            <div className={`test-result ${testResult.status}`}>
              <p>{testResult.message}</p>
              {testResult.response_time && (
                <p className="response-time">响应时间: {testResult.response_time}ms</p>
              )}
            </div>
          )}
        </div>

        <div className="settings-footer">
          <button className="test-btn" onClick={handleTestConnection} disabled={testing}>
            {testing ? '测试中...' : '测试连接'}
          </button>
          <button className="save-btn" onClick={handleSave} disabled={saving}>
            {saving ? '保存中...' : '保存设置'}
          </button>
        </div>

      </div>

      <style>{`
        .settings-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .settings-panel {
          background: white;
          border-radius: 16px;
          width: 500px;
          max-width: 90%;
          max-height: 90vh;
          overflow: auto;
        }

        .settings-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #ddd;
        }

        .settings-header h2 {
          font-size: 18px;
          color: #333;
        }

        .close-btn {
          width: 30px;
          height: 30px;
          border: none;
          background: transparent;
          font-size: 24px;
          cursor: pointer;
          color: #888;
        }

        .settings-content {
          padding: 20px;
        }

        .setting-group {
          margin-bottom: 20px;
        }

        .setting-group label {
          display: block;
          margin-bottom: 10px;
          font-size: 14px;
          font-weight: 600;
          color: #333;
        }

        .provider-options {
          display: flex;
          gap: 10px;
        }

        .provider-btn {
          padding: 8px 16px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          font-size: 13px;
        }

        .provider-btn.active {
          background: #4CAF50;
          color: white;
          border-color: #4CAF50;
        }

        .model-select {
          width: 100%;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 14px;
        }

        .api-key-input {
          display: flex;
          gap: 10px;
        }

        .api-key-input input {
          flex: 1;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 14px;
        }

        .toggle-visibility {
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          font-size: 13px;
        }

        .hint {
          font-size: 12px;
          color: #888;
          margin-top: 5px;
        }

        .advanced .param-item {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
        }

        .param-item span:first-child {
          width: 100px;
          font-size: 13px;
        }

        .param-item input[type="range"] {
          flex: 1;
        }

        .param-value {
          width: 40px;
          text-align: right;
        }

        .param-item input[type="number"] {
          flex: 1;
          padding: 5px 10px;
          border: 1px solid #ddd;
          border-radius: 6px;
        }

        .param-item input[type="checkbox"] {
          width: 20px;
          height: 20px;
        }

        .test-result {
          padding: 15px;
          border-radius: 8px;
          margin-top: 15px;
        }

        .test-result.success {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .test-result.error {
          background: #ffebee;
          color: #c62828;
        }

        .response-time {
          font-size: 12px;
          margin-top: 5px;
        }

        .settings-footer {
          display: flex;
          gap: 10px;
          padding: 20px;
          border-top: 1px solid #ddd;
        }

        .test-btn {
          flex: 1;
          padding: 12px;
          border: none;
          border-radius: 8px;
          background: #2196F3;
          color: white;
          cursor: pointer;
          font-size: 14px;
        }

        .test-btn:disabled {
          background: #ccc;
        }

        .save-btn {
          flex: 1;
          padding: 12px;
          border: none;
          border-radius: 8px;
          background: #4CAF50;
          color: white;
          cursor: pointer;
          font-size: 14px;
        }

        .save-btn:disabled {
          background: #ccc;
        }
      `}</style>
    </div>
  );
}