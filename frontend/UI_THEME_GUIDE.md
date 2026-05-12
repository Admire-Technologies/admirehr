# Admire HRMS UI Theme Guide

## Overview

This document provides comprehensive guidance on the Metronic-inspired UI theme implementation in Admire HRMS. The theme is built with Tailwind CSS and follows modern design principles with full support for dark mode, responsive design, and accessibility.

## Table of Contents

1. [Color System](#color-system)
2. [Typography](#typography)
3. [Components](#components)
4. [Layout System](#layout-system)
5. [Responsive Design](#responsive-design)
6. [Dark Mode](#dark-mode)
7. [Accessibility](#accessibility)
8. [Testing](#testing)

## Color System

### Primary Colors

The theme uses a comprehensive color palette with semantic naming:

```typescript
// Primary - Main brand color (Indigo)
primary: {
  50: '#eef2ff',
  100: '#e0e7ff',
  200: '#c7d2fe',
  300: '#a5b4fc',
  400: '#818cf8',
  500: '#6366f1',  // Base
  600: '#4f46e5',
  700: '#4338ca',
  800: '#3730a3',
  900: '#312e81',
}
```

### Semantic Colors

- **Success**: Green shades for positive actions and states
- **Warning**: Amber shades for caution and warnings
- **Danger**: Red shades for errors and destructive actions
- **Info**: Blue shades for informational messages

### Usage

```tsx
// Background
<div className="bg-primary-500">Primary background</div>

// Text
<p className="text-success-600">Success message</p>

// Border
<div className="border border-danger-500">Error border</div>

// Dark mode variants
<div className="bg-white dark:bg-gray-900">Adaptive background</div>
```

## Typography

### Font Family

The theme uses Inter font family for clean, modern typography:

```tsx
import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });
```

### Text Sizes

```tsx
// Headings
<h1 className="text-4xl font-bold">Main Heading</h1>
<h2 className="text-3xl font-semibold">Section Heading</h2>
<h3 className="text-2xl font-semibold">Subsection Heading</h3>

// Body text
<p className="text-base">Regular text</p>
<p className="text-sm">Small text</p>
<p className="text-xs">Extra small text</p>
```

### Responsive Typography

```tsx
<h1 className="text-2xl sm:text-3xl lg:text-4xl">
  Responsive heading
</h1>
```

## Components

### Button

```tsx
import { Button } from '@/components/ui';

// Variants
<Button variant="primary">Primary Button</Button>
<Button variant="secondary">Secondary Button</Button>
<Button variant="success">Success Button</Button>
<Button variant="danger">Danger Button</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// Loading state
<Button loading>Loading...</Button>
```

### Card

```tsx
import { Card, CardHeader, CardBody, CardFooter } from '@/components/ui';

<Card>
  <CardHeader>
    <h3 className="text-lg font-semibold">Card Title</h3>
  </CardHeader>
  <CardBody>
    <p>Card content goes here</p>
  </CardBody>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

### Modal

```tsx
import { Modal, ModalFooter } from '@/components/ui';

<Modal
  isOpen={isOpen}
  onClose={handleClose}
  title="Modal Title"
  size="md"
>
  <p>Modal content</p>
  <ModalFooter>
    <Button variant="secondary" onClick={handleClose}>
      Cancel
    </Button>
    <Button onClick={handleSave}>Save</Button>
  </ModalFooter>
</Modal>
```

### Form Components

```tsx
import { Input, Select, Textarea } from '@/components/ui';

// Input
<Input
  label="Email"
  type="email"
  placeholder="Enter your email"
  error="Invalid email"
  helperText="We'll never share your email"
/>

// Select
<Select
  label="Country"
  options={[
    { value: 'us', label: 'United States' },
    { value: 'uk', label: 'United Kingdom' },
  ]}
  placeholder="Select a country"
/>

// Textarea
<Textarea
  label="Description"
  rows={4}
  placeholder="Enter description"
/>
```

### Alert

```tsx
import { Alert } from '@/components/ui';

<Alert variant="info" title="Information">
  This is an informational message
</Alert>

<Alert variant="success" dismissible onDismiss={handleDismiss}>
  Operation completed successfully
</Alert>
```

### Table

```tsx
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui';

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead sortable onSort={handleSort}>
        Email
      </TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow onClick={handleRowClick}>
      <TableCell>John Doe</TableCell>
      <TableCell>john@example.com</TableCell>
      <TableCell>
        <Badge variant="success">Active</Badge>
      </TableCell>
    </TableRow>
  </TableBody>
</Table>
```

### Tabs

```tsx
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';

<Tabs defaultValue="tab1" onChange={handleTabChange}>
  <TabsList>
    <TabsTrigger value="tab1">Tab 1</TabsTrigger>
    <TabsTrigger value="tab2">Tab 2</TabsTrigger>
    <TabsTrigger value="tab3" disabled>Tab 3</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1">
    Content for tab 1
  </TabsContent>
  <TabsContent value="tab2">
    Content for tab 2
  </TabsContent>
</Tabs>
```

## Layout System

### Container

```tsx
import { Container } from '@/components/ui';

// Different sizes
<Container size="sm">Small container</Container>
<Container size="md">Medium container</Container>
<Container size="lg">Large container (default)</Container>
<Container size="xl">Extra large container</Container>
<Container size="full">Full width container</Container>
```

### Grid

```tsx
import { Grid, GridItem } from '@/components/ui';

// Responsive grid
<Grid cols={{ default: 1, md: 2, lg: 3 }} gap={4}>
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</Grid>

// Grid with spanning items
<Grid cols={{ default: 1, md: 2, lg: 3 }}>
  <GridItem colSpan={{ default: 1, md: 2 }}>
    Spanning item
  </GridItem>
  <div>Regular item</div>
</Grid>
```

### Dashboard Layout

```tsx
import DashboardLayout from '@/components/layout/DashboardLayout';

export default function Page() {
  return (
    <DashboardLayout>
      <h1>Page Title</h1>
      <p>Page content</p>
    </DashboardLayout>
  );
}
```

## Responsive Design

### Breakpoints

```typescript
// Tailwind breakpoints
sm: '640px'   // Small devices (tablets)
md: '768px'   // Medium devices (small laptops)
lg: '1024px'  // Large devices (desktops)
xl: '1280px'  // Extra large devices
2xl: '1536px' // 2X large devices
```

### Responsive Utilities

```tsx
// Width
<div className="w-full sm:w-1/2 lg:w-1/3">Responsive width</div>

// Display
<div className="block md:flex">Responsive display</div>

// Padding
<div className="p-4 sm:p-6 lg:p-8">Responsive padding</div>

// Text size
<h1 className="text-2xl sm:text-3xl lg:text-4xl">
  Responsive heading
</h1>

// Grid columns
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  Responsive grid
</div>
```

### Mobile-First Approach

Always design for mobile first, then add larger breakpoints:

```tsx
// ✅ Good - Mobile first
<div className="w-full md:w-1/2 lg:w-1/3">

// ❌ Bad - Desktop first
<div className="w-1/3 lg:w-1/2 md:w-full">
```

## Dark Mode

### Implementation

Dark mode is implemented using Tailwind's `dark:` variant and a ThemeContext:

```tsx
import { useTheme } from '@/contexts/ThemeContext';

function Component() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <button onClick={toggleTheme}>
      Toggle to {theme === 'light' ? 'dark' : 'light'} mode
    </button>
  );
}
```

### Dark Mode Classes

```tsx
// Background
<div className="bg-white dark:bg-gray-900">

// Text
<p className="text-gray-900 dark:text-white">

// Border
<div className="border-gray-200 dark:border-gray-700">

// Hover states
<button className="hover:bg-gray-100 dark:hover:bg-gray-800">
```

### Best Practices

1. Always provide dark mode variants for colors
2. Test components in both light and dark modes
3. Use semantic color names (primary, success, etc.) that work in both modes
4. Ensure sufficient contrast in both modes

## Accessibility

### WCAG 2.1 AA Compliance

The theme is designed to meet WCAG 2.1 AA standards:

#### Color Contrast

- Text: Minimum 4.5:1 contrast ratio
- Large text: Minimum 3:1 contrast ratio
- UI components: Minimum 3:1 contrast ratio

#### Keyboard Navigation

All interactive elements are keyboard accessible:

```tsx
// Focus styles
<button className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500">
  Accessible button
</button>
```

#### ARIA Labels

```tsx
// Buttons
<button aria-label="Close modal">
  <X className="w-5 h-5" />
</button>

// Form inputs
<Input
  label="Email"
  aria-describedby="email-helper"
  aria-invalid={hasError}
/>

// Modals
<Modal
  isOpen={isOpen}
  onClose={handleClose}
  aria-modal="true"
  aria-labelledby="modal-title"
>
```

#### Screen Reader Support

```tsx
// Hidden text for screen readers
<span className="sr-only">Loading...</span>

// ARIA live regions
<div role="alert" aria-live="polite">
  Success message
</div>
```

### Accessibility Checklist

- [ ] All images have alt text
- [ ] All form inputs have labels
- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicators are visible
- [ ] Color is not the only means of conveying information
- [ ] Sufficient color contrast
- [ ] Proper heading hierarchy
- [ ] ARIA labels for icon-only buttons
- [ ] Skip navigation links
- [ ] Semantic HTML elements

## Testing

### Unit Tests

```bash
# Run all tests
npm test

# Run UI component tests
npm run test:ui

# Run accessibility tests
npm run test:accessibility

# Run responsive design tests
npm run test:responsive

# Watch mode
npm run test:watch
```

### E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Test specific browser
npm run test:e2e:chromium
npm run test:e2e:firefox
npm run test:e2e:webkit

# Test mobile devices
npm run test:e2e:mobile
```

### Manual Testing Checklist

#### Responsive Design
- [ ] Test on mobile (320px - 767px)
- [ ] Test on tablet (768px - 1023px)
- [ ] Test on desktop (1024px+)
- [ ] Test landscape and portrait orientations

#### Cross-Browser
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

#### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader compatibility
- [ ] Focus indicators visible
- [ ] Color contrast sufficient
- [ ] ARIA labels present

#### Dark Mode
- [ ] All components render correctly
- [ ] Colors have sufficient contrast
- [ ] Images and icons are visible
- [ ] Transitions are smooth

## Best Practices

### Component Development

1. **Use semantic HTML**: Use appropriate HTML elements (`<button>`, `<nav>`, `<main>`, etc.)
2. **Provide ARIA labels**: Add aria-label, aria-describedby, and other ARIA attributes
3. **Support keyboard navigation**: Ensure all interactive elements are keyboard accessible
4. **Include focus styles**: Always provide visible focus indicators
5. **Test in both themes**: Verify components work in light and dark modes
6. **Make it responsive**: Design mobile-first and add larger breakpoints
7. **Write tests**: Include unit tests and accessibility tests

### Styling Guidelines

1. **Use Tailwind utilities**: Prefer Tailwind classes over custom CSS
2. **Follow naming conventions**: Use semantic color names (primary, success, etc.)
3. **Maintain consistency**: Use the same spacing, sizing, and color patterns
4. **Avoid magic numbers**: Use Tailwind's spacing scale (4, 6, 8, etc.)
5. **Group related classes**: Order classes logically (layout, spacing, colors, etc.)

### Performance

1. **Optimize images**: Use Next.js Image component
2. **Lazy load components**: Use dynamic imports for heavy components
3. **Minimize bundle size**: Tree-shake unused code
4. **Use CSS-in-JS sparingly**: Prefer Tailwind utilities
5. **Implement code splitting**: Split routes and components

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Playwright Documentation](https://playwright.dev/)
- [React Testing Library](https://testing-library.com/react)

## Support

For questions or issues related to the UI theme, please:

1. Check this documentation
2. Review existing components in `/src/components/ui`
3. Run tests to verify functionality
4. Consult the team for guidance
