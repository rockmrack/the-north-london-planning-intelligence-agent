# Vercel Deployment Setup Guide

## 🚨 CRITICAL: Fix for 404 Error

Your 404 error is happening because Vercel doesn't know your Next.js app is in the `frontend/` directory.

### ✅ THE ONLY SOLUTION: Dashboard Configuration

**You MUST set the Root Directory in Vercel Dashboard. There is no other way to make this work with the current project structure.**

#### Step-by-Step Instructions:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project (or import it if you haven't)
3. Click **Settings** → **General**
4. Scroll down to **Root Directory**
5. Click **Edit** button
6. Enter: `frontend` (no slashes, just the word "frontend")
7. Click **Save**
8. Go to **Deployments** tab
9. Click the **⋯** menu on the latest deployment
10. Click **Redeploy**

**Screenshot reference:**
```
Root Directory: [Edit]
               ↓
Root Directory: [frontend] [Save] [Cancel]
```

### Why vercel.json Doesn't Work

The `vercel.json` file in this repo is minimal because:
- You **cannot** use `cd` commands in Vercel's build/install commands
- Build commands run in isolated contexts that don't preserve directory changes
- The proper way to handle monorepos is via the Root Directory setting

The error you're seeing (`sh: line 1: cd: frontend: No such file or directory`) confirms this.

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
