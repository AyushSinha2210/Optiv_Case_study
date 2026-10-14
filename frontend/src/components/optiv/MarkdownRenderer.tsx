import React from 'react';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  if (!content) return null;

  // Split into lines for block-level processing
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeBlockLines: string[] = [];
  let currentListItems: React.ReactNode[] = [];
  let listKey = 0;

  const flushList = () => {
    if (currentListItems.length > 0) {
      elements.push(
        <ul key={`ul-${listKey++}`} className="optiv-markdown-list">
          {currentListItems}
        </ul>
      );
      currentListItems = [];
    }
  };

  const parseInline = (text: string): React.ReactNode[] => {
    // Parse inline bold (**...**), inline code (`...`), and plain text
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let keyIdx = 0;

    while (remaining.length > 0) {
      // Look for code `...`
      const codeStart = remaining.indexOf('`');
      // Look for bold **...**
      const boldStart = remaining.indexOf('**');

      if (codeStart !== -1 && (boldStart === -1 || codeStart < boldStart)) {
        const codeEnd = remaining.indexOf('`', codeStart + 1);
        if (codeEnd !== -1) {
          if (codeStart > 0) {
            parts.push(remaining.slice(0, codeStart));
          }
          parts.push(
            <code key={`code-${keyIdx++}`} className="optiv-inline-code">
              {remaining.slice(codeStart + 1, codeEnd)}
            </code>
          );
          remaining = remaining.slice(codeEnd + 1);
          continue;
        }
      }

      if (boldStart !== -1) {
        const boldEnd = remaining.indexOf('**', boldStart + 2);
        if (boldEnd !== -1) {
          if (boldStart > 0) {
            parts.push(remaining.slice(0, boldStart));
          }
          parts.push(
            <strong key={`bold-${keyIdx++}`} style={{ fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
              {parseInline(remaining.slice(boldStart + 2, boldEnd))}
            </strong>
          );
          remaining = remaining.slice(boldEnd + 2);
          continue;
        }
      }

      // No more inline matches
      parts.push(remaining);
      break;
    }

    return parts;
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Code block fences ```
    if (trimmed.startsWith('```')) {
      if (inCodeBlock) {
        // End code block
        elements.push(
          <pre key={`pre-${idx}`} className="optiv-code-block">
            <code>{codeBlockLines.join('\n')}</code>
          </pre>
        );
        codeBlockLines = [];
        inCodeBlock = false;
      } else {
        flushList();
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      return;
    }

    // Unordered List Items (- or *)
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const itemText = trimmed.slice(2);
      currentListItems.push(
        <li key={`li-${idx}`} className="optiv-markdown-li">
          {parseInline(itemText)}
        </li>
      );
      return;
    }

    // Not in a list item, flush any existing list
    flushList();

    // Empty lines
    if (!trimmed) {
      return;
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      elements.push(
        <h3 key={`h3-${idx}`} className="optiv-markdown-h3">
          {parseInline(trimmed.slice(4))}
        </h3>
      );
      return;
    }
    if (trimmed.startsWith('## ')) {
      elements.push(
        <h2 key={`h2-${idx}`} className="optiv-markdown-h2">
          {parseInline(trimmed.slice(3))}
        </h2>
      );
      return;
    }
    if (trimmed.startsWith('# ')) {
      elements.push(
        <h1 key={`h1-${idx}`} className="optiv-markdown-h1">
          {parseInline(trimmed.slice(2))}
        </h1>
      );
      return;
    }

    // Blockquote
    if (trimmed.startsWith('> ')) {
      elements.push(
        <blockquote key={`bq-${idx}`} className="optiv-markdown-blockquote">
          {parseInline(trimmed.slice(2))}
        </blockquote>
      );
      return;
    }

    // Regular paragraph
    elements.push(
      <p key={`p-${idx}`} className="optiv-markdown-p">
        {parseInline(line)}
      </p>
    );
  });

  flushList();

  return <div className="optiv-markdown-container">{elements}</div>;
};
