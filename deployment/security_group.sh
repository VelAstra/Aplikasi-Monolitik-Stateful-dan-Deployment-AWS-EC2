#!/bin/bash

# AWS Security Group Setup Script
# Run this script to configure security group rules for the Aplikasi Monolitik

echo "AWS EC2 Security Group Setup"
echo "============================"
echo ""
echo "Prerequisites:"
echo "1. AWS CLI installed and configured"
echo "2. Security group ID available"
echo ""

read -p "Enter your Security Group ID: " SG_ID
read -p "Enter your local IP (for SSH access, e.g., 203.0.113.0/32): " LOCAL_IP

if [ -z "$SG_ID" ] || [ -z "$LOCAL_IP" ]; then
    echo "Error: Security Group ID and Local IP are required"
    exit 1
fi

echo ""
echo "Adding inbound rules to security group: $SG_ID"
echo ""

# SSH access
echo "1. Adding SSH rule (port 22)..."
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr $LOCAL_IP \
    2>/dev/null || echo "   SSH rule may already exist"

# HTTP access
echo "2. Adding HTTP rule (port 80)..."
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    2>/dev/null || echo "   HTTP rule may already exist"

# HTTPS access
echo "3. Adding HTTPS rule (port 443)..."
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    2>/dev/null || echo "   HTTPS rule may already exist"

echo ""
echo "Security group rules added successfully!"
echo ""
echo "Summary:"
echo "- SSH (22): Open to $LOCAL_IP"
echo "- HTTP (80): Open to 0.0.0.0/0"
echo "- HTTPS (443): Open to 0.0.0.0/0"
echo ""
