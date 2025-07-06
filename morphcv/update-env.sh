#!/bin/bash

# This script updates the environment variables in .env files
# Usage: ./update-env.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}MorphCV Environment Configuration${NC}"
echo "======================================"
echo ""

# Function to update environment variable
update_env_var() {
  local env_file=$1
  local var_name=$2
  local current_value=$(grep -E "^$var_name=" $env_file 2>/dev/null | cut -d '=' -f2)
  
  echo -e "Setting ${YELLOW}$var_name${NC} for $env_file"
  echo -e "Current value: ${GREEN}$current_value${NC}"
  echo -n "Enter new value (leave empty to keep current): "
  read new_value
  
  if [ -n "$new_value" ]; then
    if grep -q "^$var_name=" $env_file 2>/dev/null; then
      # Update existing variable
      sed -i "s|^$var_name=.*|$var_name=$new_value|" $env_file
    else
      # Add new variable
      echo "$var_name=$new_value" >> $env_file
    fi
    echo -e "${GREEN}Updated $var_name in $env_file${NC}"
  else
    echo -e "${YELLOW}Keeping current value for $var_name${NC}"
  fi
  echo ""
}

# Create .env files if they don't exist
touch .env
touch .env.production

# Update variables for .env (development)
echo "Development Environment (.env)"
echo "------------------------------------"
update_env_var .env "VITE_API_URL"
update_env_var .env "VITE_GOOGLE_CLIENT_ID"
update_env_var .env "VITE_STRIPE_PUBLIC_KEY"
echo ""

# Update variables for .env.production
echo "Production Environment (.env.production)"
echo "------------------------------------"
update_env_var .env.production "VITE_API_URL"
update_env_var .env.production "VITE_GOOGLE_CLIENT_ID"
update_env_var .env.production "VITE_STRIPE_PUBLIC_KEY"
echo ""

echo -e "${GREEN}Environment configuration updated successfully!${NC}"
echo ""
echo -e "${YELLOW}Remember to:${NC}"
echo "1. Restart your development server if it's running"
echo "2. Rebuild and redeploy for production changes to take effect"
echo ""