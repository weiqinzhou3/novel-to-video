# SVD Service Troubleshooting Guide

## Common Issues and Solutions

### 1. Service Hangs/Freezes

**Symptoms:**
- Service appears to be running but doesn't respond
- Tasks stuck in processing state
- Empty outputs folder despite completed tasks

**Solutions:**

#### Quick Fix:
1. Run `restart_svd_service.bat`
2. This will automatically:
   - Kill hanging processes
   - Check dependencies
   - Restart the service

#### Manual Fix:
1. Open Task Manager (Ctrl+Shift+Esc)
2. End all `python.exe` processes related to SVD
3. Check if port 7860 is still in use:
   ```cmd
   netstat -ano | findstr :7860
   ```
4. Kill any processes using port 7860:
   ```cmd
   taskkill /f /pid [PID_NUMBER]
   ```
5. Restart the service

### 2. Video Export Issues (Empty Outputs Folder)

**Root Cause:** Missing video processing dependencies

**Solution:**
1. Run `install_video_deps_en.bat`
2. Wait for installation to complete
3. Restart the service using `restart_svd_service.bat`

**Manual Installation:**
```cmd
svd_env\Scripts\activate.bat
pip install imageio>=2.31.0 imageio-ffmpeg>=0.4.9
```

### 3. Batch Script Flash/Exit Issues

**Common Causes:**
- Virtual environment not found
- Python not properly installed
- Permission issues

**Solutions:**

#### For install_video_deps.bat flashing:
1. Use the English version: `install_video_deps_en.bat`
2. Run as Administrator if needed
3. Check if `svd_env` folder exists

#### Debug Mode:
1. Open Command Prompt as Administrator
2. Navigate to the deployment folder:
   ```cmd
   cd /d "d:\novel-to-video\windows_deployment"
   ```
3. Run commands manually:
   ```cmd
   svd_env\Scripts\activate.bat
   pip install imageio imageio-ffmpeg
   ```

### 4. Service Won't Start

**Check List:**
1. **Virtual Environment:**
   ```cmd
   svd_env\Scripts\activate.bat
   python --version
   ```

2. **Dependencies:**
   ```cmd
   pip list | findstr torch
   pip list | findstr diffusers
   pip list | findstr imageio
   ```

3. **Port Availability:**
   ```cmd
   netstat -ano | findstr :7860
   ```

4. **Firewall:**
   - Run `setup_firewall.bat` as Administrator
   - Or manually allow Python through Windows Firewall

### 5. Memory Issues

**Symptoms:**
- Service crashes during video generation
- "Out of memory" errors

**Solutions:**
1. **Reduce Model Precision:**
   - Edit `config.json`
   - Set `"torch_dtype": "float16"`

2. **Enable Memory Optimizations:**
   ```json
   {
     "model": {
       "enable_attention_slicing": true,
       "enable_cpu_offload": true
     }
   }
   ```

3. **Close Other Applications:**
   - Free up system RAM
   - Close unnecessary browser tabs

### 6. Network/API Issues

**Symptoms:**
- Can't access http://localhost:7860
- Connection refused errors

**Solutions:**
1. **Check Service Status:**
   ```cmd
   curl http://localhost:7860/health
   ```

2. **Firewall Configuration:**
   - Run `setup_firewall.bat` as Administrator
   - Manually add exception for port 7860

3. **Alternative Ports:**
   - Edit `config.json` to use different port
   - Update firewall rules accordingly

## Diagnostic Commands

### System Information
```cmd
# Check Python version
svd_env\Scripts\python --version

# Check GPU availability
svd_env\Scripts\python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Check disk space
dir outputs

# Check memory usage
tasklist /fi "imagename eq python.exe"
```

### Service Health Check
```cmd
# Test basic connectivity
curl http://localhost:7860/health

# Test task listing
curl http://localhost:7860/tasks

# Check service logs (if available)
type logs\svd_server.log
```

## Prevention Tips

1. **Regular Maintenance:**
   - Restart service daily if running continuously
   - Clear outputs folder periodically
   - Monitor system resources

2. **Proper Shutdown:**
   - Use Ctrl+C to stop service gracefully
   - Don't force-kill unless necessary

3. **Resource Management:**
   - Don't run multiple video generation tasks simultaneously
   - Monitor GPU memory usage
   - Ensure adequate disk space

## Getting Help

If issues persist:

1. **Collect Information:**
   - Error messages from service window
   - System specifications (RAM, GPU)
   - Python and dependency versions

2. **Check Logs:**
   - Service console output
   - Windows Event Viewer
   - Task Manager for resource usage

3. **Test Environment:**
   - Run `test_video_export.py` for diagnostics
   - Verify all dependencies are installed
   - Test with minimal configuration

## Quick Reference

| Issue | Solution |
|-------|----------|
| Service hangs | `restart_svd_service.bat` |
| Empty outputs | `install_video_deps_en.bat` |
| Script flashing | Run as Administrator |
| Port in use | Kill process or change port |
| Memory errors | Enable optimizations in config |
| Can't connect | Check firewall settings |