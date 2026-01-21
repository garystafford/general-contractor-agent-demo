# AWS Deployment for Amazon Bedrock AgentCore

This directory contains deployment code for the General Contractor system on AWS:

1. **MCP Servers** - Materials Supplier and Permitting Service (ECS + AgentCore Gateway)
2. **AgentCore Runtime** - Agent orchestration system connecting to MCP servers via HTTP

## Architecture

```text
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│                 │     │                  │     │                     │
│  Bedrock Agent  │────▶│  AgentCore       │────▶│  Materials Supplier │
│                 │     │  Gateway         │     │  MCP Server         │
│                 │     │                  │     │  (ECS Fargate)      │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
        │                                                   │
        │                                                   ▼
        │                                        ┌─────────────────────┐
        │                                        │  ALB + ECR          │
        │                                        │  CloudWatch         │
        │                                        └─────────────────────┘
        │
        │               ┌──────────────────┐     ┌─────────────────────┐
        │               │                  │     │                     │
        └──────────────▶│  AgentCore       │────▶│  Permitting Service │
                        │  Gateway         │     │  MCP Server         │
                        │                  │     │  (ECS Fargate)      │
                        └──────────────────┘     └─────────────────────┘
                                                            │
                                                            ▼
                                                 ┌─────────────────────┐
                                                 │  ALB + ECR          │
                                                 │  CloudWatch         │
                                                 └─────────────────────┘
```

## Directory Structure

```text
deployment/
├── README.md                    # This file
├── agentcore-runtime/           # Agent Runtime (connects to MCP via HTTP)
│   ├── Dockerfile              # Container build configuration
│   ├── task-definition.json    # ECS task definition
│   └── deploy.sh               # Deployment script
├── materials-supplier/          # Materials Supplier MCP Server
│   ├── Dockerfile              # Container build configuration
│   ├── requirements.txt        # Python dependencies
│   ├── task-definition.json    # ECS task definition
│   ├── deploy.sh               # Deployment script
│   └── app/
│       ├── __init__.py
│       ├── main.py             # Entry point
│       └── server.py           # HTTP MCP server
├── permitting-service/          # Permitting Service MCP Server
│   ├── Dockerfile              # Container build configuration
│   ├── requirements.txt        # Python dependencies
│   ├── task-definition.json    # ECS task definition
│   ├── deploy.sh               # Deployment script
│   └── app/
│       ├── __init__.py
│       ├── main.py             # Entry point
│       └── server.py           # HTTP MCP server
└── scripts/
    ├── create-gateway.sh       # Register with AgentCore Gateway
    ├── cleanup.sh              # Remove AWS resources
    └── update-ip.sh            # Update security groups with current IP
```

## Prerequisites

- AWS CLI v2 configured with appropriate permissions
- Docker installed and running
- AWS account with permissions for:
  - ECR (Elastic Container Registry)
  - ECS (Elastic Container Service)
  - ELB (Elastic Load Balancing)
  - IAM (Identity and Access Management)
  - CloudWatch Logs
  - Bedrock AgentCore

## Quick Start

### Make All Scripts Executable (One-Time Setup)

```bash
# From project root, make all deployment scripts executable
chmod +x deployment/**/*.sh
```

### Deploy Materials Supplier MCP Server

```bash
cd deployment/materials-supplier
./deploy.sh
```

### Deploy Permitting Service MCP Server

```bash
cd deployment/permitting-service
./deploy.sh
```

### Register with AgentCore Gateway

After deployment, register each server with AgentCore:

```bash
cd deployment/scripts

# Get the ALB DNS from deployment output, then:
./create-gateway.sh materials-supplier-mcp <alb-dns>
./create-gateway.sh permitting-service-mcp <alb-dns>
```

### Deploy AgentCore Runtime (Full Stack)

After MCP servers are deployed, deploy the agent runtime:

```bash
cd deployment/agentcore-runtime

# Set MCP server URLs (from MCP deployment output)
export MATERIALS_MCP_URL="http://materials-supplier-mcp-alb-xxx.us-east-1.elb.amazonaws.com/mcp"
export PERMITTING_MCP_URL="http://permitting-service-mcp-alb-xxx.us-east-1.elb.amazonaws.com/mcp"

# Deploy
./deploy.sh
```

This deploys the General Contractor orchestration system with all 8 trade agents, configured to connect to MCP servers via HTTP instead of local subprocesses.

## Deployment Options

### Environment Variables

| Variable      | Default       | Description                                      |
| ------------- | ------------- | ------------------------------------------------ |
| `AWS_REGION`  | `us-east-1`   | AWS region for deployment                        |
| `AWS_PROFILE` | -             | AWS CLI profile to use                           |
| `VPC_ID`      | default VPC   | VPC ID to deploy into                            |
| `SUBNET_IDS`  | auto-selected | Comma-separated subnet IDs (must be in 2+ AZs)   |

### VPC Requirements

- At least 2 subnets in different Availability Zones
- Each subnet needs **at least 8 free IP addresses** (for ALB)
- Subnets must be **public** (have route to Internet Gateway)
- VPC needs an Internet Gateway attached

### Command Line Options

```bash
./deploy.sh [OPTIONS]

Options:
  --skip-build           Skip Docker build and push
  --skip-infrastructure  Skip infrastructure creation (ECR, ECS cluster, etc.)
  --help                 Show help message
```

### Examples

```bash
# Full deployment (uses default VPC, auto-selects subnets with >= 8 IPs)
./deploy.sh

# Deploy with specific VPC
VPC_ID=vpc-12345678 ./deploy.sh

# Deploy with specific subnets (must be in different AZs)
SUBNET_IDS=subnet-aaa,subnet-bbb ./deploy.sh

# Deploy with specific VPC and subnets
VPC_ID=vpc-12345678 SUBNET_IDS=subnet-aaa,subnet-bbb ./deploy.sh

# Update code only (skip infrastructure)
./deploy.sh --skip-infrastructure

# Deploy to different region
AWS_REGION=us-west-2 ./deploy.sh

# List subnets in a VPC to find ones with enough IPs
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxx" \
  --query 'Subnets[*].[SubnetId,AvailabilityZone,AvailableIpAddressCount]' --output table
```

## AWS Resources Created

Each MCP server deployment creates:

| Resource        | Name Pattern            | Description              |
| --------------- | ----------------------- | ------------------------ |
| ECR Repository  | `<service>-mcp`         | Container image registry |
| ECS Cluster     | `<service>-mcp-cluster` | Fargate cluster          |
| ECS Service     | `<service>-mcp-service` | Running service          |
| Task Definition | `<service>-mcp-task`    | Container configuration  |
| ALB             | `<service>-mcp-alb`     | Load balancer            |
| Target Group    | `<service>-mcp-tg`      | ALB target               |
| Security Group  | `<service>-mcp-sg`      | Network security         |
| IAM Roles       | `<service>-mcp-*-role`  | Execution and task roles |
| Log Group       | `/ecs/<service>-mcp`    | CloudWatch logs          |

## Local Testing

### Test Materials Supplier

```bash
cd deployment/materials-supplier

# Build container (for ARM Mac, add --platform linux/amd64 for ECS compatibility)
docker build -t materials-supplier-mcp .

# Run container
docker run -p 8080:8080 materials-supplier-mcp

# Test health endpoint
curl http://localhost:8080/health

# Test MCP endpoint (requires SSE-compatible headers)
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}, "id": 1}'
```

### Test Permitting Service

```bash
cd deployment/permitting-service

# Build container (for ARM Mac, add --platform linux/amd64 for ECS compatibility)
docker build -t permitting-service-mcp .

# Run container
docker run -p 8081:8080 permitting-service-mcp

# Test health endpoint
curl http://localhost:8081/health

# Test MCP endpoint
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}, "id": 1}'
```

## Monitoring

### View Logs

```bash
# Materials Supplier
aws logs tail /ecs/materials-supplier-mcp --follow

# Permitting Service
aws logs tail /ecs/permitting-service-mcp --follow
```

### Check Service Status

```bash
# Materials Supplier
aws ecs describe-services \
  --cluster materials-supplier-mcp-cluster \
  --services materials-supplier-mcp-service

# Permitting Service
aws ecs describe-services \
  --cluster permitting-service-mcp-cluster \
  --services permitting-service-mcp-service
```

### Check Target Health

```bash
# Get target group ARN from deployment output, then:
aws elbv2 describe-target-health --target-group-arn <tg-arn>
```

## Update Security Group IP

If your IP address changes, update the ALB security groups to allow access from your new IP:

```bash
cd deployment/scripts

# Preview changes (dry run)
./update-ip.sh --dry-run

# Apply changes
./update-ip.sh
```

This updates the security groups for all deployed services (materials-supplier-mcp, permitting-service-mcp, agentcore-runtime) to allow access from your current public IP.

## Cleanup

Remove all AWS resources for a service:

```bash
cd deployment/scripts

# Remove Materials Supplier
./cleanup.sh materials-supplier-mcp

# Remove Permitting Service
./cleanup.sh permitting-service-mcp

# Remove AgentCore Runtime
./cleanup.sh agentcore-runtime
```

## MCP Server Tools

### Materials Supplier

| Tool                 | Description                                       |
| -------------------- | ------------------------------------------------- |
| `check_availability` | Check stock levels and pricing for materials      |
| `order_materials`    | Place orders with quantity tracking               |
| `get_catalog`        | Retrieve materials catalog (filtered by category) |
| `get_order`          | Retrieve order details by order ID                |

### Permitting Service

| Tool                   | Description                 |
| ---------------------- | --------------------------- |
| `apply_for_permit`     | Submit permit applications  |
| `check_permit_status`  | Check permit status         |
| `schedule_inspection`  | Schedule inspections        |
| `get_required_permits` | Determine required permits  |
| `get_inspection`       | Retrieve inspection details |

## Estimated Costs

Per MCP server (approximate monthly costs):

| Resource                       | Estimated Cost    |
| ------------------------------ | ----------------- |
| ECS Fargate (0.25 vCPU, 0.5GB) | ~$9/month         |
| Application Load Balancer      | ~$16/month        |
| ECR Storage                    | < $1/month        |
| CloudWatch Logs                | Variable          |
| **Total per server**           | **~$25-30/month** |

## Troubleshooting

### Service Not Starting

1. Check CloudWatch logs for errors:

   ```bash
   aws logs tail /ecs/<service-name> --follow
   ```

2. Verify task definition:

   ```bash
   aws ecs describe-task-definition --task-definition <service-name>-task
   ```

3. Check security group allows traffic on port 8080

### Health Check Failing

1. Test health endpoint directly:

   ```bash
   curl http://<alb-dns>/health
   ```

2. Check target group health:
   ```bash
   aws elbv2 describe-target-health --target-group-arn <tg-arn>
   ```

### Gateway Registration Issues

1. Verify MCP server is healthy before registering
2. Check IAM role trust policy includes `bedrock.amazonaws.com`
3. Ensure endpoint URL is accessible from AWS

### ECR Pull Errors (Private Subnets)

If using private subnets with VPC endpoints for ECR, ensure the VPC endpoint security group allows inbound HTTPS (443) traffic from the ECS task security group:

```bash
# Add ECS security group to VPC endpoint security group
aws ec2 authorize-security-group-ingress \
  --group-id <vpc-endpoint-sg-id> \
  --protocol tcp \
  --port 443 \
  --source-group <ecs-task-sg-id>
```

### Platform Mismatch (ARM Mac)

If building on ARM-based Mac (M1/M2/M3) for ECS Fargate (linux/amd64):

```bash
# Build with explicit platform
docker buildx build --platform linux/amd64 -t <image-name> .
```

## Security Considerations

- **Security groups restrict external access to deployer's IP only** (auto-detected with `/32` CIDR)
  - Ports 80/443: Restricted to your IP address
  - Port 8080: Internal VPC CIDR only (ALB to ECS traffic)
- For production, enable HTTPS with ACM certificates
- If using private subnets, add VPC endpoints for ECR (`com.amazonaws.<region>.ecr.api` and `com.amazonaws.<region>.ecr.dkr`) and ensure endpoint security groups allow traffic from ECS task security groups
- Review IAM permissions and apply least-privilege principle
- Enable AWS WAF for additional protection

## Contributing

When modifying the MCP servers:

1. Test locally with Docker first
2. Update the server code in `app/server.py`
3. Run deployment with `--skip-infrastructure` to update only the code
4. Verify health check passes before updating gateway registration
