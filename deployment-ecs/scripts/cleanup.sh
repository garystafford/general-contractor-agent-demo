#!/bin/bash
#
# Cleanup AWS resources created by the MCP server deployment
#
# Usage:
#   ./cleanup.sh <service-name>
#
# Examples:
#   ./cleanup.sh materials-supplier-mcp
#   ./cleanup.sh permitting-service-mcp
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
if [ $# -lt 1 ]; then
	echo "Usage: ./cleanup.sh <service-name>"
	echo ""
	echo "Examples:"
	echo "  ./cleanup.sh materials-supplier-mcp"
	echo "  ./cleanup.sh permitting-service-mcp"
	exit 1
fi

SERVICE_NAME="$1"

log_warn "This will delete ALL resources for ${SERVICE_NAME}"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
	log_info "Cleanup cancelled"
	exit 0
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

log_info "Cleaning up resources for ${SERVICE_NAME}"
log_info "AWS Region: ${AWS_REGION}"

# =============================================================================
# Step 1: Delete ECS Service
# =============================================================================
log_info "Deleting ECS service..."
aws ecs update-service \
	--cluster "${SERVICE_NAME}-cluster" \
	--service "${SERVICE_NAME}-service" \
	--desired-count 0 \
	--region "${AWS_REGION}" 2>/dev/null || log_warn "Service not found or already stopped"

aws ecs delete-service \
	--cluster "${SERVICE_NAME}-cluster" \
	--service "${SERVICE_NAME}-service" \
	--force \
	--region "${AWS_REGION}" 2>/dev/null || log_warn "Service not found"

# =============================================================================
# Step 2: Delete ECS Cluster
# =============================================================================
log_info "Deleting ECS cluster..."
aws ecs delete-cluster \
	--cluster "${SERVICE_NAME}-cluster" \
	--region "${AWS_REGION}" 2>/dev/null || log_warn "Cluster not found"

# =============================================================================
# Step 3: Delete Load Balancer Resources
# =============================================================================
log_info "Deleting load balancer resources..."

# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers \
	--names "${SERVICE_NAME}-alb" \
	--query "LoadBalancers[0].LoadBalancerArn" \
	--output text \
	--region "${AWS_REGION}" 2>/dev/null || echo "")

if [ -n "$ALB_ARN" ] && [ "$ALB_ARN" != "None" ]; then
	# Delete listeners first
	LISTENER_ARNS=$(aws elbv2 describe-listeners \
		--load-balancer-arn "${ALB_ARN}" \
		--query "Listeners[*].ListenerArn" \
		--output text \
		--region "${AWS_REGION}" 2>/dev/null || echo "")

	for LISTENER_ARN in $LISTENER_ARNS; do
		aws elbv2 delete-listener \
			--listener-arn "${LISTENER_ARN}" \
			--region "${AWS_REGION}" 2>/dev/null || true
	done

	# Delete ALB
	aws elbv2 delete-load-balancer \
		--load-balancer-arn "${ALB_ARN}" \
		--region "${AWS_REGION}" 2>/dev/null || log_warn "ALB not found"
fi

# Delete Target Group
TG_ARN=$(aws elbv2 describe-target-groups \
	--names "${SERVICE_NAME}-tg" \
	--query "TargetGroups[0].TargetGroupArn" \
	--output text \
	--region "${AWS_REGION}" 2>/dev/null || echo "")

if [ -n "$TG_ARN" ] && [ "$TG_ARN" != "None" ]; then
	# Wait for ALB to be deleted
	log_info "Waiting for ALB to be deleted..."
	sleep 30

	aws elbv2 delete-target-group \
		--target-group-arn "${TG_ARN}" \
		--region "${AWS_REGION}" 2>/dev/null || log_warn "Target group not found or still in use"
fi

# =============================================================================
# Step 4: Delete Security Group
# =============================================================================
log_info "Deleting security group..."
# Wait a bit for ENIs to be released
sleep 10

SG_ID=$(aws ec2 describe-security-groups \
	--filters "Name=group-name,Values=${SERVICE_NAME}-sg" \
	--query "SecurityGroups[0].GroupId" \
	--output text \
	--region "${AWS_REGION}" 2>/dev/null || echo "")

if [ -n "$SG_ID" ] && [ "$SG_ID" != "None" ]; then
	aws ec2 delete-security-group \
		--group-id "${SG_ID}" \
		--region "${AWS_REGION}" 2>/dev/null || log_warn "Security group not found or still in use"
fi

# =============================================================================
# Step 5: Delete ECR Repository
# =============================================================================
log_info "Deleting ECR repository..."
aws ecr delete-repository \
	--repository-name "${SERVICE_NAME}" \
	--force \
	--region "${AWS_REGION}" 2>/dev/null || log_warn "ECR repository not found"

# =============================================================================
# Step 6: Delete CloudWatch Log Group
# =============================================================================
log_info "Deleting CloudWatch log group..."
aws logs delete-log-group \
	--log-group-name "/ecs/${SERVICE_NAME}" \
	--region "${AWS_REGION}" 2>/dev/null || log_warn "Log group not found"

# =============================================================================
# Step 7: Delete IAM Roles
# =============================================================================
log_info "Deleting IAM roles..."

# Delete task role policy and role
aws iam delete-role-policy \
	--role-name "${SERVICE_NAME}-task-role" \
	--policy-name "CloudWatchLogsPolicy" 2>/dev/null || true

aws iam delete-role \
	--role-name "${SERVICE_NAME}-task-role" 2>/dev/null || log_warn "Task role not found"

# Detach and delete execution role
aws iam detach-role-policy \
	--role-name "${SERVICE_NAME}-execution-role" \
	--policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" 2>/dev/null || true

aws iam delete-role \
	--role-name "${SERVICE_NAME}-execution-role" 2>/dev/null || log_warn "Execution role not found"

# Delete gateway role
aws iam delete-role-policy \
	--role-name "${SERVICE_NAME}-gateway-role" \
	--policy-name "MCPEndpointAccess" 2>/dev/null || true

aws iam delete-role \
	--role-name "${SERVICE_NAME}-gateway-role" 2>/dev/null || log_warn "Gateway role not found"

# =============================================================================
# Step 8: Deregister Task Definitions
# =============================================================================
log_info "Deregistering task definitions..."

TASK_DEFS=$(aws ecs list-task-definitions \
	--family-prefix "${SERVICE_NAME}-task" \
	--query "taskDefinitionArns" \
	--output text \
	--region "${AWS_REGION}" 2>/dev/null || echo "")

for TASK_DEF in $TASK_DEFS; do
	aws ecs deregister-task-definition \
		--task-definition "${TASK_DEF}" \
		--region "${AWS_REGION}" 2>/dev/null || true
done

# =============================================================================
# Summary
# =============================================================================
echo ""
log_info "=========================================="
log_info "Cleanup Complete!"
log_info "=========================================="
echo ""
echo "Deleted resources for: ${SERVICE_NAME}"
echo ""
echo "Note: Some resources may take a few minutes to fully delete."
echo "If you encounter 'still in use' errors, wait and re-run the script."
echo ""
