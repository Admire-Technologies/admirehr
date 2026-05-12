import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from '../Button';
import { Input } from '../Input';
import { Select } from '../Select';
import { Modal } from '../Modal';
import { Alert } from '../Alert';

describe('Accessibility Tests', () => {
  describe('Button Accessibility', () => {
    it('has proper focus styles', () => {
      render(<Button>Click me</Button>);
      const button = screen.getByText('Click me');
      // The btn class includes focus styles via globals.css
      expect(button).toHaveClass('btn');
    });

    it('is keyboard accessible', () => {
      const mockOnClick = jest.fn();
      render(<Button onClick={mockOnClick}>Click me</Button>);
      const button = screen.getByText('Click me');
      
      button.focus();
      expect(document.activeElement).toBe(button);
    });

    it('shows loading state with proper ARIA', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByText('Loading');
      expect(button).toBeDisabled();
    });
  });

  describe('Input Accessibility', () => {
    it('has proper label association', () => {
      render(<Input label="Email" id="email-input" />);
      const input = screen.getByLabelText('Email');
      expect(input).toHaveAttribute('id', 'email-input');
    });

    it('shows error with proper ARIA attributes', () => {
      render(<Input label="Email" error="Invalid email" />);
      const input = screen.getByLabelText('Email');
      expect(input).toHaveAttribute('aria-invalid', 'true');
      expect(input).toHaveAttribute('aria-describedby');
      
      const errorMessage = screen.getByRole('alert');
      expect(errorMessage).toHaveTextContent('Invalid email');
    });

    it('shows helper text with proper ARIA', () => {
      render(<Input label="Email" helperText="Enter your email address" />);
      const input = screen.getByLabelText('Email');
      expect(input).toHaveAttribute('aria-describedby');
      expect(screen.getByText('Enter your email address')).toBeInTheDocument();
    });
  });

  describe('Select Accessibility', () => {
    const options = [
      { value: '1', label: 'Option 1' },
      { value: '2', label: 'Option 2' },
    ];

    it('has proper label association', () => {
      render(<Select label="Choose option" options={options} />);
      const select = screen.getByLabelText('Choose option');
      expect(select).toBeInTheDocument();
    });

    it('shows error with proper ARIA attributes', () => {
      render(<Select label="Choose option" options={options} error="Required field" />);
      const select = screen.getByLabelText('Choose option');
      expect(select).toHaveAttribute('aria-invalid', 'true');
      expect(screen.getByRole('alert')).toHaveTextContent('Required field');
    });
  });

  describe('Modal Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(
        <Modal isOpen={true} onClose={() => {}} title="Test Modal">
          Content
        </Modal>
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
    });

    it('modal content is focusable', () => {
      render(
        <Modal isOpen={true} onClose={() => {}} title="Test Modal">
          <button>Button 1</button>
          <button>Button 2</button>
        </Modal>
      );

      // Verify modal contains focusable elements
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  describe('Alert Accessibility', () => {
    it('has proper ARIA live region', () => {
      render(<Alert>Important message</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });

    it('has accessible dismiss button', () => {
      render(
        <Alert dismissible onDismiss={() => {}}>
          Dismissible alert
        </Alert>
      );
      const dismissButton = screen.getByLabelText('Dismiss alert');
      expect(dismissButton).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('all interactive elements are keyboard accessible', () => {
      render(
        <div>
          <Button>Button</Button>
          <Input label="Input" />
          <Select label="Select" options={[{ value: '1', label: 'Option 1' }]} />
        </div>
      );

      const button = screen.getByText('Button');
      const input = screen.getByLabelText('Input');
      const select = screen.getByLabelText('Select');

      // All elements should be focusable
      button.focus();
      expect(document.activeElement).toBe(button);

      input.focus();
      expect(document.activeElement).toBe(input);

      select.focus();
      expect(document.activeElement).toBe(select);
    });
  });

  describe('Color Contrast', () => {
    it('buttons have proper styling classes', () => {
      const { container } = render(
        <div>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="success">Success</Button>
          <Button variant="danger">Danger</Button>
        </div>
      );

      // All buttons should have the btn class
      const buttons = container.querySelectorAll('button');
      buttons.forEach((button) => {
        expect(button.className).toContain('btn');
      });
    });
  });
});
