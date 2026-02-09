import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  if (!content) return null;

  // Normalize escaped newlines from API/MCP storage to actual line breaks
  const normalized = content.replace(/\\n/g, '\n');

  return (
    <div className={`markdown-body${className ? ` ${className}` : ''}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalized}</ReactMarkdown>
    </div>
  );
}
