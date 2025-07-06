# MorphCV Integration Test Plan

This document outlines the comprehensive test plan for verifying the integration between the React frontend and Flask backend.

## 1. Authentication Tests

### 1.1 Google OAuth Flow
- **Test:** Click "Continue with Google" button on login page
- **Expected:** Redirects to Google OAuth consent screen
- **Verification:** After successful authentication, redirects to main app with authenticated state

### 1.2 JWT Token Handling
- **Test:** Check that authenticated API requests include Authorization header
- **Expected:** All requests after login include Bearer token
- **Verification:** Use browser network tab to verify headers

### 1.3 Token Refresh
- **Test:** Simulate expired access token (can be tested by modifying token expiry)
- **Expected:** System automatically refreshes token without user intervention
- **Verification:** No session interruption, successful API calls continue

### 1.4 Logout
- **Test:** Click logout button
- **Expected:** Clears tokens, redirects to login page
- **Verification:** Protected routes are no longer accessible

## 2. CV Generation Tests

### 2.1 CV Creation
- **Test:** Fill form with CV information and click Generate
- **Expected:** Creates CV generation request, shows status tracker
- **Verification:** Backend receives correct data, job is created

### 2.2 Status Tracking
- **Test:** Monitor status updates during CV generation
- **Expected:** Status updates in real-time showing progress
- **Verification:** Status changes from "Processing" to "Completed"

### 2.3 Template Selection
- **Test:** Select different templates before generating CV
- **Expected:** Template selection is sent to backend
- **Verification:** Generated CV uses selected template

### 2.4 CV Preview
- **Test:** After generation, view CV preview
- **Expected:** Displays generated CV content
- **Verification:** Content matches input data

## 3. CV Management Tests

### 3.1 CV Listing
- **Test:** Navigate to CV list page
- **Expected:** Shows list of user's CVs with pagination
- **Verification:** Correct CVs are displayed with metadata

### 3.2 CV Editing
- **Test:** Edit an existing CV
- **Expected:** Updates CV on backend, refreshes view
- **Verification:** Changes are persisted and visible on refresh

### 3.3 CV Deletion
- **Test:** Delete a CV
- **Expected:** Removes CV from list
- **Verification:** CV no longer appears in list

### 3.4 CV Download
- **Test:** Download a CV
- **Expected:** Downloads PDF file
- **Verification:** File contains correct CV content

## 4. Subscription Tests

### 4.1 Subscription Status
- **Test:** View subscription page
- **Expected:** Shows current subscription status
- **Verification:** Status matches backend data

### 4.2 Pricing Display
- **Test:** Check available subscription plans
- **Expected:** Shows prices from backend
- **Verification:** Prices match backend configuration

### 4.3 Checkout Flow
- **Test:** Click subscribe button
- **Expected:** Redirects to Stripe checkout
- **Verification:** Checkout includes correct products/prices

### 4.4 Subscription Management
- **Test:** Access customer portal
- **Expected:** Redirects to Stripe customer portal
- **Verification:** Can manage subscription settings

## 5. Error Handling Tests

### 5.1 Network Errors
- **Test:** Disconnect internet during operation
- **Expected:** Shows network error message
- **Verification:** Error is displayed in user-friendly manner

### 5.2 Server Errors
- **Test:** Trigger 500 error from backend
- **Expected:** Shows appropriate error message
- **Verification:** Error handling components activate

### 5.3 Validation Errors
- **Test:** Submit invalid data
- **Expected:** Shows validation errors
- **Verification:** Form highlights errors correctly

## 6. Performance Tests

### 6.1 Page Load Time
- **Test:** Measure initial page load time
- **Expected:** Under 3 seconds on standard connection
- **Verification:** Use browser performance tools

### 6.2 API Response Handling
- **Test:** Monitor UI during slow API responses
- **Expected:** Shows loading states appropriately
- **Verification:** UI remains responsive, gives feedback

## 7. Security Tests

### 7.1 Protected Routes
- **Test:** Access protected routes without authentication
- **Expected:** Redirects to login page
- **Verification:** Cannot access protected content

### 7.2 Token Storage
- **Test:** Check where tokens are stored
- **Expected:** Tokens stored securely (not localStorage)
- **Verification:** Check storage mechanisms

### 7.3 CSRF Protection
- **Test:** Verify CSRF protection measures
- **Expected:** API requests include CSRF protection
- **Verification:** Headers include appropriate tokens

## Test Execution Checklist

- [ ] Authentication Tests (1.1-1.4)
- [ ] CV Generation Tests (2.1-2.4)
- [ ] CV Management Tests (3.1-3.4)
- [ ] Subscription Tests (4.1-4.4)
- [ ] Error Handling Tests (5.1-5.3)
- [ ] Performance Tests (6.1-6.2)
- [ ] Security Tests (7.1-7.3)

## Test Environment Setup

1. Start backend API server
2. Configure environment variables
3. Start frontend development server
4. Prepare test user accounts
5. Configure test payment methods in Stripe test mode

## Notes for Testers

- Always use Stripe test mode for payment testing
- Use different browsers to test cross-browser compatibility
- Test on both desktop and mobile devices
- Document any issues with screenshots and steps to reproduce