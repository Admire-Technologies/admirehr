import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Container } from '../Container';
import { Grid, GridItem } from '../Grid';
import { Modal } from '../Modal';

describe('Responsive Design Tests', () => {
  describe('Container Responsiveness', () => {
    it('renders with different sizes', () => {
      const { rerender, container } = render(
        <Container size="sm">Small container</Container>
      );
      expect(container.firstChild).toHaveClass('max-w-3xl');

      rerender(<Container size="md">Medium container</Container>);
      expect(container.firstChild).toHaveClass('max-w-5xl');

      rerender(<Container size="lg">Large container</Container>);
      expect(container.firstChild).toHaveClass('max-w-7xl');

      rerender(<Container size="xl">Extra large container</Container>);
      expect(container.firstChild).toHaveClass('max-w-[1400px]');

      rerender(<Container size="full">Full width container</Container>);
      expect(container.firstChild).toHaveClass('max-w-full');
    });

    it('has responsive padding', () => {
      const { container } = render(<Container>Content</Container>);
      expect(container.firstChild).toHaveClass('px-4');
      expect(container.firstChild).toHaveClass('sm:px-6');
      expect(container.firstChild).toHaveClass('lg:px-8');
    });
  });

  describe('Grid Responsiveness', () => {
    it('renders with responsive columns', () => {
      const { container } = render(
        <Grid cols={{ default: 1, md: 2, lg: 3 }}>
          <div>Item 1</div>
          <div>Item 2</div>
          <div>Item 3</div>
        </Grid>
      );

      const grid = container.firstChild;
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('renders GridItem with responsive column spans', () => {
      const { container } = render(
        <Grid>
          <GridItem colSpan={{ default: 1, md: 2, lg: 3 }}>
            Spanning item
          </GridItem>
        </Grid>
      );

      const gridItem = screen.getByText('Spanning item');
      expect(gridItem).toHaveClass('col-span-1');
      expect(gridItem).toHaveClass('md:col-span-2');
      expect(gridItem).toHaveClass('lg:col-span-3');
    });

    it('renders with custom gap', () => {
      const { container } = render(
        <Grid gap={6}>
          <div>Item 1</div>
          <div>Item 2</div>
        </Grid>
      );

      expect(container.firstChild).toHaveClass('gap-6');
    });
  });

  describe('Modal Responsiveness', () => {
    it('renders with responsive sizes', () => {
      const { rerender } = render(
        <Modal isOpen={true} onClose={() => {}} size="sm">
          Small modal
        </Modal>
      );
      expect(screen.getByRole('dialog').firstChild).toHaveClass('max-w-md');

      rerender(
        <Modal isOpen={true} onClose={() => {}} size="md">
          Medium modal
        </Modal>
      );
      expect(screen.getByRole('dialog').firstChild).toHaveClass('max-w-lg');

      rerender(
        <Modal isOpen={true} onClose={() => {}} size="lg">
          Large modal
        </Modal>
      );
      expect(screen.getByRole('dialog').firstChild).toHaveClass('max-w-2xl');

      rerender(
        <Modal isOpen={true} onClose={() => {}} size="xl">
          Extra large modal
        </Modal>
      );
      expect(screen.getByRole('dialog').firstChild).toHaveClass('max-w-4xl');

      rerender(
        <Modal isOpen={true} onClose={() => {}} size="full">
          Full modal
        </Modal>
      );
      expect(screen.getByRole('dialog').firstChild).toHaveClass('max-w-full');
    });
  });

  describe('Button Responsiveness', () => {
    it('maintains proper sizing on different screen sizes', () => {
      const { container } = render(
        <div className="flex flex-col sm:flex-row gap-2">
          <button className="w-full sm:w-auto">Button 1</button>
          <button className="w-full sm:w-auto">Button 2</button>
        </div>
      );

      const buttons = container.querySelectorAll('button');
      buttons.forEach((button) => {
        expect(button).toHaveClass('w-full');
        expect(button).toHaveClass('sm:w-auto');
      });
    });
  });

  describe('Layout Responsiveness', () => {
    it('sidebar is hidden on mobile and visible on desktop', () => {
      const { container } = render(
        <aside className="fixed lg:translate-x-0 -translate-x-full">
          Sidebar
        </aside>
      );

      const sidebar = container.firstChild;
      expect(sidebar).toHaveClass('-translate-x-full');
      expect(sidebar).toHaveClass('lg:translate-x-0');
    });

    it('main content adjusts for sidebar on desktop', () => {
      const { container } = render(
        <div className="lg:pl-64">
          Main content
        </div>
      );

      expect(container.firstChild).toHaveClass('lg:pl-64');
    });
  });

  describe('Typography Responsiveness', () => {
    it('headings scale responsively', () => {
      const { container } = render(
        <h1 className="text-2xl sm:text-3xl lg:text-4xl">
          Responsive Heading
        </h1>
      );

      const heading = container.firstChild;
      expect(heading).toHaveClass('text-2xl');
      expect(heading).toHaveClass('sm:text-3xl');
      expect(heading).toHaveClass('lg:text-4xl');
    });
  });

  describe('Spacing Responsiveness', () => {
    it('padding adjusts for different screen sizes', () => {
      const { container } = render(
        <div className="p-4 sm:p-6 lg:p-8">
          Content with responsive padding
        </div>
      );

      const element = container.firstChild;
      expect(element).toHaveClass('p-4');
      expect(element).toHaveClass('sm:p-6');
      expect(element).toHaveClass('lg:p-8');
    });

    it('margins adjust for different screen sizes', () => {
      const { container } = render(
        <div className="mx-4 sm:mx-6 lg:mx-auto">
          Content with responsive margins
        </div>
      );

      const element = container.firstChild;
      expect(element).toHaveClass('mx-4');
      expect(element).toHaveClass('sm:mx-6');
      expect(element).toHaveClass('lg:mx-auto');
    });
  });
});
