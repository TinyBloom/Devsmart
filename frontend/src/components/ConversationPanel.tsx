import { useState, useEffect, useRef } from 'react';
import type { KeyboardEvent } from 'react';
import {
  Bot,
  CheckCircle2,
  FileText,
  LoaderCircle,
  RefreshCw,
  Send,
  Sparkles,
  UserRound,
} from 'lucide-react';
import type { Conversation } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';

interface PRDTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  dimensions: Record<string, number>;
}

interface ConversationPanelProps {
  projectId: string;
  projectName: string;
  onPrdGenerated?: () => void;
}

export function ConversationPanel({ projectId, projectName, onPrdGenerated }: ConversationPanelProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [completenessScore, setCompletenessScore] = useState(0);
  const [isReadyForPrd, setIsReadyForPrd] = useState(false);
  const [templates, setTemplates] = useState<PRDTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
    loadTemplates();
  }, [projectId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversations]);

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/prd/templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
        if (data.length > 0) {
          setSelectedTemplate(data[0].id);
        }
      }
    } catch (error) {
      console.error('加载模板列表失败:', error);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await fetch(`/api/conversations/${projectId}?phase=prd`);
      if (response.ok) {
        const data = await response.json();
        setConversations(data);

        if (data.length > 0) {
          const lastMessage = data[data.length - 1];
          if (lastMessage.completeness_score) {
            setCompletenessScore(lastMessage.completeness_score);
          }
        }
      }
    } catch (error) {
      console.error('加载对话历史失败:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    setLoading(true);
    const userMessage = inputValue.trim();
    setInputValue('');

    try {
      const response = await fetch(`/api/conversations/${projectId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: userMessage,
          phase: 'prd',
          template_id: selectedTemplate || undefined,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.user_message && data.assistant_message) {
          setConversations((previous) => [
            ...previous,
            data.user_message,
            data.assistant_message,
          ]);
          setCompletenessScore(data.completeness_score);
          setIsReadyForPrd(data.is_ready_for_prd);
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: '发送失败' }));
        console.error('发送消息失败:', errorData);
      }
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const generatePrd = async () => {
    if (conversations.length === 0 || loading) return;

    setLoading(true);
    try {
      const response = await fetch('/api/prd/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          template_id: selectedTemplate || undefined,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(`PRD 已生成！\nHuman PRD: ${data.human_prd_path}\nMachine PRD: ${data.machine_prd_path}`);
        onPrdGenerated?.();
      } else {
        const errorData = await response.json().catch(() => ({ detail: '生成失败' }));
        alert(`生成 PRD 失败: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('生成 PRD 失败:', error);
      alert('生成 PRD 失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleInputKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.nativeEvent.isComposing) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="conversation-panel">
      <div className="completeness-bar">
        <div className="progress-info">
          <span>需求完整度</span>
          <span className="score">{completenessScore}%</span>
        </div>
        <div
          className="progress-bar"
          role="progressbar"
          aria-label="需求完整度"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={completenessScore}
        >
          <div className="progress-fill" style={{ width: `${completenessScore}%` }} />
        </div>

        <div className="conversation-controls">
          <div className="template-selector">
            <label htmlFor="template-select">PRD 模板</label>
            <select
              id="template-select"
              value={selectedTemplate}
              onChange={(event) => setSelectedTemplate(event.target.value)}
              disabled={loading}
            >
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>

          <div className="prd-actions">
            {isReadyForPrd && (
              <button
                type="button"
                className="generate-prd-btn ready"
                onClick={generatePrd}
                disabled={loading}
              >
                <CheckCircle2 size={15} aria-hidden="true" />
                需求完整，生成 PRD
              </button>
            )}
            <button
              type="button"
              className="generate-prd-btn manual"
              onClick={generatePrd}
              disabled={loading || conversations.length === 0}
            >
              {isReadyForPrd ? <RefreshCw size={15} aria-hidden="true" /> : <FileText size={15} aria-hidden="true" />}
              {isReadyForPrd ? '重新生成 PRD' : '手动生成 PRD'}
            </button>
          </div>
        </div>
      </div>

      <div className="messages-container" aria-live="polite">
        {conversations.length === 0 && (
          <div className="welcome-message">
            <div className="welcome-icon">
              <Sparkles size={24} strokeWidth={1.7} aria-hidden="true" />
            </div>
            <h3>从一句话开始描述你的项目</h3>
            <p>当前项目：{projectName}</p>
            <p>我会通过逐步追问，帮你补全功能、用户、数据和技术约束。</p>
          </div>
        )}

        {conversations.filter((message) => message.role !== 'system').map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-avatar" aria-hidden="true">
              {message.role === 'user' ? <UserRound size={17} strokeWidth={1.8} /> : <Bot size={17} strokeWidth={1.8} />}
            </div>
            <div className="message-content">
              {message.role === 'assistant' ? (
                <MarkdownRenderer content={message.content} />
              ) : (
                <div className="message-text">{message.content}</div>
              )}
              <div className="message-time">{new Date(message.created_at).toLocaleTimeString()}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-avatar" aria-hidden="true">
              <Bot size={17} strokeWidth={1.8} />
            </div>
            <div className="message-content">
              <div className="loading-inline">
                <LoaderCircle size={16} className="loading-icon" aria-hidden="true" />
                <span>正在思考...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <label htmlFor="conversation-input" className="sr-only">输入项目需求</label>
        <input
          id="conversation-input"
          type="text"
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          onKeyDown={handleInputKeyDown}
          placeholder="输入你的项目想法..."
          disabled={loading}
        />
        <button
          type="button"
          onClick={sendMessage}
          disabled={loading || !inputValue.trim()}
          aria-label="发送消息"
        >
          <Send size={16} aria-hidden="true" />
          发送
        </button>
      </div>
    </div>
  );
}
