import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../Tabs';

describe('Tabs', () => {
  const TabsExample = () => (
    <Tabs defaultValue="tab1">
      <TabsList>
        <TabsTrigger value="tab1">Tab 1</TabsTrigger>
        <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        <TabsTrigger value="tab3" disabled>
          Tab 3
        </TabsTrigger>
      </TabsList>
      <TabsContent value="tab1">Content 1</TabsContent>
      <TabsContent value="tab2">Content 2</TabsContent>
      <TabsContent value="tab3">Content 3</TabsContent>
    </Tabs>
  );

  it('renders tabs with default active tab', () => {
    render(<TabsExample />);

    expect(screen.getByText('Tab 1')).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('Tab 2')).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByText('Content 1')).toBeInTheDocument();
    expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
  });

  it('switches tabs when clicked', () => {
    render(<TabsExample />);

    const tab2 = screen.getByText('Tab 2');
    fireEvent.click(tab2);

    expect(screen.getByText('Tab 2')).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByText('Tab 1')).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByText('Content 2')).toBeInTheDocument();
    expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
  });

  it('does not switch to disabled tab', () => {
    render(<TabsExample />);

    const tab3 = screen.getByText('Tab 3');
    fireEvent.click(tab3);

    expect(screen.getByText('Tab 3')).toHaveAttribute('aria-selected', 'false');
    expect(screen.getByText('Content 1')).toBeInTheDocument();
    expect(screen.queryByText('Content 3')).not.toBeInTheDocument();
  });

  it('calls onChange callback when tab changes', () => {
    const mockOnChange = jest.fn();
    render(
      <Tabs defaultValue="tab1" onChange={mockOnChange}>
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
        <TabsContent value="tab2">Content 2</TabsContent>
      </Tabs>
    );

    const tab2 = screen.getByText('Tab 2');
    fireEvent.click(tab2);

    expect(mockOnChange).toHaveBeenCalledWith('tab2');
  });

  it('has proper ARIA attributes', () => {
    render(<TabsExample />);

    const tabList = screen.getByRole('tablist');
    expect(tabList).toBeInTheDocument();

    const tabs = screen.getAllByRole('tab');
    expect(tabs).toHaveLength(3);

    const tabPanel = screen.getByRole('tabpanel');
    expect(tabPanel).toHaveAttribute('id', 'tabpanel-tab1');
    expect(tabPanel).toHaveAttribute('aria-labelledby', 'tab-tab1');
  });
});
