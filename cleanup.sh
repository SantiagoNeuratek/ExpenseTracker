#!/bin/bash

# Clean up script for after successful deployment
echo "Cleaning up unnecessary deployment files..."

# Remove temporary deployment files
rm -f expense-tracker-deploy-v*.zip
rm -f deployment.zip
rm -f AWSCLIV2.pkg

# Move EB deployment files to eb-deploy directory for reference
mkdir -p eb-deploy/latest
cp docker-compose.yml eb-deploy/latest/
cp Dockerrun.aws.json eb-deploy/latest/
cp -r .ebextensions eb-deploy/latest/

echo "Cleanup complete! Your successful deployment files have been backed up to eb-deploy/latest/"
echo "Use docker-compose-local.yml for local development with: docker-compose -f docker-compose-local.yml up" 