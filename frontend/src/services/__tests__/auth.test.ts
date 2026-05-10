import { authService } from '../auth';

// Mock the API client
jest.mock('@/lib/api', () => ({
  __esModule: true,
  default: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

import apiClient from '@/lib/api';

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('AuthService', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    localStorageMock.clear.mockClear();
  });

  describe('login', () => {
    it('should login successfully and store tokens', async () => {
      const mockResponse = {
        data: {
          access: 'mock-access-token',
          refresh: 'mock-refresh-token',
          user: {
            id: '1',
            username: 'testuser',
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User',
            company: { id: '1', name: 'Test Company', code: 'TEST' },
            role: { id: '1', name: 'Admin', permissions: [] },
          },
        },
      };

      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await authService.login({
        username: 'testuser',
        password: 'password123',
      });

      expect(result).toEqual(mockResponse.data);
      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/login/', {
        username: 'testuser',
        password: 'password123',
      });
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'mock-access-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('refresh_token', 'mock-refresh-token');
    });

    it('should throw error on invalid credentials', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Invalid credentials'));

      await expect(
        authService.login({ username: 'testuser', password: 'wrongpassword' })
      ).rejects.toThrow('Invalid credentials');
    });
  });

  describe('logout', () => {
    it('should logout successfully and clear tokens', async () => {
      mockApiClient.post.mockResolvedValue({ status: 205 });

      await authService.logout();

      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/logout/');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });

    it('should clear tokens even if logout request fails', async () => {
      mockApiClient.post.mockRejectedValue(new Error('Server error'));

      // Should not throw error - errors are caught and logged
      await authService.logout();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      localStorageMock.getItem.mockReturnValue('mock-refresh-token');
      const mockResponse = { data: { access: 'new-access-token' } };
      mockApiClient.post.mockResolvedValue(mockResponse);

      const result = await authService.refreshToken();

      expect(result).toBe('new-access-token');
      expect(mockApiClient.post).toHaveBeenCalledWith('/auth/refresh/', {
        refresh: 'mock-refresh-token',
      });
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'new-access-token');
    });

    it('should throw error when no refresh token available', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      await expect(authService.refreshToken()).rejects.toThrow('No refresh token available');
    });
  });

  describe('getCurrentUser', () => {
    it('should get current user successfully', async () => {
      const mockUser = {
        id: '1',
        username: 'testuser',
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
        company: { id: '1', name: 'Test Company', code: 'TEST' },
        role: { id: '1', name: 'Admin', permissions: [] },
      };

      mockApiClient.get.mockResolvedValue({ data: mockUser });

      const result = await authService.getCurrentUser();

      expect(result).toEqual(mockUser);
      expect(mockApiClient.get).toHaveBeenCalledWith('/auth/profile/');
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when access token exists', () => {
      localStorageMock.getItem.mockReturnValue('mock-access-token');

      const result = authService.isAuthenticated();

      expect(result).toBe(true);
    });

    it('should return false when no access token exists', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const result = authService.isAuthenticated();

      expect(result).toBe(false);
    });
  });
});