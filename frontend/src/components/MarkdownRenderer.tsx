import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
      <style>{`
        .markdown-content {
          line-height: 1.8;
          color: #333;
        }

        .markdown-content h1 {
          font-size: 24px;
          font-weight: bold;
          margin: 24px 0 16px;
          padding-bottom: 8px;
          border-bottom: 2px solid #eee;
          color: #1a1a1a;
        }

        .markdown-content h2 {
          font-size: 20px;
          font-weight: bold;
          margin: 20px 0 12px;
          color: #222;
        }

        .markdown-content h3 {
          font-size: 16px;
          font-weight: bold;
          margin: 16px 0 10px;
          color: #333;
        }

        .markdown-content h4 {
          font-size: 14px;
          font-weight: bold;
          margin: 12px 0 8px;
          color: #444;
        }

        .markdown-content p {
          margin: 10px 0;
        }

        .markdown-content ul, .markdown-content ol {
          padding-left: 24px;
          margin: 10px 0;
        }

        .markdown-content li {
          margin: 6px 0;
        }

        .markdown-content li > ul, .markdown-content li > ol {
          margin: 4px 0;
          padding-left: 20px;
        }

        .markdown-content blockquote {
          border-left: 4px solid #2196F3;
          padding: 10px 16px;
          margin: 12px 0;
          background: #f5f9ff;
          color: #555;
          font-style: italic;
        }

        .markdown-content code {
          background: #f4f4f4;
          padding: 2px 6px;
          border-radius: 4px;
          font-family: 'Consolas', 'Monaco', monospace;
          font-size: 14px;
          color: #c7254e;
        }

        .markdown-content pre {
          background: #2d2d2d;
          padding: 16px;
          border-radius: 8px;
          overflow-x: auto;
          margin: 12px 0;
        }

        .markdown-content pre code {
          background: none;
          padding: 0;
          color: #ccc;
          font-size: 13px;
          line-height: 1.6;
        }

        .markdown-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 16px 0;
          font-size: 14px;
        }

        .markdown-content th, .markdown-content td {
          border: 1px solid #ddd;
          padding: 10px 12px;
          text-align: left;
        }

        .markdown-content th {
          background: #f5f5f5;
          font-weight: bold;
          color: #333;
        }

        .markdown-content tr:nth-child(even) {
          background: #f9f9f9;
        }

        .markdown-content a {
          color: #2196F3;
          text-decoration: none;
        }

        .markdown-content a:hover {
          text-decoration: underline;
        }

        .markdown-content hr {
          border: none;
          border-top: 1px solid #eee;
          margin: 20px 0;
        }

        .markdown-content strong {
          font-weight: bold;
          color: #222;
        }

        .markdown-content em {
          font-style: italic;
        }
      `}</style>
    </div>
  );
}
