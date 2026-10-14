import React from 'react';

interface PageHeaderProps {
  title: string;
  description: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  actions,
}) => {
  return (
    <div className="optiv-page-header">
      <div className="optiv-page-header-content">
        <div className="optiv-page-header-title-row">
          <h1 className="optiv-page-title">{title}</h1>
          {badge}
        </div>
        <p className="optiv-page-description">{description}</p>
      </div>

      {actions && <div className="optiv-page-header-actions">{actions}</div>}
    </div>
  );
};
