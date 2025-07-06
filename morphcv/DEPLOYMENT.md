# MorphCV Deployment Guide

This guide explains how to deploy and configure the MorphCV application, which connects to the Flask backend API.

## Prerequisites

- Node.js 16+ and pnpm installed
- Backend API server (Flask) running and accessible
- Google OAuth credentials for authentication
- (Optional) Stripe account for payment processing

## Environment Configuration

The application uses environment variables for configuration. Create the following files:

### Development Environment (.env)

```
VITE_API_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_STRIPE_PUBLIC_KEY=your-stripe-public-key
```

### Production Environment (.env.production)

```
VITE_API_URL=/api/v1
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_STRIPE_PUBLIC_KEY=your-stripe-public-key
```

> **Note**: For production, the API URL is set to a relative path (`/api/v1`) assuming the frontend and backend are deployed together, with the backend serving the frontend static files.

## Setting Up Google OAuth

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or use an existing one
3. Navigate to "APIs & Services" > "Credentials"
4. Create an OAuth client ID for a Web Application
5. Add your authorized JavaScript origins (e.g., `https://yourdomain.com`)
6. Add your authorized redirect URIs (e.g., `https://yourdomain.com/login`)
7. Copy the Client ID and add it to your environment variables

## Setting Up Stripe (Optional)

1. Create a [Stripe account](https://stripe.com/)
2. Get your publishable key from the Stripe Dashboard
3. Add it to your environment variables
4. Configure webhook endpoints in your backend

## Build and Deployment

### Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Production Build

```bash
# Install dependencies
pnpm install

# Create production build
pnpm build
```

This will generate a `dist` directory with optimized static files.

## Deployment Options

### Option 1: Static Hosting with Separate Backend

Deploy the contents of the `dist` directory to any static hosting service (Netlify, Vercel, GitHub Pages, etc.).

Ensure your CORS settings on the backend allow requests from your frontend domain.

### Option 2: Backend-Served Frontend (Recommended)

1. Build the frontend
2. Copy the contents of the `dist` directory to your Flask backend's static files directory
3. Configure Flask to serve the frontend and handle all non-API routes by returning the `index.html` file

Example Flask route:
```python
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    # First, try to serve as a static file
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    
    # Otherwise, serve index.html for client-side routing
    return send_from_directory(app.static_folder, 'index.html')
```

## Troubleshooting

### API Connection Issues

- Check that the API URL is correctly set in your environment variables
- Verify CORS settings on the backend
- Inspect network requests in the browser console for errors

### Authentication Issues

- Verify Google Client ID is correct
- Check that authorized origins and redirect URIs are properly configured
- Test Google OAuth flow in development before deploying

### Subscription/Payment Issues

- Verify Stripe publishable key is correct
- Check webhook configuration on the backend
- Test payment flow with Stripe test mode before going live