import React from 'react';

interface TableProps {
  children: React.ReactNode;
  className?: string;
}

export function Table({ children, className = '' }: TableProps) {
  return (
    <div className="w-full overflow-x-auto">
      <table className={`w-full text-sm text-left ${className}`}>
        {children}
      </table>
    </div>
  );
}

interface TableHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function TableHeader({ children, className = '' }: TableHeaderProps) {
  return (
    <thead className={`text-xs uppercase bg-gray-50 dark:bg-gray-800 ${className}`}>
      {children}
    </thead>
  );
}

interface TableBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function TableBody({ children, className = '' }: TableBodyProps) {
  return (
    <tbody className={className}>
      {children}
    </tbody>
  );
}

interface TableRowProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function TableRow({ children, className = '', onClick }: TableRowProps) {
  return (
    <tr
      className={`border-b border-gray-200 dark:border-gray-700 ${
        onClick ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800' : ''
      } ${className}`}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

interface TableHeadProps {
  children: React.ReactNode;
  className?: string;
  sortable?: boolean;
  onSort?: () => void;
}

export function TableHead({ children, className = '', sortable, onSort }: TableHeadProps) {
  return (
    <th
      scope="col"
      className={`px-6 py-3 text-gray-700 dark:text-gray-300 font-semibold ${
        sortable ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700' : ''
      } ${className}`}
      onClick={sortable ? onSort : undefined}
    >
      {children}
    </th>
  );
}

interface TableCellProps {
  children: React.ReactNode;
  className?: string;
}

export function TableCell({ children, className = '' }: TableCellProps) {
  return (
    <td className={`px-6 py-4 text-gray-900 dark:text-gray-100 ${className}`}>
      {children}
    </td>
  );
}
