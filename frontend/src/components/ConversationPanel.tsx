/**
 * ConversationPanel Component
 * Phase 1 对话界面组件
 * 根据 DevSmart_PRD_v1.0.md Section 5.1 定义
 * 支持模板选择
 */

import { useState, useEffect, useRef } from 'react';
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
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
    loadTemplates();
  }, [projectId]);

  useEffect(() => {
    scrollToBottom();
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

        // 获取完整度分数
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
          template_id: selectedTemplate || undefined
        })
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);

      if (response.ok) {
        const data = await response.json();
        console.log('Response data:', data);

        if (data.user_message && data.assistant_message) {
          setConversations(prev => [
            ...prev,
            data.user_message,
            data.assistant_message
          ]);

          setCompletenessScore(data.completeness_score);
          setIsReadyForPrd(data.is_ready_for_prd);
        } else {
          console.error('消息数据不完整:', data);
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('发送消息失败:', errorData);
      }
    } catch (error) {
      console.error('发送消息失败:', error);
    }

    setLoading(false);
  };

  const generatePrd = async () => {
    if (conversations.length === 0) return;

    setLoading(true);
    try {
      const response = await fetch('/api/prd/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          project_id: projectId,
          template_id: selectedTemplate || undefined
        })
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
    }

    setLoading(false);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="conversation-panel">
      {/* 完整度进度条 */}
      <div className="completeness-bar">
        <div className="progress-info">
          <span>需求完整度</span>
          <span className="score">{completenessScore}%</span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${completenessScore}%` }}
          />
        </div>
        
        {/* 模板选择器 */}
        <div className="template-selector">
          <label>选择PRD模板:</label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            disabled={loading}
          >
            {templates.map(template => (
              <option key={template.id} value={template.id}>
                {template.icon} {template.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="prd-actions">
          {isReadyForPrd && (
            <button
              className="generate-prd-btn ready"
              onClick={generatePrd}
              disabled={loading}
            >
              ✅ 需求完整，生成 PRD
            </button>
          )}
          <button
            className="generate-prd-btn manual"
            onClick={generatePrd}
            disabled={loading || conversations.length === 0}
          >
            {isReadyForPrd ? '重新生成 PRD' : '手动生成 PRD'}
          </button>
        </div>
      </div>

      {/* 对话历史 */}
      <div className="messages-container">
        {conversations.length === 0 && (
          <div className="welcome-message">
            <h3>开始描述你的项目需求</h3>
            <p>项目: {projectName}</p>
            <p>在下方输入框中描述你的项目想法，我会通过追问帮你梳理需求细节。</p>
          </div>
        )}

        {conversations.filter(m => m.role !== 'system').map((message) => (
          <div
            key={message.id}
            className={`message ${message.role}`}
          >
            <div className="message-avatar">
              {message.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              {message.role === 'assistant' ? (
                <MarkdownRenderer content={message.content} />
              ) : (
                <div className="message-text">{message.content}</div>
              )}
              <div className="message-time">
                {new Date(message.created_at).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="loading-indicator">思考中...</div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <div className="input-container">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="输入你的想法..."
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !inputValue.trim()}
        >
          发送
        </button>
      </div>

      <style>{`
        .conversation-panel {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: #f5f5f5;
        }

        .completeness-bar {
          padding: 15px 20px;
          background: white;
          border-bottom: 1px solid #ddd;
        }

        .progress-info {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        .score {
          font-weight: bold;
          color: #4CAF50;
        }

        .progress-bar {
          height: 8px;
          background: #e0e0e0;
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(to right, #4CAF50, #8BC34A);
          transition: width 0.3s ease;
        }

        .template-selector {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 10px;
        }

        .template-selector label {
          font-size: 14px;
          color: #666;
        }

        .template-selector select {
          padding: 6px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
          background: white;
        }

        .template-selector select:disabled {
          background: #f5f5f5;
          cursor: not-allowed;
        }

        .prd-actions {
          display: flex;
          gap: 10px;
          margin-top: 10px;
        }

        .generate-prd-btn {
          padding: 10px 20px;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
        }

        .generate-prd-btn.ready {
          background: #4CAF50;
        }

        .generate-prd-btn.manual {
          background: #FF9800;
        }

        .generate-prd-btn:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .welcome-message {
          text-align: center;
          padding: 40px 20px;
          color: #666;
        }

        .message {
          display: flex;
          margin-bottom: 20px;
        }

        .message.user {
          flex-direction: row-reverse;
        }

        .message-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: #e0e0e0;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          margin: 0 10px;
        }

        .message.user .message-avatar {
          background: #2196F3;
        }

        .message.assistant .message-avatar {
          background: #9C27B0;
        }

        .message-content {
          max-width: 70%;
          padding: 15px;
          border-radius: 12px;
          background: white;
        }

        .message.user .message-content {
          background: #E3F2FD;
        }

        .message-text {
          line-height: 1.6;
        }

        .message-time {
          margin-top: 5px;
          font-size: 12px;
          color: #888;
        }

        .loading-indicator {
          color: #888;
        }

        .input-container {
          padding: 20px;
          background: white;
          border-top: 1px solid #ddd;
          display: flex;
          gap: 10px;
        }

        .input-container input {
          flex: 1;
          padding: 10px 15px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 14px;
        }

        .input-container button {
          padding: 10px 20px;
          background: #2196F3;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
        }

        .input-container button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}