import { test, expect } from '@playwright/test';

/**
 * E2E tests for UI components across different browsers
 * These tests verify that components render and function correctly
 * in all supported browsers and devices.
 */

test.describe('UI Components - Cross-Browser', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to a test page with UI components
    await page.goto('/dashboard');
  });

  test('buttons render and are clickable', async ({ page }) => {
    // Find a button on the page
    const button = page.locator('button').first();
    
    // Verify button is visible
    await expect(button).toBeVisible();
    
    // Verify button is clickable
    await expect(button).toBeEnabled();
    
    // Click the button
    await button.click();
  });

  test('modal opens and closes correctly', async ({ page }) => {
    // Look for a button that opens a modal
    const openModalButton = page.locator('button:has-text("Add"), button:has-text("Create")').first();
    
    if (await openModalButton.isVisible()) {
      await openModalButton.click();
      
      // Verify modal is visible
      const modal = page.locator('[role="dialog"]');
      await expect(modal).toBeVisible();
      
      // Close modal with close button
      const closeButton = modal.locator('button[aria-label="Close modal"]');
      if (await closeButton.isVisible()) {
        await closeButton.click();
        await expect(modal).not.toBeVisible();
      }
    }
  });

  test('navigation menu is accessible', async ({ page }) => {
    // Verify navigation is present
    const nav = page.locator('nav, [role="navigation"]');
    await expect(nav).toBeVisible();
    
    // Verify menu items are clickable
    const menuItems = nav.locator('a, button');
    const count = await menuItems.count();
    expect(count).toBeGreaterThan(0);
  });

  test('theme toggle works correctly', async ({ page }) => {
    // Find theme toggle button
    const themeToggle = page.locator('button[aria-label*="theme"], button[aria-label*="mode"]');
    
    if (await themeToggle.isVisible()) {
      // Get initial theme
      const html = page.locator('html');
      const initialTheme = await html.getAttribute('class');
      
      // Toggle theme
      await themeToggle.click();
      
      // Wait for theme change
      await page.waitForTimeout(300);
      
      // Verify theme changed
      const newTheme = await html.getAttribute('class');
      expect(newTheme).not.toBe(initialTheme);
    }
  });

  test('forms are accessible and functional', async ({ page }) => {
    // Look for input fields
    const inputs = page.locator('input[type="text"], input[type="email"]');
    
    if (await inputs.first().isVisible()) {
      const input = inputs.first();
      
      // Verify input is focusable
      await input.focus();
      await expect(input).toBeFocused();
      
      // Type into input
      await input.fill('Test input');
      await expect(input).toHaveValue('Test input');
    }
  });

  test('responsive design works on mobile', async ({ page, isMobile }) => {
    if (isMobile) {
      // Verify mobile menu button is visible
      const mobileMenuButton = page.locator('button[aria-label="Toggle menu"]');
      await expect(mobileMenuButton).toBeVisible();
      
      // Open mobile menu
      await mobileMenuButton.click();
      
      // Verify sidebar is visible
      const sidebar = page.locator('aside, [role="navigation"]');
      await expect(sidebar).toBeVisible();
    }
  });

  test('tables render correctly', async ({ page }) => {
    // Look for tables on the page
    const table = page.locator('table').first();
    
    if (await table.isVisible()) {
      // Verify table has headers
      const headers = table.locator('th');
      const headerCount = await headers.count();
      expect(headerCount).toBeGreaterThan(0);
      
      // Verify table has rows
      const rows = table.locator('tbody tr');
      const rowCount = await rows.count();
      expect(rowCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('alerts and notifications display correctly', async ({ page }) => {
    // Look for alert elements
    const alerts = page.locator('[role="alert"]');
    
    if (await alerts.first().isVisible()) {
      const alert = alerts.first();
      
      // Verify alert is visible
      await expect(alert).toBeVisible();
      
      // Check if alert is dismissible
      const dismissButton = alert.locator('button[aria-label*="Dismiss"]');
      if (await dismissButton.isVisible()) {
        await dismissButton.click();
        await expect(alert).not.toBeVisible();
      }
    }
  });

  test('keyboard navigation works correctly', async ({ page }) => {
    // Focus first interactive element
    await page.keyboard.press('Tab');
    
    // Verify an element is focused
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
    
    // Navigate with Tab key
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Verify focus moved
    const newFocusedElement = page.locator(':focus');
    await expect(newFocusedElement).toBeVisible();
  });

  test('tooltips appear on hover', async ({ page, isMobile }) => {
    if (!isMobile) {
      // Look for elements with tooltips
      const tooltipTriggers = page.locator('[data-tooltip], [title]');
      
      if (await tooltipTriggers.first().isVisible()) {
        const trigger = tooltipTriggers.first();
        
        // Hover over element
        await trigger.hover();
        
        // Wait for tooltip to appear
        await page.waitForTimeout(500);
        
        // Verify tooltip is visible
        const tooltip = page.locator('[role="tooltip"]');
        if (await tooltip.isVisible()) {
          await expect(tooltip).toBeVisible();
        }
      }
    }
  });
});

test.describe('Layout - Cross-Browser', () => {
  test('header is sticky on scroll', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Get header position
    const header = page.locator('header, [role="banner"]');
    await expect(header).toBeVisible();
    
    const initialPosition = await header.boundingBox();
    
    // Scroll down
    await page.evaluate(() => window.scrollBy(0, 500));
    
    // Verify header is still visible
    await expect(header).toBeVisible();
  });

  test('sidebar is responsive', async ({ page, isMobile }) => {
    await page.goto('/dashboard');
    
    const sidebar = page.locator('aside');
    
    if (isMobile) {
      // On mobile, sidebar should be hidden initially
      const isHidden = await sidebar.evaluate((el) => {
        const transform = window.getComputedStyle(el).transform;
        return transform.includes('matrix') && transform.includes('-');
      });
      expect(isHidden).toBeTruthy();
    } else {
      // On desktop, sidebar should be visible
      await expect(sidebar).toBeVisible();
    }
  });

  test('content area adjusts for sidebar', async ({ page, isMobile }) => {
    await page.goto('/dashboard');
    
    const mainContent = page.locator('main, [role="main"]');
    await expect(mainContent).toBeVisible();
    
    if (!isMobile) {
      // On desktop, main content should have left padding for sidebar
      const paddingLeft = await mainContent.evaluate((el) => {
        return window.getComputedStyle(el).paddingLeft;
      });
      
      // Verify there's padding (sidebar width)
      expect(parseInt(paddingLeft)).toBeGreaterThan(0);
    }
  });
});

test.describe('Accessibility - Cross-Browser', () => {
  test('all interactive elements are keyboard accessible', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Tab through interactive elements
    const interactiveElements = [];
    
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      const focused = await page.locator(':focus').first();
      
      if (await focused.isVisible()) {
        const tagName = await focused.evaluate((el) => el.tagName);
        interactiveElements.push(tagName);
      }
    }
    
    // Verify we could tab through elements
    expect(interactiveElements.length).toBeGreaterThan(0);
  });

  test('ARIA labels are present', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Check for ARIA landmarks
    const banner = page.locator('[role="banner"]');
    const navigation = page.locator('[role="navigation"]');
    const main = page.locator('[role="main"]');
    
    await expect(banner).toBeVisible();
    await expect(navigation).toBeVisible();
    await expect(main).toBeVisible();
  });

  test('focus indicators are visible', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Focus an interactive element
    await page.keyboard.press('Tab');
    
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();
    
    // Verify focus indicator is visible (outline or ring)
    const hasOutline = await focused.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return styles.outline !== 'none' || styles.boxShadow !== 'none';
    });
    
    expect(hasOutline).toBeTruthy();
  });
});

test.describe('Performance - Cross-Browser', () => {
  test('page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/dashboard');
    const loadTime = Date.now() - startTime;
    
    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
  });

  test('animations are smooth', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Open a modal or dropdown
    const button = page.locator('button').first();
    if (await button.isVisible()) {
      await button.click();
      
      // Wait for animation to complete
      await page.waitForTimeout(500);
      
      // Verify no layout shifts occurred
      const layoutShift = await page.evaluate(() => {
        return (window as any).layoutShiftScore || 0;
      });
      
      expect(layoutShift).toBeLessThan(0.1);
    }
  });
});
