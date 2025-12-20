# Vercel Deployment Setup Guide

## Quick Fix for 404 Error

Your 404 error is happening because Vercel doesn't know your Next.js app is in the `frontend/` directory.

### Solution 1: Dashboard Configuration (Easiest)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Click **Settings** → **General**
4. Scroll to **Root Directory**
5. Click **Edit**
6. Enter: `frontend`
7. Click **Save**
8. Go to **Deployments** tab
9. Click the **⋯** menu on latest deployment → **Redeploy**

✅ **This is the recommended approach** - it's cleaner and doesn't require config files.

### Solution 2: Using vercel.json (Alternative)

The `vercel.json` file in the root handles this automatically by telling Vercel:
- Where to run the build (`cd frontend && npm run build`)
- Where the output is (`frontend/.next`)
- How to install dependencies (`cd frontend && npm install`)

If you use this approach, you don't need to set Root Directory in the dashboard.

## Why Did This Happen?

### Root Cause
Your project is a **monorepo** with this structure:
```
/
├── backend/          (Python FastAPI)
├── frontend/         (Next.js app) ← Your app is HERE
│   ├── src/
│   ├── package.json
│   └── next.config.js
└── (other dirs)
```

**Without configuration**, Vercel looks in the root directory for a Next.js app and finds nothing, resulting in a 404.

### The Mental Model

Think of Vercel deployment in 3 steps:
1. **Detection**: "Where is the app?" (needs Root Directory or vercel.json)
2. **Build**: "How do I build it?" (runs `npm run build`)
3. **Serve**: "Where is the output?" (looks for `.next` directory)

For monorepos, step 1 fails without explicit configuration.

## Environment Variables

After fixing the 404, you'll need to configure:

### Required
- `NEXT_PUBLIC_API_URL` - Your backend API URL

### Optional
- `NEXT_PUBLIC_ENV=production`
- `NEXT_PUBLIC_ENABLE_ANALYTICS=true`

Set these in: **Vercel Dashboard** → **Settings** → **Environment Variables**

## Testing Your Fix

After deployment:
1. Visit your Vercel URL (e.g., `https://your-project.vercel.app`)
2. You should see your homepage, not a 404
3. Check the browser console for any API errors
4. Test the chat widget functionality

## Common Issues

### Still getting 404?
- Verify Root Directory is set to `frontend` (no trailing slash)
- Check deployment logs for build errors
- Ensure the build completed successfully

### Build succeeds but page is blank?
- Check browser console for JavaScript errors
- Verify environment variables are set
- Check that `NEXT_PUBLIC_API_URL` is correct

### API not working?
- Set `NEXT_PUBLIC_API_URL` to your backend URL
- Ensure your backend allows CORS from your Vercel domain
- Check backend logs for errors

## Additional Resources

- [Vercel Monorepo Documentation](https://vercel.com/docs/monorepos)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- Main deployment guide: [DEPLOYMENT.md](./DEPLOYMENT.md)
