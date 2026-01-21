#!/bin/bash
#
# Deploy General Contractor AgentCore Runtime to AWS
#
# This script deploys the agent runtime container that connects to
# MCP servers via AgentCore Gateway (HTTP mode).
#
# Prerequisites:
# - AWS CLI v2 configured with appropriate permissions
# - Docker installed and running
# - MCP servers already deployed (run materials-supplier and permitting-service deploy.sh first)
#
# Usage:
#   ./deploy.sh [OPTIONS]
#
# Options:
#   --skip-build           Skip Docker build and push
#   --skip-infrastructure  Skip infrastructure creation
#   --help                 Show this help message
#
# Required environment variables:
#   MATERIALS_MCP_URL      URL of the Materials Supplier MCP server
#   PERMITTING_MCP_URL     URL of the Permitting Service MCP server
#
# Optional environment variables:
#   AWS_REGION             AWS region (default: us-east-1)
#   AWS_PROFILE            AWS CLI profile to use
#   VPC_ID                 VPC ID to deploy into (default: default VPC)
#   SUBNET_IDS             Comma-separated subnet IDs
#

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SERVICE_NAME="agentcore-runtime"
AWS_REGION="${AWS_REGION:-us-east-1}"

# MCP Server URLs (required)
MATERIALS_MCP_URL="${MATERIALS_MCP_URL:-}"
PERMITTING_MCP_URL="${PERMITTING_MCP_URL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
SKIP_BUILD=false
SKIP_INFRASTRUCTURE=false

for arg in "$@"; do
    case $arg in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-infrastructure)
            SKIP_INFRASTRUCTURE=true
            shift
            ;;
        --help)
            head -40 "$0" | tail -35
            exit 0
            ;;
        *)
            ;;
    esac
done

# =============================================================================
# Helper Functions
# =============================================================================

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

# =============================================================================
# Validation
# =============================================================================

log_step "Validating Configuration"

# Check required MCP URLs
if [ -z "$MATERIALS_MCP_URL" ]; then
    log_error "MATERIALS_MCP_URL is required"
    log_error "Deploy the Materials Supplier MCP server first and set the URL"
    log_error "Example: MATERIALS_MCP_URL=http://materials-mcp-alb-xxx.us-east-1.elb.amazonaws.com/mcp ./deploy.sh"
    exit 1
fi

if [ -z "$PERMITTING_MCP_URL" ]; then
    log_error "PERMITTING_MCP_URL is required"
    log_error "Deploy the Permitting Service MCP server first and set the URL"
    log_error "Example: PERMITTING_MCP_URL=http://permitting-mcp-alb-xxx.us-east-1.elb.amazonaws.com/mcp ./deploy.sh"
    exit 1
fi

log_info "Materials MCP URL: ${MATERIALS_MCP_URL}"
log_info "Permitting MCP URL: ${PERMITTING_MCP_URL}"

# Verify MCP servers are healthy
log_info "Checking MCP server health..."

MATERIALS_HEALTH_URL="${MATERIALS_MCP_URL%/mcp}/health"
PERMITTING_HEALTH_URL="${PERMITTING_MCP_URL%/mcp}/health"

if ! curl -sf "$MATERIALS_HEALTH_URL" > /dev/null 2>&1; then
    log_error "Materials MCP server is not healthy at ${MATERIALS_HEALTH_URL}"
    exit 1
fi
log_info "✓ Materials MCP server is healthy"

if ! curl -sf "$PERMITTING_HEALTH_URL" > /dev/null 2>&1; then
    log_error "Permitting MCP server is not healthy at ${PERMITTING_HEALTH_URL}"
    exit 1
fi
log_info "✓ Permitting MCP server is healthy"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
log_info "AWS Account: ${AWS_ACCOUNT_ID}"
log_info "AWS Region: ${AWS_REGION}"

# =============================================================================
# ECR Repository
# =============================================================================

if [ "$SKIP_INFRASTRUCTURE" = false ]; then
    log_step "Creating ECR Repository"

    ECR_REPO="${SERVICE_NAME}"
    aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${AWS_REGION}" 2>/dev/null || \
        aws ecr create-repository --repository-name "${ECR_REPO}" --region "${AWS_REGION}"

    log_info "ECR Repository: ${ECR_REPO}"
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${SERVICE_NAME}"

# =============================================================================
# Docker Build and Push
# =============================================================================

if [ "$SKIP_BUILD" = false ]; then
    log_step "Building and Pushing Docker Image"

    # Navigate to project root (two levels up from deployment/agentcore-runtime)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

    log_info "Building from project root: ${PROJECT_ROOT}"

    # Login to ECR
    aws ecr get-login-password --region "${AWS_REGION}" | \
        docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    # Build image (use buildx for cross-platform support)
    docker buildx build --platform linux/amd64 \
        -f "${SCRIPT_DIR}/Dockerfile" \
        -t "${SERVICE_NAME}:latest" \
        "${PROJECT_ROOT}"

    # Tag and push
    docker tag "${SERVICE_NAME}:latest" "${ECR_URI}:latest"
    docker push "${ECR_URI}:latest"

    log_info "Image pushed: ${ECR_URI}:latest"
fi

# =============================================================================
# IAM Roles
# =============================================================================

if [ "$SKIP_INFRASTRUCTURE" = false ]; then
    log_step "Creating IAM Roles"

    EXECUTION_ROLE="${SERVICE_NAME}-execution-role"
    TASK_ROLE="${SERVICE_NAME}-task-role"

    # Execution role (for ECS to pull images and write logs)
    aws iam create-role \
        --role-name "${EXECUTION_ROLE}" \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' 2>/dev/null || log_warn "Execution role already exists"

    aws iam attach-role-policy \
        --role-name "${EXECUTION_ROLE}" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" 2>/dev/null || true

    # Task role (for the container to access Bedrock)
    aws iam create-role \
        --role-name "${TASK_ROLE}" \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' 2>/dev/null || log_warn "Task role already exists"

    # Bedrock access policy
    aws iam put-role-policy \
        --role-name "${TASK_ROLE}" \
        --policy-name "BedrockAccess" \
        --policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            }]
        }' 2>/dev/null || true

    EXECUTION_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${EXECUTION_ROLE}"
    TASK_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${TASK_ROLE}"

    log_info "Execution Role: ${EXECUTION_ROLE_ARN}"
    log_info "Task Role: ${TASK_ROLE_ARN}"
fi

# =============================================================================
# CloudWatch Log Group
# =============================================================================

if [ "$SKIP_INFRASTRUCTURE" = false ]; then
    log_step "Creating CloudWatch Log Group"

    LOG_GROUP="/ecs/${SERVICE_NAME}"
    aws logs create-log-group --log-group-name "${LOG_GROUP}" --region "${AWS_REGION}" 2>/dev/null || \
        log_warn "Log group already exists"

    log_info "Log Group: ${LOG_GROUP}"
fi

# =============================================================================
# VPC and Networking
# =============================================================================

if [ "$SKIP_INFRASTRUCTURE" = false ]; then
    log_step "Configuring Networking"

    # Get VPC
    if [ -z "${VPC_ID:-}" ]; then
        VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" \
            --query "Vpcs[0].VpcId" --output text --region "${AWS_REGION}")
    fi
    log_info "VPC: ${VPC_ID}"

    # Get subnets
    if [ -z "${SUBNET_IDS:-}" ]; then
        SUBNET_IDS=$(aws ec2 describe-subnets \
            --filters "Name=vpc-id,Values=${VPC_ID}" \
            --query 'Subnets[?AvailableIpAddressCount>=`8`].[SubnetId,AvailabilityZone]' \
            --output text --region "${AWS_REGION}" | \
            awk '!seen[$2]++ {print $1}' | head -2 | tr '\n' ',' | sed 's/,$//')
    fi
    log_info "Subnets: ${SUBNET_IDS}"

    # Get your IP for security group
    MY_IP=$(curl -s https://checkip.amazonaws.com)
    log_info "Your IP: ${MY_IP}"

    # Create security group
    SG_NAME="${SERVICE_NAME}-sg"
    SG_ID=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
        --query "SecurityGroups[0].GroupId" --output text --region "${AWS_REGION}" 2>/dev/null || echo "None")

    if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
        SG_ID=$(aws ec2 create-security-group \
            --group-name "${SG_NAME}" \
            --description "Security group for ${SERVICE_NAME}" \
            --vpc-id "${VPC_ID}" \
            --query "GroupId" --output text --region "${AWS_REGION}")

        # Allow HTTP from your IP
        aws ec2 authorize-security-group-ingress \
            --group-id "${SG_ID}" \
            --protocol tcp --port 80 \
            --cidr "${MY_IP}/32" --region "${AWS_REGION}" || true

        aws ec2 authorize-security-group-ingress \
            --group-id "${SG_ID}" \
            --protocol tcp --port 8000 \
            --cidr "${MY_IP}/32" --region "${AWS_REGION}" || true
    fi
    log_info "Security Group: ${SG_ID}"
fi

# =============================================================================
# ECS Cluster and Service
# =============================================================================

if [ "$SKIP_INFRASTRUCTURE" = false ]; then
    log_step "Creating ECS Cluster and Service"

    CLUSTER_NAME="${SERVICE_NAME}-cluster"

    # Create cluster
    aws ecs create-cluster --cluster-name "${CLUSTER_NAME}" --region "${AWS_REGION}" 2>/dev/null || \
        log_warn "Cluster already exists"

    # Get role ARNs
    EXECUTION_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${SERVICE_NAME}-execution-role"
    TASK_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${SERVICE_NAME}-task-role"

    # Register task definition
    TASK_DEF=$(cat task-definition.json | \
        sed "s|EXECUTION_ROLE_ARN_PLACEHOLDER|${EXECUTION_ROLE_ARN}|g" | \
        sed "s|TASK_ROLE_ARN_PLACEHOLDER|${TASK_ROLE_ARN}|g" | \
        sed "s|IMAGE_URI_PLACEHOLDER|${ECR_URI}:latest|g" | \
        sed "s|MATERIALS_MCP_URL_PLACEHOLDER|${MATERIALS_MCP_URL}|g" | \
        sed "s|PERMITTING_MCP_URL_PLACEHOLDER|${PERMITTING_MCP_URL}|g" | \
        sed "s|AWS_REGION_PLACEHOLDER|${AWS_REGION}|g")

    echo "${TASK_DEF}" > /tmp/task-def-resolved.json

    aws ecs register-task-definition \
        --cli-input-json "file:///tmp/task-def-resolved.json" \
        --region "${AWS_REGION}"

    rm /tmp/task-def-resolved.json

    # Create or update service
    SERVICE_EXISTS=$(aws ecs describe-services \
        --cluster "${CLUSTER_NAME}" \
        --services "${SERVICE_NAME}-service" \
        --query "services[?status=='ACTIVE'].serviceName" \
        --output text --region "${AWS_REGION}" 2>/dev/null || echo "")

    SUBNET_LIST=$(echo "${SUBNET_IDS}" | tr ',' ' ')

    if [ -z "$SERVICE_EXISTS" ]; then
        aws ecs create-service \
            --cluster "${CLUSTER_NAME}" \
            --service-name "${SERVICE_NAME}-service" \
            --task-definition "${SERVICE_NAME}-task" \
            --desired-count 1 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_LIST}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
            --region "${AWS_REGION}"
        log_info "Service created: ${SERVICE_NAME}-service"
    else
        aws ecs update-service \
            --cluster "${CLUSTER_NAME}" \
            --service "${SERVICE_NAME}-service" \
            --task-definition "${SERVICE_NAME}-task" \
            --force-new-deployment \
            --region "${AWS_REGION}"
        log_info "Service updated: ${SERVICE_NAME}-service"
    fi
fi

# =============================================================================
# Summary
# =============================================================================

log_step "Deployment Complete"

echo ""
echo "AgentCore Runtime deployed successfully!"
echo ""
echo "Configuration:"
echo "  Cluster: ${SERVICE_NAME}-cluster"
echo "  Service: ${SERVICE_NAME}-service"
echo "  Region:  ${AWS_REGION}"
echo ""
echo "MCP Servers:"
echo "  Materials:  ${MATERIALS_MCP_URL}"
echo "  Permitting: ${PERMITTING_MCP_URL}"
echo ""
echo "To view logs:"
echo "  aws logs tail /ecs/${SERVICE_NAME} --follow"
echo ""
echo "To check service status:"
echo "  aws ecs describe-services --cluster ${SERVICE_NAME}-cluster --services ${SERVICE_NAME}-service"
echo ""
