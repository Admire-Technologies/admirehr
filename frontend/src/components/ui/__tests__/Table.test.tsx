import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../Table';

describe('Table', () => {
  const TableExample = () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead sortable onSort={() => {}}>
            Status
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>John Doe</TableCell>
          <TableCell>john@example.com</TableCell>
          <TableCell>Active</TableCell>
        </TableRow>
        <TableRow onClick={() => {}}>
          <TableCell>Jane Smith</TableCell>
          <TableCell>jane@example.com</TableCell>
          <TableCell>Inactive</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );

  it('renders table with headers and data', () => {
    render(<TableExample />);

    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('renders sortable column header', () => {
    const mockOnSort = jest.fn();
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead sortable onSort={mockOnSort}>
              Sortable Column
            </TableHead>
          </TableRow>
        </TableHeader>
      </Table>
    );

    const sortableHeader = screen.getByText('Sortable Column');
    expect(sortableHeader).toHaveClass('cursor-pointer');

    fireEvent.click(sortableHeader);
    expect(mockOnSort).toHaveBeenCalledTimes(1);
  });

  it('renders clickable table row', () => {
    const mockOnClick = jest.fn();
    render(
      <Table>
        <TableBody>
          <TableRow onClick={mockOnClick}>
            <TableCell>Clickable Row</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );

    const row = screen.getByText('Clickable Row').closest('tr');
    expect(row).toHaveClass('cursor-pointer');

    if (row) {
      fireEvent.click(row);
      expect(mockOnClick).toHaveBeenCalledTimes(1);
    }
  });

  it('applies custom className to table components', () => {
    render(
      <Table className="custom-table">
        <TableHeader className="custom-header">
          <TableRow className="custom-row">
            <TableHead className="custom-head">Header</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody className="custom-body">
          <TableRow>
            <TableCell className="custom-cell">Cell</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );

    const table = screen.getByText('Header').closest('table');
    expect(table).toHaveClass('custom-table');
  });
});
