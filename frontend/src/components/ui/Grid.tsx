import React from 'react';

interface GridProps {
  children: React.ReactNode;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: number;
  className?: string;
}

export function Grid({ children, cols = { default: 1, md: 2, lg: 3 }, gap = 4, className = '' }: GridProps) {
  const colClasses = [
    cols.default && `grid-cols-${cols.default}`,
    cols.sm && `sm:grid-cols-${cols.sm}`,
    cols.md && `md:grid-cols-${cols.md}`,
    cols.lg && `lg:grid-cols-${cols.lg}`,
    cols.xl && `xl:grid-cols-${cols.xl}`,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={`grid ${colClasses} gap-${gap} ${className}`}>
      {children}
    </div>
  );
}

interface GridItemProps {
  children: React.ReactNode;
  colSpan?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  className?: string;
}

export function GridItem({ children, colSpan, className = '' }: GridItemProps) {
  const spanClasses = colSpan
    ? [
        colSpan.default && `col-span-${colSpan.default}`,
        colSpan.sm && `sm:col-span-${colSpan.sm}`,
        colSpan.md && `md:col-span-${colSpan.md}`,
        colSpan.lg && `lg:col-span-${colSpan.lg}`,
        colSpan.xl && `xl:col-span-${colSpan.xl}`,
      ]
        .filter(Boolean)
        .join(' ')
    : '';

  return <div className={`${spanClasses} ${className}`}>{children}</div>;
}
