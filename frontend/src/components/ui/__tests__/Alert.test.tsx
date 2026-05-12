import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Alert } from '../Alert';

describe('Alert', () => {
  it('renders alert with children', () => {
    render(<Alert>Test alert message</Alert>);
    expect(screen.getByText('Test alert message')).toBeInTheDocument();
  });

  it('renders alert with title', () => {
    render(<Alert title="Alert Title">Test message</Alert>);
    expect(screen.getByText('Alert Title')).toBeInTheDocument();
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('renders different variants correctly', () => {
    const { rerender } = render(<Alert variant="info">Info message</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('bg-info-50');

    rerender(<Alert variant="success">Success message</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('bg-success-50');

    rerender(<Alert variant="warning">Warning message</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('bg-warning-50');

    rerender(<Alert variant="danger">Danger message</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('bg-danger-50');
  });

  it('renders dismiss button when dismissible', () => {
    const mockOnDismiss = jest.fn();
    render(
      <Alert dismissible onDismiss={mockOnDismiss}>
        Dismissible alert
      </Alert>
    );

    const dismissButton = screen.getByLabelText('Dismiss alert');
    expect(dismissButton).toBeInTheDocument();

    fireEvent.click(dismissButton);
    expect(mockOnDismiss).toHaveBeenCalledTimes(1);
  });

  it('does not render dismiss button when not dismissible', () => {
    render(<Alert>Non-dismissible alert</Alert>);
    expect(screen.queryByLabelText('Dismiss alert')).not.toBeInTheDocument();
  });

  it('has proper ARIA attributes', () => {
    render(<Alert>Test alert</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('aria-live', 'polite');
  });
});
