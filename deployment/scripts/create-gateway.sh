#!/bin/bash
#
# Register MCP Servers with Amazon Bedrock AgentCore Gateway
#
# Prerequisites:
# - AWS CLI v2 configured with appropriate permissions
# - MCP servers deployed and healthy (run deploy.sh for each service first)
#
# Usage:
#   ./create-gateway.sh <service-name> <alb-dns>
#
# Examples:
#   ./create-gateway.sh materials-supplier-mcp materials-supplier-mcp-alb-123456.us-east-1.elb.amazonaws.com
#   ./create-gateway.sh permitting-service-mcp permitting-service-mcp-alb-789012.us-east-1.elb.amazonaws.com
#
# Environment variables (optional):
#   AWS_REGION - AWS region (default: us-east-1)
#   AWS_PROFILE - AWS CLI profile to use
#

set -euo pipefail

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: ./create-gateway.sh <service-name> <alb-dns>"
    echo ""
    echo "Examples:"
    echo "  ./create-gateway.sh materials-supplier-mcp materials-supplier-mcp-alb-123456.us-east-1.elb.amazonaws.com"
    echo "  ./create-gateway.sh permitting-service-mcp permitting-service-mcp-alb-789012.us-east-1.elb.amazonaws.com"
    exit 1
fi

SERVICE_NAME="$1"
ALB_DNS="$2"
GATEWAY_NAME="${SERVICE_NAME}-gateway"
MCP_ENDPOINT="http://${ALB_DNS}/mcp"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

log_info "Registering AgentCore Gateway"
log_info "Service: ${SERVICE_NAME}"
log_info "Gateway Name: ${GATEWAY_NAME}"
log_info "MCP Endpoint: ${MCP_ENDPOINT}"
log_info "AWS Region: ${AWS_REGION}"

# =============================================================================
# Step 1: Create IAM Role for AgentCore Gateway
# =============================================================================
log_info "Creating IAM role for AgentCore Gateway..."

GATEWAY_ROLE_NAME="${SERVICE_NAME}-gateway-role"

# Create trust policy for AgentCore
aws iam create-role \
    --role-name "${GATEWAY_ROLE_NAME}" \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "bedrock.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
            "Condition": {
                "StringEquals": {
                    "aws:SourceAccount": "'"${AWS_ACCOUNT_ID}"'"
                }
            }
        }]
    }' 2>/dev/null || log_warn "Gateway role already exists"

# Attach policy for invoking the MCP endpoint
aws iam put-role-policy \
    --role-name "${GATEWAY_ROLE_NAME}" \
    --policy-name "MCPEndpointAccess" \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "elasticloadbalancing:DescribeLoadBalancers",
                "elasticloadbalancing:DescribeTargetGroups",
                "elasticloadbalancing:DescribeTargetHealth"
            ],
            "Resource": "*"
        }]
    }' 2>/dev/null || true

GATEWAY_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${GATEWAY_ROLE_NAME}"
log_info "Gateway Role ARN: ${GATEWAY_ROLE_ARN}"

# =============================================================================
# Step 2: Verify MCP Server Health
# =============================================================================
log_info "Verifying MCP server health..."

HEALTH_URL="http://${ALB_DNS}/health"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" != "200" ]; then
    log_error "MCP server is not healthy (HTTP ${HTTP_CODE})"
    log_error "Please ensure the service is deployed and healthy before creating the gateway"
    log_error "Check: ${HEALTH_URL}"
    exit 1
fi

log_info "MCP server is healthy"

# =============================================================================
# Step 3: Create AgentCore Gateway
# =============================================================================
log_info "Creating AgentCore Gateway..."

# Note: The exact API may vary based on AWS SDK version and AgentCore GA release
# This uses the bedrock-agent-runtime API pattern

# Create the gateway configuration file
GATEWAY_CONFIG=$(cat <<EOF
{
    "name": "${GATEWAY_NAME}",
    "description": "MCP Gateway for ${SERVICE_NAME}",
    "protocolType": "MCP",
    "connectionConfiguration": {
        "url": "${MCP_ENDPOINT}"
    },
    "roleArn": "${GATEWAY_ROLE_ARN}"
}
EOF
)

echo "${GATEWAY_CONFIG}" > /tmp/gateway-config.json

# Create the gateway using AWS CLI
# Note: Command may need adjustment based on final AgentCore API
aws bedrock-agent create-agent-action-group \
    --agent-id "placeholder" \
    --agent-version "DRAFT" \
    --action-group-name "${GATEWAY_NAME}" \
    --description "MCP Gateway for ${SERVICE_NAME}" \
    --action-group-executor '{"customControl": "RETURN_CONTROL"}' \
    --region "${AWS_REGION}" 2>/dev/null || {
    log_warn "Direct gateway creation not available via CLI"
    log_info "Please use the AWS Console or SDK to complete gateway registration"
}

rm /tmp/gateway-config.json

# =============================================================================
# Summary
# =============================================================================
echo ""
log_info "=========================================="
log_info "Gateway Registration Information"
log_info "=========================================="
echo ""
echo "Gateway Name: ${GATEWAY_NAME}"
echo "MCP Endpoint: ${MCP_ENDPOINT}"
echo "IAM Role ARN: ${GATEWAY_ROLE_ARN}"
echo ""
echo "Manual Gateway Registration (if CLI not available):"
echo ""
echo "1. Go to AWS Console > Amazon Bedrock > AgentCore"
echo "2. Create new MCP Gateway with:"
echo "   - Name: ${GATEWAY_NAME}"
echo "   - Protocol: MCP"
echo "   - Endpoint URL: ${MCP_ENDPOINT}"
echo "   - IAM Role: ${GATEWAY_ROLE_ARN}"
echo ""
echo "3. Configure tools discovery or manually define tools"
echo ""
echo "Using AWS SDK (Python):"
echo ""
cat <<PYTHON
import boto3

bedrock = boto3.client('bedrock-agent', region_name='${AWS_REGION}')

# Create gateway (API may vary based on service availability)
response = bedrock.create_mcp_gateway(
    name='${GATEWAY_NAME}',
    endpoint='${MCP_ENDPOINT}',
    roleArn='${GATEWAY_ROLE_ARN}'
)

print(f"Gateway ID: {response['gatewayId']}")
PYTHON
echo ""
