#!/bin/bash
#
# Deploy Permitting Service MCP Server to AWS
#
# Prerequisites:
# - AWS CLI v2 configured with appropriate permissions
# - Docker installed and running
# - jq installed for JSON parsing
#
# Usage:
#   ./deploy.sh [--skip-build] [--skip-infrastructure]
#
# Environment variables (optional):
#   AWS_REGION - AWS region (default: us-east-1)
#   AWS_PROFILE - AWS CLI profile to use
#

set -euo pipefail

# Configuration
SERVICE_NAME="permitting-service-mcp"
AWS_REGION="${AWS_REGION:-us-east-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
SKIP_BUILD=false
SKIP_INFRASTRUCTURE=false
for arg in "$@"; do
	case $arg in
	--skip-build) SKIP_BUILD=true ;;
	--skip-infrastructure) SKIP_INFRASTRUCTURE=true ;;
	--help)
		echo "Usage: ./deploy.sh [--skip-build] [--skip-infrastructure]"
		exit 0
		;;
	esac
done

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

log_info "Deploying ${SERVICE_NAME}"
log_info "AWS Account: ${AWS_ACCOUNT_ID}"
log_info "AWS Region: ${AWS_REGION}"

# =============================================================================
# Step 1: Create IAM Roles
# =============================================================================
if [ "$SKIP_INFRASTRUCTURE" = false ]; then
	log_info "Creating IAM roles..."

	# ECS Task Execution Role
	aws iam create-role \
		--role-name "${SERVICE_NAME}-execution-role" \
		--assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' 2>/dev/null || log_warn "Execution role already exists"

	aws iam attach-role-policy \
		--role-name "${SERVICE_NAME}-execution-role" \
		--policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" 2>/dev/null || true

	# ECS Task Role
	aws iam create-role \
		--role-name "${SERVICE_NAME}-task-role" \
		--assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' 2>/dev/null || log_warn "Task role already exists"

	# Task role policy for CloudWatch Logs
	aws iam put-role-policy \
		--role-name "${SERVICE_NAME}-task-role" \
		--policy-name "CloudWatchLogsPolicy" \
		--policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "*"
            }]
        }' 2>/dev/null || true
fi

# =============================================================================
# Step 2: Create ECR Repository
# =============================================================================
if [ "$SKIP_INFRASTRUCTURE" = false ]; then
	log_info "Creating ECR repository..."
	aws ecr create-repository \
		--repository-name "${SERVICE_NAME}" \
		--image-scanning-configuration scanOnPush=true \
		--region "${AWS_REGION}" 2>/dev/null || log_warn "ECR repository already exists"
fi

# =============================================================================
# Step 3: Build and Push Docker Image
# =============================================================================
if [ "$SKIP_BUILD" = false ]; then
	log_info "Building Docker image for linux/amd64..."
	cd "${SCRIPT_DIR}"
	docker buildx build --platform linux/amd64 -t "${SERVICE_NAME}:latest" .

	log_info "Authenticating with ECR..."
	aws ecr get-login-password --region "${AWS_REGION}" |
		docker login --username AWS --password-stdin "${ECR_URI}"

	log_info "Tagging and pushing image..."
	docker tag "${SERVICE_NAME}:latest" "${ECR_URI}/${SERVICE_NAME}:latest"
	docker push "${ECR_URI}/${SERVICE_NAME}:latest"
fi

# =============================================================================
# Step 4: Create CloudWatch Log Group
# =============================================================================
if [ "$SKIP_INFRASTRUCTURE" = false ]; then
	log_info "Creating CloudWatch log group..."
	aws logs create-log-group \
		--log-group-name "/ecs/${SERVICE_NAME}" \
		--region "${AWS_REGION}" 2>/dev/null || log_warn "Log group already exists"
fi

# =============================================================================
# Step 5: Create ECS Cluster
# =============================================================================
if [ "$SKIP_INFRASTRUCTURE" = false ]; then
	log_info "Creating ECS cluster..."
	aws ecs create-cluster \
		--cluster-name "${SERVICE_NAME}-cluster" \
		--capacity-providers FARGATE FARGATE_SPOT \
		--default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
		--region "${AWS_REGION}" 2>/dev/null || log_warn "ECS cluster already exists"
fi

# =============================================================================
# Step 6: Register Task Definition
# =============================================================================
log_info "Registering ECS task definition..."

# Substitute environment variables in task definition
TASK_DEF=$(cat "${SCRIPT_DIR}/task-definition.json" |
	sed "s/\${AWS_ACCOUNT_ID}/${AWS_ACCOUNT_ID}/g" |
	sed "s/\${AWS_REGION}/${AWS_REGION}/g")

echo "${TASK_DEF}" >/tmp/task-definition-resolved.json

aws ecs register-task-definition \
	--cli-input-json file:///tmp/task-definition-resolved.json \
	--region "${AWS_REGION}"

rm /tmp/task-definition-resolved.json

# =============================================================================
# Step 7: Get VPC and Subnets
# =============================================================================
log_info "Getting VPC configuration..."

# Use VPC_ID env var if set, otherwise use default VPC
if [ -n "${VPC_ID:-}" ]; then
	TARGET_VPC_ID="${VPC_ID}"
	log_info "Using specified VPC: ${TARGET_VPC_ID}"
else
	TARGET_VPC_ID=$(aws ec2 describe-vpcs \
		--filters "Name=isDefault,Values=true" \
		--query "Vpcs[0].VpcId" \
		--output text \
		--region "${AWS_REGION}")

	if [ "$TARGET_VPC_ID" = "None" ] || [ -z "$TARGET_VPC_ID" ]; then
		log_error "No default VPC found. Set VPC_ID environment variable to specify a VPC."
		log_error "Example: VPC_ID=vpc-12345678 ./deploy.sh"
		exit 1
	fi
	log_info "Using default VPC: ${TARGET_VPC_ID}"
fi

# Use SUBNET_IDS env var if set, otherwise auto-select
if [ -n "${SUBNET_IDS:-}" ]; then
	log_info "Using specified subnets: ${SUBNET_IDS}"
else
	# Get subnets with at least 8 available IPs (ALB requirement), from different AZs
	log_info "Auto-selecting subnets with >= 8 available IPs in different AZs..."

	SUBNET_IDS=$(aws ec2 describe-subnets \
		--filters "Name=vpc-id,Values=${TARGET_VPC_ID}" \
		--query "Subnets[?AvailableIpAddressCount>=\`8\`].[SubnetId,AvailabilityZone,AvailableIpAddressCount]" \
		--output text \
		--region "${AWS_REGION}" | sort -k2 -u | head -2 | awk '{print $1}' | tr '\n' ',' | sed 's/,$//')

	if [ -z "$SUBNET_IDS" ]; then
		log_error "No subnets found with >= 8 available IPs."
		log_error "List available subnets with:"
		log_error "  aws ec2 describe-subnets --filters Name=vpc-id,Values=${TARGET_VPC_ID} --query 'Subnets[*].[SubnetId,AvailabilityZone,AvailableIpAddressCount]' --output table"
		log_error "Then specify manually: SUBNET_IDS=subnet-xxx,subnet-yyy ./deploy.sh"
		exit 1
	fi
fi

# Verify we have at least 2 subnets in different AZs
SUBNET_COUNT=$(echo "${SUBNET_IDS}" | tr ',' '\n' | wc -l | tr -d ' ')
if [ "$SUBNET_COUNT" -lt 2 ]; then
	log_error "ALB requires subnets in at least 2 different availability zones."
	log_error "Found only ${SUBNET_COUNT} subnet(s)."
	log_error "Specify subnets manually: SUBNET_IDS=subnet-xxx,subnet-yyy ./deploy.sh"
	exit 1
fi

log_info "Using VPC: ${TARGET_VPC_ID}"
log_info "Using Subnets: ${SUBNET_IDS}"

# =============================================================================
# Step 8: Create Security Group
# =============================================================================

# Get current public IP for security group rules
log_info "Getting your public IP address..."
MY_IP=$(curl -s https://checkip.amazonaws.com || curl -s https://ifconfig.me)
if [ -z "$MY_IP" ]; then
	log_error "Failed to determine your public IP address."
	log_error "Please set MY_IP environment variable manually."
	exit 1
fi
MY_CIDR="${MY_IP}/32"
log_info "Your IP: ${MY_CIDR}"

# Get VPC CIDR for internal communication
VPC_CIDR=$(aws ec2 describe-vpcs \
	--vpc-ids "${TARGET_VPC_ID}" \
	--query "Vpcs[0].CidrBlock" \
	--output text \
	--region "${AWS_REGION}")

if [ "$SKIP_INFRASTRUCTURE" = false ]; then
	log_info "Creating security group..."

	SG_ID=$(aws ec2 create-security-group \
		--group-name "${SERVICE_NAME}-sg" \
		--description "Security group for ${SERVICE_NAME}" \
		--vpc-id "${TARGET_VPC_ID}" \
		--query "GroupId" \
		--output text \
		--region "${AWS_REGION}" 2>/dev/null) ||
		SG_ID=$(aws ec2 describe-security-groups \
			--filters "Name=group-name,Values=${SERVICE_NAME}-sg" \
			--query "SecurityGroups[0].GroupId" \
			--output text \
			--region "${AWS_REGION}")

	# Allow inbound HTTP traffic from your IP only
	aws ec2 authorize-security-group-ingress \
		--group-id "${SG_ID}" \
		--protocol tcp \
		--port 80 \
		--cidr "${MY_CIDR}" \
		--region "${AWS_REGION}" 2>/dev/null || true

	# Allow inbound HTTPS traffic from your IP only
	aws ec2 authorize-security-group-ingress \
		--group-id "${SG_ID}" \
		--protocol tcp \
		--port 443 \
		--cidr "${MY_CIDR}" \
		--region "${AWS_REGION}" 2>/dev/null || true

	# Allow internal VPC traffic on port 8080 (ALB to ECS)
	aws ec2 authorize-security-group-ingress \
		--group-id "${SG_ID}" \
		--protocol tcp \
		--port 8080 \
		--cidr "${VPC_CIDR}" \
		--region "${AWS_REGION}" 2>/dev/null || true
else
	SG_ID=$(aws ec2 describe-security-groups \
		--filters "Name=group-name,Values=${SERVICE_NAME}-sg" \
		--query "SecurityGroups[0].GroupId" \
		--output text \
		--region "${AWS_REGION}")
fi

log_info "Using Security Group: ${SG_ID}"

# =============================================================================
# Step 9: Create Application Load Balancer
# =============================================================================
log_info "Setting up Application Load Balancer..."

# Check if ALB already exists
ALB_ARN=$(aws elbv2 describe-load-balancers \
	--names "${SERVICE_NAME}-alb" \
	--query "LoadBalancers[0].LoadBalancerArn" \
	--output text \
	--region "${AWS_REGION}" 2>/dev/null || echo "")

if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" = "None" ]; then
	if [ "$SKIP_INFRASTRUCTURE" = true ]; then
		log_error "ALB does not exist and --skip-infrastructure was specified."
		log_error "Run without --skip-infrastructure first to create the ALB."
		exit 1
	fi

	log_info "Creating Application Load Balancer..."
	ALB_ARN=$(aws elbv2 create-load-balancer \
		--name "${SERVICE_NAME}-alb" \
		--subnets $(echo "${SUBNET_IDS}" | tr ',' ' ') \
		--security-groups "${SG_ID}" \
		--scheme internet-facing \
		--type application \
		--query "LoadBalancers[0].LoadBalancerArn" \
		--output text \
		--region "${AWS_REGION}")

	if [ -z "$ALB_ARN" ] || [ "$ALB_ARN" = "None" ]; then
		log_error "Failed to create Application Load Balancer"
		exit 1
	fi
	log_info "Created ALB: ${ALB_ARN}"
else
	log_info "ALB already exists: ${ALB_ARN}"
fi

# Check if Target Group already exists
TG_ARN=$(aws elbv2 describe-target-groups \
	--names "${SERVICE_NAME}-tg" \
	--query "TargetGroups[0].TargetGroupArn" \
	--output text \
	--region "${AWS_REGION}" 2>/dev/null || echo "")

if [ -z "$TG_ARN" ] || [ "$TG_ARN" = "None" ]; then
	if [ "$SKIP_INFRASTRUCTURE" = true ]; then
		log_error "Target Group does not exist and --skip-infrastructure was specified."
		exit 1
	fi

	log_info "Creating Target Group..."
	TG_ARN=$(aws elbv2 create-target-group \
		--name "${SERVICE_NAME}-tg" \
		--protocol HTTP \
		--port 8080 \
		--vpc-id "${TARGET_VPC_ID}" \
		--target-type ip \
		--health-check-path "/health" \
		--health-check-interval-seconds 30 \
		--health-check-timeout-seconds 10 \
		--healthy-threshold-count 2 \
		--unhealthy-threshold-count 3 \
		--query "TargetGroups[0].TargetGroupArn" \
		--output text \
		--region "${AWS_REGION}")

	if [ -z "$TG_ARN" ] || [ "$TG_ARN" = "None" ]; then
		log_error "Failed to create Target Group"
		exit 1
	fi
	log_info "Created Target Group: ${TG_ARN}"
else
	log_info "Target Group already exists: ${TG_ARN}"
fi

# Create Listener if it doesn't exist
if [ "$SKIP_INFRASTRUCTURE" = false ]; then
	aws elbv2 create-listener \
		--load-balancer-arn "${ALB_ARN}" \
		--protocol HTTP \
		--port 80 \
		--default-actions Type=forward,TargetGroupArn="${TG_ARN}" \
		--region "${AWS_REGION}" 2>/dev/null || log_info "Listener already exists"
fi

log_info "Using ALB: ${ALB_ARN}"
log_info "Using Target Group: ${TG_ARN}"

# =============================================================================
# Step 10: Create or Update ECS Service
# =============================================================================
log_info "Creating/updating ECS service..."

# Check if service exists
SERVICE_EXISTS=$(aws ecs describe-services \
	--cluster "${SERVICE_NAME}-cluster" \
	--services "${SERVICE_NAME}-service" \
	--query "services[?status=='ACTIVE'].serviceName" \
	--output text \
	--region "${AWS_REGION}" 2>/dev/null || echo "")

# Get first two subnet IDs for the service
SUBNET_ARRAY=(${SUBNET_IDS//,/ })
SERVICE_SUBNETS="${SUBNET_ARRAY[0]},${SUBNET_ARRAY[1]}"

if [ -z "$SERVICE_EXISTS" ]; then
	log_info "Creating new ECS service..."
	aws ecs create-service \
		--cluster "${SERVICE_NAME}-cluster" \
		--service-name "${SERVICE_NAME}-service" \
		--task-definition "${SERVICE_NAME}-task" \
		--desired-count 1 \
		--launch-type FARGATE \
		--network-configuration "awsvpcConfiguration={subnets=[${SERVICE_SUBNETS}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
		--load-balancers "targetGroupArn=${TG_ARN},containerName=${SERVICE_NAME},containerPort=8080" \
		--region "${AWS_REGION}"
else
	log_info "Updating existing ECS service..."
	aws ecs update-service \
		--cluster "${SERVICE_NAME}-cluster" \
		--service "${SERVICE_NAME}-service" \
		--task-definition "${SERVICE_NAME}-task" \
		--force-new-deployment \
		--region "${AWS_REGION}"
fi

# =============================================================================
# Step 11: Get ALB DNS Name
# =============================================================================
ALB_DNS=$(aws elbv2 describe-load-balancers \
	--load-balancer-arns "${ALB_ARN}" \
	--query "LoadBalancers[0].DNSName" \
	--output text \
	--region "${AWS_REGION}")

# =============================================================================
# Summary
# =============================================================================
echo ""
log_info "=========================================="
log_info "Deployment Complete!"
log_info "=========================================="
echo ""
echo "Service Name: ${SERVICE_NAME}"
echo "ECS Cluster: ${SERVICE_NAME}-cluster"
echo "ECS Service: ${SERVICE_NAME}-service"
echo ""
echo "Endpoints:"
echo "  Health Check: http://${ALB_DNS}/health"
echo "  MCP Endpoint: http://${ALB_DNS}/mcp"
echo ""
echo "To check service status:"
echo "  aws ecs describe-services --cluster ${SERVICE_NAME}-cluster --services ${SERVICE_NAME}-service"
echo ""
echo "To view logs:"
echo "  aws logs tail /ecs/${SERVICE_NAME} --follow"
echo ""
echo "Next steps:"
echo "  1. Wait for the service to become healthy"
echo "  2. Note the ALB DNS name for connecting the backend runtime"
echo "  3. See: deployment/backend-runtime/deploy.sh for backend deployment"
echo ""
