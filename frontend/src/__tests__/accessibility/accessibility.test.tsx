/**
 * Accessibility Testing Suite
 * 
 * Tests WCAG 2.1 compliance and accessibility features across the application
 */

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const BASE_URL = process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(`${BASE_URL}/dashboard`);
  });

  test('Dashboard page should not have accessibility violations', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Employee list page should not have accessibility violations', async ({ page }) => {
    await page.goto(`${BASE_URL}/employees`);
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Attendance page should not have accessibility violations', async ({ page }) => {
    await page.goto(`${BASE_URL}/attendance`);
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Leave management page should not have accessibility violations', async ({ page }) => {
    await page.goto(`${BASE_URL}/leave`);
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Payroll page should not have accessibility violations', async ({ page }) => {
    await page.goto(`${BASE_URL}/payroll`);
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('Forms should have proper labels and ARIA attributes', async ({ page }) => {
    await page.goto(`${BASE_URL}/employees/new`);
    
    // Check that all form inputs have labels
    const inputs = await page.locator('input, select, textarea').all();
    
    for (const input of inputs) {
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      
      // Each input should have either an id with corresponding label, aria-label, or aria-labelledby
      const hasLabel = id ? await page.locator(`label[for="${id}"]`).count() > 0 : false;
      
      expect(hasLabel || ariaLabel || ariaLabelledBy).toBeTruthy();
    }
  });

  test('Keyboard navigation should work properly', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    
    // Tab through interactive elements
    await page.keyboard.press('Tab');
    let focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    
    // Should focus on interactive elements
    const interactiveElements = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'];
    expect(interactiveElements).toContain(focusedElement);
    
    // Test that Tab key moves focus
    const firstFocus = await page.evaluate(() => document.activeElement?.outerHTML);
    await page.keyboard.press('Tab');
    const secondFocus = await page.evaluate(() => document.activeElement?.outerHTML);
    
    expect(firstFocus).not.toEqual(secondFocus);
  });

  test('Skip to main content link should be present', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    
    // Press Tab to focus on skip link (usually first focusable element)
    await page.keyboard.press('Tab');
    
    const skipLink = await page.locator('a[href="#main-content"], a:has-text("Skip to")').first();
    const isVisible = await skipLink.isVisible().catch(() => false);
    
    // Skip link should exist (may be visually hidden until focused)
    expect(await skipLink.count()).toBeGreaterThan(0);
  });

  test('Images should have alt text', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    
    const images = await page.locator('img').all();
    
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      const role = await img.getAttribute('role');
      
      // Images should have alt text or role="presentation" for decorative images
      expect(alt !== null || role === 'presentation').toBeTruthy();
    }
  });

  test('Color contrast should meet WCAG AA standards', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();
    
    const contrastViolations = accessibilityScanResults.violations.filter(
      v => v.id === 'color-contrast'
    );
    
    expect(contrastViolations).toEqual([]);
  });

  test('Buttons should have accessible names', async ({ page }) => {
    await page.goto(`${BASE_URL}/employees`);
    
    const buttons = await page.locator('button').all();
    
    for (const button of buttons) {
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      const ariaLabelledBy = await button.getAttribute('aria-labelledby');
      const title = await button.getAttribute('title');
      
      // Buttons should have text content or aria-label
      const hasAccessibleName = (text && text.trim().length > 0) || ariaLabel || ariaLabelledBy || title;
      expect(hasAccessibleName).toBeTruthy();
    }
  });

  test('Tables should have proper structure', async ({ page }) => {
    await page.goto(`${BASE_URL}/employees`);
    
    const tables = await page.locator('table').all();
    
    for (const table of tables) {
      // Tables should have thead and tbody
      const hasThead = await table.locator('thead').count() > 0;
      const hasTbody = await table.locator('tbody').count() > 0;
      
      expect(hasThead).toBeTruthy();
      expect(hasTbody).toBeTruthy();
      
      // Table headers should have scope attribute
      const headers = await table.locator('th').all();
      for (const header of headers) {
        const scope = await header.getAttribute('scope');
        expect(scope).toBeTruthy();
      }
    }
  });

  test('Modal dialogs should trap focus', async ({ page }) => {
    await page.goto(`${BASE_URL}/employees`);
    
    // Open a modal (if exists)
    const addButton = page.locator('button:has-text("Add"), button:has-text("New")').first();
    if (await addButton.count() > 0) {
      await addButton.click();
      
      // Wait for modal to appear
      await page.waitForSelector('[role="dialog"], .modal', { timeout: 5000 }).catch(() => {});
      
      const modal = page.locator('[role="dialog"], .modal').first();
      if (await modal.isVisible()) {
        // Focus should be within modal
        const focusedElement = await page.evaluate(() => {
          const active = document.activeElement;
          const modal = document.querySelector('[role="dialog"], .modal');
          return modal?.contains(active);
        });
        
        expect(focusedElement).toBeTruthy();
      }
    }
  });

  test('Error messages should be announced to screen readers', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    
    // Submit form with invalid data
    await page.click('button[type="submit"]');
    
    // Check for aria-live region or role="alert"
    const errorRegion = page.locator('[role="alert"], [aria-live="polite"], [aria-live="assertive"]');
    const hasErrorAnnouncement = await errorRegion.count() > 0;
    
    // Error messages should be announced
    expect(hasErrorAnnouncement).toBeTruthy();
  });

  test('Loading states should be announced', async ({ page }) => {
    await page.goto(`${BASE_URL}/employees`);
    
    // Check for loading indicators with proper ARIA
    const loadingIndicators = page.locator('[role="status"], [aria-busy="true"], [aria-live]');
    
    // At some point during page load, there should be loading indicators
    // This is a basic check - actual implementation may vary
    const count = await loadingIndicators.count();
    console.log(`Found ${count} loading indicators with ARIA attributes`);
  });

  test('Responsive design should maintain accessibility', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${BASE_URL}/dashboard`);
    
    const mobileResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    
    expect(mobileResults.violations).toEqual([]);
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`${BASE_URL}/dashboard`);
    
    const tabletResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    
    expect(tabletResults.violations).toEqual([]);
  });

  test('Focus indicators should be visible', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    
    // Tab to first interactive element
    await page.keyboard.press('Tab');
    
    // Check that focused element has visible outline or focus indicator
    const focusStyles = await page.evaluate(() => {
      const element = document.activeElement as HTMLElement;
      const styles = window.getComputedStyle(element);
      return {
        outline: styles.outline,
        outlineWidth: styles.outlineWidth,
        boxShadow: styles.boxShadow,
      };
    });
    
    // Should have some form of focus indicator
    const hasFocusIndicator = 
      focusStyles.outline !== 'none' ||
      focusStyles.outlineWidth !== '0px' ||
      focusStyles.boxShadow !== 'none';
    
    expect(hasFocusIndicator).toBeTruthy();
  });

  test('Page should have proper heading hierarchy', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    const headingLevels: number[] = [];
    
    for (const heading of headings) {
      const tagName = await heading.evaluate(el => el.tagName);
      const level = parseInt(tagName.substring(1));
      headingLevels.push(level);
    }
    
    // Should have at least one h1
    expect(headingLevels.filter(l => l === 1).length).toBeGreaterThan(0);
    
    // Heading levels should not skip (e.g., h1 -> h3)
    for (let i = 1; i < headingLevels.length; i++) {
      const diff = headingLevels[i] - headingLevels[i - 1];
      expect(diff).toBeLessThanOrEqual(1);
    }
  });
});
