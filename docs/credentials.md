# Default Credentials

This document contains the default login credentials for the Neovance-AI system.

**Note: These are development credentials only. Change these for production deployment.**

## User Accounts

### Doctor Account
- **Username**: `DR001`
- **Password**: `password@dr`
- **Role**: Doctor
- **Permissions**: 
  - Full dashboard access
  - Can respond to sepsis alerts
  - View all patient data
  - Access Critical Action Panel

### Nurse Account
- **Username**: `NS001`
- **Password**: `password@ns`
- **Role**: Nurse
- **Permissions**:
  - Full dashboard access
  - Receive doctor notifications
  - View all patient data
  - Cannot respond to sepsis alerts directly

## Database Credentials

### PostgreSQL
- **Host**: `localhost` (or Docker container name: `postgres`)
- **Port**: `5432`
- **Database**: `neovance_hil`
- **Username**: `postgres`
- **Password**: `password`

## API Access

### Development API
- **Base URL**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs`
- **Authentication**: None (development only)

## Security Notes

1. **Change all credentials** before production deployment
2. **Implement proper authentication** (OAuth2/OIDC)
3. **Use environment variables** for sensitive data
4. **Enable SSL/TLS** for all communications
5. **Regular credential rotation** in production

## Production Setup

For production deployment:

1. Remove these default credentials
2. Implement proper user management system
3. Use secure password policies
4. Enable multi-factor authentication where appropriate
5. Follow HIPAA compliance guidelines for healthcare data