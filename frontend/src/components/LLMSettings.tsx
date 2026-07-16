import { useState, useEffect } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  LoaderCircle,
  Save,
  SlidersHorizontal,
  Wifi,
  X,
} from 'lucide-react';
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
    } finally {
      setTesting(false);
    }
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
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="settings-overlay" role="dialog" aria-modal="true" aria-labelledby="llm-settings-title">
      <div className="settings-panel">
        <div className="settings-header">
          <div>
            <div className="page-eyebrow">Workspace settings</div>
            <h2 id="llm-settings-title">LLM 设置</h2>
          </div>
          <button type="button" className="close-btn" onClick={onClose} aria-label="关闭设置">
            <X size={19} strokeWidth={1.8} aria-hidden="true" />
          </button>
        </div>

        <div className="settings-content">
          <div className="setting-group">
            <label>LLM 提供商</label>
            <div className="provider-options" role="group" aria-label="LLM 提供商">
              {PROVIDERS.map((provider) => (
                <button
                  type="button"
                  key={provider}
                  className={`provider-btn ${settings.llm_provider === provider ? 'active' : ''}`}
                  onClick={() => handleProviderChange(provider)}
                >
                  {PROVIDER_DISPLAY_NAMES[provider] || provider}
                </button>
              ))}
            </div>
          </div>

          <div className="setting-group">
            <label htmlFor="llm-model">模型选择</label>
            {settings.llm_provider === 'custom' ? (
              <input
                id="llm-model"
                type="text"
                value={settings.llm_model}
                onChange={(event) => setSettings({ ...settings, llm_model: event.target.value })}
                placeholder="输入自定义模型名称"
                className="model-input"
              />
            ) : (
              <select
                id="llm-model"
                value={settings.llm_model}
                onChange={(event) => setSettings({ ...settings, llm_model: event.target.value })}
                className="model-select"
              >
                {PROVIDER_MODELS[settings.llm_provider]?.map((model) => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            )}
          </div>

          {(settings.llm_provider === 'custom' || settings.llm_provider === 'ollama') && (
            <div className="setting-group">
              <label htmlFor="base-url">Base URL</label>
              <input
                id="base-url"
                type="url"
                value={settings.base_url}
                onChange={(event) => setSettings({ ...settings, base_url: event.target.value })}
                placeholder="API 基础地址"
                className="base-url-input"
              />
              <p className="hint">Ollama 默认地址为 http://localhost:11434</p>
            </div>
          )}

          <div className="setting-group">
            <label htmlFor="api-key">API Key</label>
            <div className="api-key-input">
              <input
                id="api-key"
                type={showApiKey ? 'text' : 'password'}
                value={settings.api_key}
                onChange={(event) => setSettings({ ...settings, api_key: event.target.value })}
                placeholder="API Key（可选，环境变量优先）"
                autoComplete="off"
              />
              <button
                type="button"
                className="toggle-visibility"
                onClick={() => setShowApiKey(!showApiKey)}
                aria-label={showApiKey ? '隐藏 API Key' : '显示 API Key'}
              >
                {showApiKey ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
                <span>{showApiKey ? '隐藏' : '显示'}</span>
              </button>
            </div>
            <p className="hint">通过环境变量注入 Key 时可以留空。</p>
          </div>

          <div className="setting-group advanced">
            <label><SlidersHorizontal size={15} aria-hidden="true" />高级参数</label>

            <div className="param-item">
              <span>温度</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(event) => setSettings({ ...settings, temperature: parseFloat(event.target.value) })}
                aria-label="温度"
              />
              <span className="param-value">{settings.temperature}</span>
            </div>

            <div className="param-item">
              <span>最大 Token</span>
              <input
                type="number"
                value={settings.max_tokens}
                onChange={(event) => setSettings({ ...settings, max_tokens: parseInt(event.target.value, 10) })}
                min="100"
                max="100000"
                aria-label="最大 Token"
              />
            </div>

            <div className="param-item">
              <span>流式输出</span>
              <input
                type="checkbox"
                checked={settings.streaming}
                onChange={(event) => setSettings({ ...settings, streaming: event.target.checked })}
                aria-label="流式输出"
              />
            </div>
          </div>

          {testResult && (
            <div className={`test-result ${testResult.status}`} role="status">
              <div className="flex items-center gap-2 font-semibold">
                {testResult.status === 'success' ? <CheckCircle2 size={16} aria-hidden="true" /> : <AlertCircle size={16} aria-hidden="true" />}
                <span>{testResult.message}</span>
              </div>
              {testResult.response_time && <p className="response-time">响应时间：{testResult.response_time}ms</p>}
            </div>
          )}
        </div>

        <div className="settings-footer">
          <button type="button" className="test-btn" onClick={handleTestConnection} disabled={testing || saving}>
            {testing ? <LoaderCircle size={16} className="loading-icon" aria-hidden="true" /> : <Wifi size={16} aria-hidden="true" />}
            {testing ? '测试中...' : '测试连接'}
          </button>
          <button type="button" className="save-btn" onClick={handleSave} disabled={saving || testing}>
            {saving ? <LoaderCircle size={16} className="loading-icon" aria-hidden="true" /> : <Save size={16} aria-hidden="true" />}
            {saving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  );
}
