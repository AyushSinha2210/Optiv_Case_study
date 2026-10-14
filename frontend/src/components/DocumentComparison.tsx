import React, { useState } from 'react';
import type { DetectedEntity } from '../types';
import { Eye, ShieldAlert, FileCheck2, Filter, Lock } from 'lucide-react';

interface DocumentComparisonProps {
  extractedText: string | null;
  redactedText: string | null;
  entities: DetectedEntity[];
  releaseAllowed: boolean;
  verificationStatus: string | null;
}

export const DocumentComparison: React.FC<DocumentComparisonProps> = ({
  extractedText,
  redactedText,
  entities,
  releaseAllowed,
  verificationStatus,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  const filteredEntities = selectedCategory === 'ALL'
    ? entities
    : entities.filter((e) => e.type.toUpperCase() === selectedCategory.toUpperCase());

  const categories = Array.from(new Set(entities.map((e) => e.type.toUpperCase())));

  // Render text with highlighted spans for detected PII entities
  const renderHighlightedOriginal = () => {
    if (!extractedText) return <p style={{ color: '#64748b' }}>No text extracted.</p>;
    if (entities.length === 0) return <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{extractedText}</pre>;

    // Sort entities by start offset ascending
    const sorted = [...entities].sort((a, b) => a.start - b.start);
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    sorted.forEach((ent, i) => {
      if (ent.start > lastIndex) {
        elements.push(extractedText.slice(lastIndex, ent.start));
      }
      const val = extractedText.slice(ent.start, ent.end);
      const isFiltered = selectedCategory === 'ALL' || ent.type.toUpperCase() === selectedCategory.toUpperCase();

      elements.push(
        <span
          key={`ent-${i}`}
          className={isFiltered ? 'highlight-entity' : ''}
          style={{ opacity: isFiltered ? 1 : 0.6 }}
          title={`${ent.type} (${(ent.confidence * 100).toFixed(0)}% confidence, span [${ent.start}, ${ent.end}))`}
        >
          {val}
        </span>
      );
      lastIndex = ent.end;
    });

    if (lastIndex < extractedText.length) {
      elements.push(extractedText.slice(lastIndex));
    }

    return (
      <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', lineHeight: '1.6' }}>
        {elements}
      </pre>
    );
  };

  const getBadgeClass = (type: string) => {
    switch (type.toUpperCase()) {
      case 'EMAIL': return 'badge-email';
      case 'PHONE': return 'badge-phone';
      case 'GOVERNMENT_ID': return 'badge-gov';
      case 'FINANCIAL_IDENTIFIER': return 'badge-card';
      case 'EMPLOYEE_ID': return 'badge-emp';
      case 'IP_ADDRESS': return 'badge-ip';
      case 'PERSON': return 'badge-person';
      default: return 'badge-generic';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Category Filter Chips */}
      {categories.length > 0 && (
        <div className="glass-panel" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', color: '#94a3b8' }}>
            <Filter size={16} />
            <span>Filter by PII Category:</span>
          </div>
          <button
            onClick={() => setSelectedCategory('ALL')}
            className={`btn-secondary ${selectedCategory === 'ALL' ? 'glow-cyan' : ''}`}
            style={{ padding: '4px 10px', fontSize: '0.75rem', borderColor: selectedCategory === 'ALL' ? '#06b6d4' : undefined }}
          >
            All Entities ({entities.length})
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`badge ${getBadgeClass(cat)}`}
              style={{
                cursor: 'pointer',
                padding: '4px 10px',
                border: selectedCategory === cat ? '1px solid #ffffff' : undefined,
                boxShadow: selectedCategory === cat ? '0 0 10px rgba(255,255,255,0.4)' : undefined,
              }}
            >
              {cat} ({entities.filter((e) => e.type.toUpperCase() === cat).length})
            </button>
          ))}
        </div>
      )}

      {/* Side-by-Side Comparison Panels */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 20 }}>
        {/* Left Panel: Original Document with Highlighted Entities */}
        <div className="glass-panel" style={{ padding: 20, display: 'flex', flexDirection: 'column', height: '420px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, borderBottom: '1px solid var(--border-color)', paddingBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Eye size={18} color="#06b6d4" />
              <h4 style={{ margin: 0, fontSize: '0.95rem' }}>Original Document (Detected Entities Highlighted)</h4>
            </div>
            <span className="badge badge-gov">{entities.length} PII Flagged</span>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', background: 'rgba(10, 15, 29, 0.6)', padding: 14, borderRadius: 8, border: '1px solid rgba(51, 65, 85, 0.4)' }}>
            {renderHighlightedOriginal()}
          </div>
        </div>

        {/* Right Panel: Sanitized Redacted Output */}
        <div className="glass-panel" style={{ padding: 20, display: 'flex', flexDirection: 'column', height: '420px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, borderBottom: '1px solid var(--border-color)', paddingBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileCheck2 size={18} color={releaseAllowed ? '#10b981' : '#ef4444'} />
              <h4 style={{ margin: 0, fontSize: '0.95rem' }}>Sanitized Output Artifact (Protected Masking)</h4>
            </div>
            <span className={`badge ${releaseAllowed ? 'badge-phone' : 'badge-gov'}`}>
              {releaseAllowed ? 'VERIFICATION PASS' : 'RELEASE WITHHELD'}
            </span>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', background: 'rgba(10, 15, 29, 0.6)', padding: 14, borderRadius: 8, border: '1px solid rgba(51, 65, 85, 0.4)' }}>
            {releaseAllowed && redactedText ? (
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', lineHeight: '1.6', color: '#e2e8f0' }}>
                {redactedText}
              </pre>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 14, textAlign: 'center', color: '#94a3b8' }}>
                <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: 16, borderRadius: '50%', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                  <Lock size={36} color="#ef4444" />
                </div>
                <div>
                  <h4 style={{ color: '#f87171', marginBottom: 6 }}>Sanitized Artifact Withheld</h4>
                  <p style={{ fontSize: '0.8rem', maxWidth: 360, margin: '0 auto' }}>
                    Independent verification evaluated to <strong>{verificationStatus || 'FAIL'}</strong>. Under the fail-closed release gate, unverified artifacts cannot be displayed or egressed.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Entity Classification Inventory Table */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h4 style={{ margin: 0, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <ShieldAlert size={18} color="#06b6d4" />
            Classified Entity Spans Inventory ({filteredEntities.length})
          </h4>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Character Offsets: 0-based, end-exclusive</span>
        </div>

        {filteredEntities.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No PII entities detected matching current filter.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: '#94a3b8' }}>
                  <th style={{ padding: '8px 12px' }}>Entity Type</th>
                  <th style={{ padding: '8px 12px' }}>Character Span [Start, End)</th>
                  <th style={{ padding: '8px 12px' }}>Detector Confidence</th>
                  <th style={{ padding: '8px 12px' }}>Detected Sensitive Value</th>
                  <th style={{ padding: '8px 12px' }}>Replacement Mask</th>
                </tr>
              </thead>
              <tbody>
                {filteredEntities.map((ent, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.3)' }}>
                    <td style={{ padding: '8px 12px' }}>
                      <span className={`badge ${getBadgeClass(ent.type)}`}>{ent.type}</span>
                    </td>
                    <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>
                      [{ent.start}, {ent.end}) ({ent.end - ent.start} chars)
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 60, height: 6, background: 'rgba(51, 65, 85, 0.5)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${ent.confidence * 100}%`, height: '100%', background: ent.confidence >= 0.9 ? '#10b981' : '#f59e0b' }} />
                        </div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#94a3b8' }}>
                          {(ent.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#f87171', fontWeight: 600 }}>
                      {ent.value}
                    </td>
                    <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                      {ent.masked_value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
