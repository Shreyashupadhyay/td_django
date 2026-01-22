# Truth & Dare - Render Deployment Guide

## Deployment Steps

### 1. Prepare Your Repository
Make sure all changes are committed and pushed to your Git repository (GitHub, GitLab, or Bitbucket).

### 2. Create a New Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** and select **"Web Service"**
3. Connect your Git repository
4. Configure the service:

   - **Name**: `truth-dare-game` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your primary branch)
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `daphne -b 0.0.0.0 -p $PORT truth_dare.asgi:application`

### 3. Add Environment Variables

In the Render dashboard, add these environment variables:

**Required:**
- `SECRET_KEY`: Generate a secure random string (e.g., use https://djecrety.ir/)
- `DATABASE_URL`: Render will auto-populate this when you add a PostgreSQL database
- `PYTHON_VERSION`: `3.11.0`

**Optional:**
- `DEBUG`: `False` (default, leave empty for production)
- `ALLOWED_HOSTS`: Your render domain (e.g., `truth-dare-game.onrender.com`)

### 4. Add PostgreSQL Database

1. In Render dashboard, click **"New +"** and select **"PostgreSQL"**
2. Configure:
   - **Name**: `truth-dare-db`
   - **Database**: `truth_dare`
   - **User**: `truth_dare_user`
   - **Region**: Same as your web service
   - **Plan**: Free or paid
3. Click **"Create Database"**
4. Once created, go to your Web Service settings
5. In Environment Variables, the `DATABASE_URL` will be automatically linked

### 5. Deploy

1. Click **"Create Web Service"**
2. Render will automatically:
   - Install dependencies
   - Run migrations
   - Collect static files
   - Start the server
3. Wait for deployment to complete (5-10 minutes for first deploy)

### 6. Create Superuser (Admin Account)

After deployment, you need to create an admin account:

**Option 1: Using Render Shell**
1. Go to your web service in Render dashboard
2. Click on **"Shell"** tab
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Follow the prompts to create your admin account

**Option 2: Modify build.sh (before deployment)**
Uncomment the superuser creation lines in `build.sh` and set your credentials.

## Post-Deployment

### Access Your Application
- Main site: `https://your-app-name.onrender.com/`
- Admin dashboard: `https://your-app-name.onrender.com/admin/dashboard/`
- Django admin: `https://your-app-name.onrender.com/admin/`
- Standalone page: `https://your-app-name.onrender.com/standalone/`

### Update ALLOWED_HOSTS
After deployment, add your Render domain to environment variables:
```
ALLOWED_HOSTS=your-app-name.onrender.com,localhost,127.0.0.1
```

## WebSocket Support

**Note:** Render's free tier doesn't support WebSocket connections reliably. The application will automatically fall back to polling, which works perfectly fine but may have a slight delay in real-time updates.

For full WebSocket support, consider:
- Upgrading to a paid Render plan
- Using Redis for channel layers (add Redis instance on Render)

## Troubleshooting

### Static Files Not Loading
1. Check if `collectstatic` ran successfully in build logs
2. Verify `STATIC_ROOT` and `STATIC_URL` in settings
3. Check WhiteNoise is in `MIDDLEWARE`

### Database Connection Issues
1. Verify `DATABASE_URL` is set correctly
2. Check database is in same region as web service
3. Ensure `psycopg2-binary` is in requirements.txt

### 500 Internal Server Error
1. Set `DEBUG=True` temporarily to see error details
2. Check deployment logs in Render dashboard
3. Verify all environment variables are set
4. Check migrations ran successfully

### Application Not Starting
1. Review build logs for errors
2. Check `build.sh` has execute permissions
3. Verify start command is correct
4. Ensure all dependencies installed successfully

## Monitoring

- **Logs**: View real-time logs in Render dashboard
- **Metrics**: Monitor CPU, memory, and request metrics
- **Health Checks**: Render automatically checks `https://your-app.onrender.com/`

## Free Tier Limitations

Render's free tier includes:
- ✅ 750 hours/month web service
- ✅ Automatic SSL certificates
- ✅ PostgreSQL database (90 days, then deleted if inactive)
- ⚠️ Service spins down after 15 min of inactivity (first request may be slow)
- ⚠️ Limited WebSocket support

## Updating Your App

To deploy updates:
1. Push changes to your Git repository
2. Render automatically detects changes and redeploys
3. Or manually trigger deploy from Render dashboard

## Custom Domain (Optional)

1. Go to your web service settings
2. Click **"Custom Domains"**
3. Add your domain
4. Update DNS records as instructed
5. SSL certificate will be automatically provisioned

---

**Need Help?** Check [Render Documentation](https://render.com/docs) or [Django Deployment Guide](https://docs.djangoproject.com/en/4.2/howto/deployment/)
