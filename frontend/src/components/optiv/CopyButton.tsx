import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface CopyButtonProps {
  text: string;
  label?: string;
  className?: string;
  iconSize?: number;
}

export const CopyButton: React.FC<CopyButtonProps> = ({
  text,
  label,
  className = 'optiv-btn-header icon-only',
  iconSize = 13,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older environments
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.warn('Failed to copy to clipboard', err);
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={className}
      title={copied ? 'Copied to clipboard!' : `Copy ID: ${text}`}
      aria-label={copied ? 'Copied to clipboard' : `Copy ID ${text}`}
      style={{ cursor: 'pointer', flexShrink: 0 }}
    >
      {copied ? (
        <Check size={iconSize} color="var(--tprm-emerald)" />
      ) : (
        <Copy size={iconSize} color="var(--tprm-text-muted)" />
      )}
      {label && <span style={{ marginLeft: 4 }}>{copied ? 'Copied' : label}</span>}
    </button>
  );
};
